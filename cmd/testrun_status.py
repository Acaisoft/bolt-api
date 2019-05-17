import click
from flask import current_app
from flask.cli import with_appcontext

from services import const
from services.testruns.status import get_test_run_status
from services.hasura import hce


@click.command(name='testrun_status')
@with_appcontext
def testrun_status():
    executions = hce(current_app.config, '''query ($finalStates:[String!]!) {
        execution(where:{status:{_nin:$finalStates}}) { id, status }
    }''', {'finalStates': [
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
