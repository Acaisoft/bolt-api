import os
import yaml
import json
import subprocess

from . import templates


class Client:
    def __init__(self, executions_path):
        self.executions_path = executions_path

    def _run_template(self, template, execution_id):
        file_path = os.path.join(self.executions_path, execution_id + '.yaml')
        with open(file_path, 'w+') as file:
            file.write(yaml.dump(template))

        result = subprocess.check_output(['argo', 'submit', file_path, '-n', 'argo', '--serviceaccount', 'argo'])
        return result

    def run_master_slave(self, jwt, execution_id, tenant_id, project_id, repository_url, slaves_count, monitoring=False):
        template = templates.get_master_slave_template(jwt, execution_id, tenant_id, project_id, repository_url)
        slave_entry = {
            'name': 'locust-slave-',
            'template': 'slave',
            'dependencies': ['locust-master'],
            'arguments': {
                'parameters': [{'name': 'master-ip', 'value': '{{tasks.locust-master.ip}}'}]
            }
        }

        monitoring_entry = {
            'name': 'locust-monitoring',
            'template': 'monitoring',
        }

        tests_index = int([i for i, d in enumerate(template['spec']['templates']) if d['name'] == 'locust-tests'][0])

        if monitoring:
            template['spec']['templates'][tests_index]['dag']['tasks'].append(monitoring_entry)

        for i in range(slaves_count):
            entry = slave_entry.copy()
            entry['name'] += str(i)
            template['spec']['templates'][tests_index]['dag']['tasks'].append(entry)

        template = json.loads(json.dumps(template))  # since template was tempered with dumping it directly to yaml isnt working properly

        return self._run_template(template, execution_id)
