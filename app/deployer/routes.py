from flask import Blueprint, current_app

from app.deployer import clients

bp = Blueprint('deployer_service', __name__)


@bp.route('/jobs/<tenant_id>')
def jobs(tenant_id):
    resp = clients.jobs(current_app.config).jobs_get(tenant_id=tenant_id)
    return str(resp)


@bp.route('/job/<job_id>')
def job(job_id):
    resp = clients.jobs(current_app.config).jobs_job_id_get(job_id=job_id)
    return str(resp)


@bp.route('/image/<image_id>')
def image(image_id):
    resp = clients.images(current_app.config).image_builds_task_id_get(task_id=image_id)
    return str(resp)
