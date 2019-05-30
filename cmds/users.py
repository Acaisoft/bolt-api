import click
from flask.cli import with_appcontext
from services.user_management import user_management


@click.command(name='user_create')
@click.argument('email', required=True)
@click.argument('project', required=True)
@click.argument('role', required=True)
@with_appcontext
def user_create(email, project, role):
    """
    Create a user in keycloak with given roles.
    """
    user_management.user_create(email, project, role)


@click.command(name='user_create_registration_token')
@click.argument('project', required=True)
@click.argument('role', required=True)
@with_appcontext
def user_create_registration_token(project, role):
    """
    Open registration to given project with given default role.
    Return a registration token.
    """
    full, short = user_management.user_create_registration_token(project, role)
    print(f'full registration token: {full}\nshort token: {short}')


@click.command(name='user_register')
@click.argument('email', required=True)
@click.argument('token', required=True)
@with_appcontext
def user_register(email, token):
    """
    Register user account, given an email and a registration token.
    Return new user id.
    """
    user_id = user_management.user_register(email, token)
    print(f'user account has been created, please go to login page')


@click.command(name='disable_registration')
@click.argument('project_id', required=False)
@with_appcontext
def disable_registration(project_id=None):
    """
    Disable registratino to project or to all projects.
    """
    user_management.disable_registration(project_id)


@click.command(name='user_list_in_project')
@click.argument('project', required=True)
@with_appcontext
def user_list_in_project(project):
    """
    List keycloak users with access to given repo.
    """
    users = user_management.list_users_in_project(project)
    for i in users:
        print(i)


@click.command(name='user_assign_role')
@click.argument('user_id', required=True)
@click.argument('roles', required=True)
@with_appcontext
def user_assign_role(user_id, roles):
    """
    Change keycloak user's roles.
    """
    user_management.user_roles_update(user_id, roles)


@click.command(name='user_unassign')
@click.argument('user_id', required=True)
@click.argument('project_id', required=True)
@with_appcontext
def user_unassign(user_id, project_id):
    """
    Unassign a user from a project.
    """
    resp = user_management.user_unassign_from_project(user_id, project_id)
    print(resp)
