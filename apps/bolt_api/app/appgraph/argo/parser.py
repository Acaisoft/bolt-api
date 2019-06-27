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
        # sometimes argo during crashing container returning status SUCCEEDED and then FAILED/ERROR
        # we need to allow after status SUCCEEDED assign status FAILED/ERROR
        Status.SUCCEEDED.value: [Status.FAILED.value, Status.ERROR.value],
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
        ]
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

    def parse_status_for(self, stage, data):
        current_status = self.get_current_status_for(stage)
        phase = data.get('phase', 'UNKNOWN').upper()
        allowed_statuses = self.status_mapper[current_status]
        if phase != current_status and phase in allowed_statuses:
            level = 'error' if phase in (Status.FAILED.value, Status.ERROR.value) else 'info'
            # if stage == 'argo_monitoring' and level == 'error':
            #     # update status for execution if monitoring failed
            #     if self.execution_status != Status.TERMINATED.value:
            #         self.update_execution_status(Status.FAILED.value)
            #     # terminate all flow if monitoring failed and flow has load tests
            #     if self.has_load_tests and not self.is_terminated:
            #         logger.info('Monitoring crashed (flow has load_tests). Start terminating flow')
            #         ok, _ = TestrunTerminate.terminate_flow(self.argo_id)
            #         self.is_terminated = True if ok else False
            self.insert_execution_stage_log(stage, level, phase)

    def parse_load_tests_status(self, data):
        logger.info(f'Detected load_tests pods {data}')
        current_status = self.get_current_status_for('argo_load_tests')
        argo_load_tests_statuses = [d['phase'].upper() for d in data]
        allowed_statuses = self.status_mapper[current_status]
        logger.info(f'Argo load tests statuses {argo_load_tests_statuses} | current status {current_status}')
        logger.info(f'Allowed statuses {allowed_statuses}')
        if Status.ERROR.value in argo_load_tests_statuses and Status.ERROR.value in allowed_statuses:
            self.insert_execution_stage_log('argo_load_tests', 'error', Status.ERROR.value)
            # update status for execution if load tests failed
            if self.execution_status != Status.TERMINATED.value:
                self.update_execution_status(Status.FAILED.value)
        elif Status.FAILED.value in argo_load_tests_statuses and Status.FAILED.value in allowed_statuses:
            self.insert_execution_stage_log('argo_load_tests', 'error', Status.FAILED.value)
            # update status for execution if load tests failed
            if self.execution_status != Status.TERMINATED.value:
                self.update_execution_status(Status.FAILED.value)
        elif Status.PENDING.value in argo_load_tests_statuses and Status.PENDING.value in allowed_statuses:
            self.insert_execution_stage_log('argo_load_tests', 'info', Status.PENDING.value)
        elif Status.RUNNING.value in argo_load_tests_statuses and Status.RUNNING.value in allowed_statuses:
            self.insert_execution_stage_log('argo_load_tests', 'info', Status.RUNNING.value)
        elif Status.SUCCEEDED.value in argo_load_tests_statuses and Status.SUCCEEDED.value in allowed_statuses:
            self.insert_execution_stage_log('argo_load_tests', 'info', Status.SUCCEEDED.value)

    def parse_argo_statuses(self, argo_data):
        logger.info(f'Start parsing argo data {argo_data}')
        load_tests_data = []
        for key, value in argo_data.get('nodes', {}).items():
            if value['type'] != ArgoFlow.POD.value:
                continue
            if value['templateName'] == ArgoFlow.PRE_START.value:
                logger.info(f'Detected pre_start argo pod {value}')
                self.parse_status_for('argo_pre_start', value)
            elif value['templateName'] == ArgoFlow.POST_STOP.value:
                logger.info(f'Detected post_stop argo pod {value}')
                self.parse_status_for('argo_post_stop', value)
            elif value['templateName'] == ArgoFlow.MONITORING.value:
                logger.info(f'Detected monitoring argo pod {value}')
                self.parse_status_for('argo_monitoring', value)
            elif value['templateName'] in (ArgoFlow.LOAD_TESTS_MASTER.value, ArgoFlow.LOAD_TESTS_SLAVE.value):
                # if master crashed we will terminate all flow
                is_master = value['templateName'] == ArgoFlow.LOAD_TESTS_MASTER.value
                is_crashed = value['phase'].upper() in (Status.ERROR.value, Status.FAILED.value)
                is_not_terminated = not self.is_terminated  # argo flow
                if is_master and is_crashed and is_not_terminated:
                    ok, _ = TestrunTerminate.terminate_flow(self.argo_id)
                    self.is_terminated = True if ok else False
                load_tests_data.append(value)  # aggregate records for master/slaves
        # analyze and parse together data for slaves and for master
        if load_tests_data:
            self.parse_load_tests_status(load_tests_data)
