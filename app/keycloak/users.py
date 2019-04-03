import json
from app.keycloak.clients import k_admin


def create_user_with_role(config, email, role):
    client = k_admin(config)

    needs_registration = True
    users = client.get_users({})

    for u in users:
        if u.get('email', '') == email:
            needs_registration = False

    if needs_registration:
        client.create_user({
            "email": email,
            "username": email,
            "enabled": True,
        })

        user_id = client.get_user_id(email)

        # force user to register and setup password
        client.send_update_account(user_id=user_id, payload=json.dumps(['UPDATE_PASSWORD']))
        client.send_verify_email(user_id=user_id)

    else:
        user_id = client.get_user_id(email)

    # assign bolt client role to user
    bolt_client_id = client.get_client_id('bolt-portal')
    role_id = client.get_client_role(client_id=bolt_client_id, role_name=role)
    client.assign_client_role(client_id=bolt_client_id, user_id=user_id, roles=[role_id])

    return user_id
