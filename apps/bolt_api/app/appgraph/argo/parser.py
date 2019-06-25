from datetime import datetime

from flask import current_app
from services.hasura import hce
from services.logger import setup_custom_logger

from apps.bolt_api.app.appgraph.argo.enums import ArgoFlow, Status

logger = setup_custom_logger(__file__)


class ArgoFlowParser(object):
    execution_id: None
    current_statuses: None

    def __init__(self, argo_id):
        self.execution_id = self.get_execution_by_argo_id(argo_id)
        self.current_statuses = self.get_current_statuses(self.execution_id)

    def get_execution_by_argo_id(self, argo_id):
        query = '''            
            query ($argo_name: String){
                execution(where: {argo_name: {_eq: $argo_name}}){
                    id
                }
            }
        '''
        response = hce(current_app.config, query, variable_values={'argo_name': argo_id})
        logger.info(f'Response for `get_execution_by_argo_id({argo_id})` | {response}')
        return response['execution'][0]['id']

    def get_current_statuses(self, execution_id):
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
        response = hce(current_app.config, query, variable_values={'execution_id': execution_id})
        logger.info(f'List of current statuses for execution {execution_id} | {response}')
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
            'stage': stage, 'level': level, 'msg': msg,
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
            logger.exception(f'Current status for stage {stage} does not exist')
            return None

    def parse_status_for(self, stage, data):
        current_status = self.get_current_status_for(stage)
        phase = data.get('phase', '').upper()
        if phase is not None and current_status != phase:
            level = 'error' if phase in (Status.FAILED.value, Status.ERROR.value) else 'info'
            self.insert_execution_stage_log(stage, level, phase)

    def parse_load_tests_status(self, data):
        logger.info(f'Detected load_tests pods {data}')
        current_status = self.get_current_status_for('argo_load_tests')
        argo_load_tests_statuses = [d.get('phase').upper() for d in data]
        if Status.ERROR.value in argo_load_tests_statuses and current_status != Status.ERROR.value:
            self.insert_execution_stage_log('argo_load_tests', 'error', Status.ERROR.value)
        elif Status.FAILED.value in argo_load_tests_statuses and current_status != Status.FAILED.value:
            self.insert_execution_stage_log('argo_load_tests', 'error', Status.FAILED.value)
        elif Status.PENDING.value in argo_load_tests_statuses and current_status != Status.PENDING.value:
            self.insert_execution_stage_log('argo_load_tests', 'info', Status.PENDING.value)
        elif Status.RUNNING.value in argo_load_tests_statuses and current_status != Status.RUNNING.value:
            self.insert_execution_stage_log('argo_load_tests', 'info', Status.RUNNING.value)
        elif Status.SUCCEEDED.value in argo_load_tests_statuses and current_status != Status.SUCCEEDED.value:
            self.insert_execution_stage_log('argo_load_tests', 'info', Status.SUCCEEDED.value)

    def parse_argo_statuses(self, argo_data):
        logger.info(f'Start parsing argo data {argo_data}')
        load_tests_data = []
        for key, value in argo_data.get('nodes', {}).items():
            if value['type'] is not ArgoFlow.POD.value:
                continue
            if value['templateName'] is ArgoFlow.PRE_START.value:
                logger.info(f'Detected pre_start argo pod {value}')
                self.parse_status_for('argo_pre_start', value)
            elif value['templateName'] is ArgoFlow.POST_STOP.value:
                logger.info(f'Detected post_stop argo pod {value}')
                self.parse_status_for('argo_post_stop', value)
            elif value['templateName'] is ArgoFlow.MONITORING.value:
                logger.info(f'Detected monitoring argo pod {value}')
                self.parse_status_for('argo_monitoring', value)
            elif value['templateName'] in (ArgoFlow.LOAD_TESTS_MASTER.value, ArgoFlow.LOAD_TESTS_SLAVE.value):
                load_tests_data.append(value)  # aggregate records for master/slaves
        # analyze and parse together data for slaves and for master
        self.parse_load_tests_status(load_tests_data)
