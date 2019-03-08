import click
from flask import current_app
from flask.cli import with_appcontext
from gql import gql

from app import const
from app.deployer.utils import get_test_run_status
from bolt_api.upstream.devclient import devclient


@click.command(name='testrun_status')
@with_appcontext
def testrun_status():
    executions = devclient(current_app.config).execute(gql('''query ($finalStates:[String!]!) {
        execution(where:{status:{_nin:$finalStates}}) { id, status }
    }'''), {'finalStates': [
        const.TESTRUN_FINISHED,
        const.TESTRUN_CRASHED,
    ]})

    for i in executions.get('execution', []):
        try:
            new_state, deployer_response = get_test_run_status(i.get('id'))
        except Exception as e:
            print(f'{i.get("status")} job id {i.get("id")} error: {str(e)}')
        else:
            print(f'{i.get("status")} -> {new_state} for job id {i.get("id")} with bolt-deplyer response: {str(deployer_response)}')
