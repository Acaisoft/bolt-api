from datetime import datetime
from flask import current_app

from services.hasura import hce
from services.logger import setup_custom_logger

from apps.bolt_api.app.appgraph.test_runs import TestrunTerminate
from apps.bolt_api.app.appgraph.argo.enums import ArgoFlow, Status

logger = setup_custom_logger(__file__)


class ArgoFlowParser(object):
    argo_id: None
    execution_id: None
    execution_status: None
    current_statuses: None
    has_load_tests: None

    is_terminated = False

    status_mapper = {
        None: [
            Status.ERROR.value,
            Status.FAILED.value,
            Status.PENDING.value,
            Status.RUNNING.value,
            Status.SUCCEEDED.value
        ],
        Status.ERROR.value: [],
        Status.FAILED.value: [],
        Status.SUCCEEDED.value: [],
        Status.PENDING.value: [
            Status.RUNNING.value,
            Status.FAILED.value,
            Status.ERROR.value,
            Status.SUCCEEDED.value
        ],
        Status.RUNNING.value: [
            Status.ERROR.value,
            Status.FAILED.value,
            Status.SUCCEEDED.value
        ],
        Status.TERMINATED.value: []
    }

    def __init__(self, argo_id):
        self.argo_id = argo_id
        execution_data = self.get_execution_by_argo_id(argo_id)
        self.execution_id = execution_data['execution'][0]['id']
        self.execution_status = execution_data['execution'][0]['status']
        self.has_load_tests = execution_data['execution'][0]['configuration']['has_load_tests']
        self.current_statuses = self.get_current_statuses()

    def get_execution_by_argo_id(self, argo_id):
        query = '''            
            query ($argo_name: String){
                execution(where: {argo_name: {_eq: $argo_name}}){
                    id
                    status
                    configuration {
                        has_load_tests
                    }
                }
            }
        '''
        response = hce(current_app.config, query, variable_values={'argo_name': argo_id})
        logger.info(f'Response for `get_execution_by_argo_id({argo_id})` | {response}')
        return response

    def update_execution_status(self, status):
        query = '''
            mutation ($id: uuid, $status: String) {
                update_execution (where: {id: {_eq: $id}}, _set: {status: $status}) {
                    affected_rows
                }
            }
        '''
        response = hce(current_app.config, query, variable_values={'id': self.execution_id, 'status': status})
        logger.info(f'Assigned new status {status} for execution {self.execution_id} | {response}')
        return response

    def get_current_statuses(self):
        query = '''
            query ($execution_id: uuid) {
                execution_stage_log (where: {execution_id: {_eq: $execution_id}}, order_by: {timestamp: desc}){
                    level
                    msg
                    stage
                    timestamp
                }
            }
        '''
        response = hce(current_app.config, query, variable_values={'execution_id': self.execution_id})
        logger.info(f'List of current statuses for execution {self.execution_id} | {response}')
        return response['execution_stage_log']

    def insert_execution_stage_log(self, stage, level, msg):
        query = '''
            mutation ($data: execution_stage_log_insert_input!) {
                insert_execution_stage_log (objects: [$data]){
                    affected_rows
                }
            }
        '''
        data = {
            'execution_id': self.execution_id, 'timestamp': datetime.now().isoformat(),
            'stage': stage, 'level': level, 'msg': msg
        }
        logger.info(f'Inserting execution log (status) with data {data}')
        response = hce(current_app.config, query, variable_values={'data': data})
        return response

    def get_current_status_for(self, stage):
        try:
            status = [status for status in self.current_statuses if stage == status['stage']][0]['msg']
            logger.info(f'Extracted current status {status} for {stage}')
            return status
        except LookupError:
            logger.info(f'Current status for stage {stage} does not exist')
            return None

    def parse_stage_status_for(self, stage, data):
        current_status = self.get_current_status_for(stage)
        phase = data.get('phase', 'UNKNOWN').upper()
        allowed_statuses = self.status_mapper[current_status]
        level = 'error' if phase in (Status.FAILED.value, Status.ERROR.value) else 'info'
        self.insert_execution_stage_log(stage, level, phase)
        if phase != current_status and phase in allowed_statuses:
            level = 'error' if phase in (Status.FAILED.value, Status.ERROR.value) else 'info'
            if stage == 'monitoring' and level == 'error':
                if self.has_load_tests and not self.is_terminated:
                    logger.info('Monitoring crashed (flow has load_tests). Start terminating flow')
                    ok, _ = TestrunTerminate.terminate_flow(self.argo_id)
                    self.is_terminated = True if ok else False
            self.insert_execution_stage_log(stage, level, phase)

    def parse_common_status(self, flow_status, build_status):  # for execution
        new_build_status = None
        if build_status is not None:
            build_status = build_status.upper()
            if flow_status is not None and flow_status.upper() == Status.RUNNING.value:
                if build_status in (Status.PENDING.value, Status.RUNNING.value):
                    new_build_status = Status.PENDING.value
                    self.update_execution_status(Status.PENDING.value)
        if flow_status is not None and new_build_status is None:
            flow_status = flow_status.upper()
            allowed_statuses = self.status_mapper[self.execution_status]
            if flow_status.upper() in allowed_statuses:
                self.update_execution_status(flow_status)

    def parse_argo_statuses(self, argo_data):
        logger.info(f'Start parsing argo data {argo_data}')
        flow_status = argo_data.get('phase', None)
        build_status = None
        # update stage statuses
        for key, value in argo_data.get('nodes', {}).items():
            template_name = value.get('templateName')
            display_name = value.get('displayName')
            if value['type'] == ArgoFlow.POD.value or value['type'] == ArgoFlow.RETRY.value:
                if template_name == ArgoFlow.BUILD.value:
                    build_status = value.get('phase')
                if template_name == ArgoFlow.PRE_START.value:
                    logger.info(f'Detected pre_start argo pod {value}')
                    self.parse_stage_status_for('pre_start', value)
                elif template_name == ArgoFlow.POST_STOP.value:
                    logger.info(f'Detected post_stop argo pod {value}')
                    self.parse_stage_status_for('post_stop', value)
                elif value['type'] == ArgoFlow.RETRY.value and display_name == ArgoFlow.MONITORING.value:
                    logger.info(f'Detected monitoring argo retry {value}')
                    self.parse_stage_status_for('monitoring', value)
                elif value.get('templateName') == ArgoFlow.LOAD_TESTS_MASTER.value:
                    logger.info(f'Detected master argo pod {value}')
                    self.parse_stage_status_for('load_tests', value)
        self.parse_common_status(flow_status, build_status)
