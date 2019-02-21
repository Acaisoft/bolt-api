from flask import Blueprint, current_app

from app.deployer import clients

bp = Blueprint('deployer_service', __name__)


@bp.route('/jobs')
def jobs():
    resp = clients.jobs(current_app.config).jobs_get('b45c834e-caf1-4587-9c95-be4707aed2bd')
    return str(resp)
