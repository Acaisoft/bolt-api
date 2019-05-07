import graphene
from flask import current_app

from apps.bolt_api.app.appgraph.extension.types import ExtensionParamInput, ExtensionType
from services import const, gql_util
from services import validators
from services.hasura import hce


class CreateValidate(graphene.Mutation):
    """Validates single extension."""

    class Arguments:
        configuration_id = graphene.UUID()
        type_slug = graphene.String(
            required=True,
            description=f'Extension type: "{const.EXTENSION_CHOICE}"')
        params = graphene.List(
            ExtensionParamInput,
            required=True,
            description='Extension parameters.')

    Output = gql_util.ValidationInterface

    @staticmethod
    def validate(info, configuration_id, type_slug, params):
        configuration_id = str(configuration_id)

        assert type_slug in const.EXTENSION_CHOICE, f'invalid choice of type_slug (valid choices: {const.EXTENSION_CHOICE})'

        role, user_id = gql_util.get_request_role_userid(info, (const.ROLE_ADMIN, const.ROLE_MANAGER))

        resp = hce(current_app.config, '''query ($conf_id:uuid!, $user_id:uuid!) {
            configuration(where:{
                id:{ _eq:$conf_id }
                is_deleted:{ _eq:false }
                project:{
                    is_deleted:{ _eq:false }
                    userProjects:{user_id:{ _eq:$user_id }}
                }
            }) {
                id
            }
        }''', {
            'user_id': user_id,
            'conf_id': configuration_id,
        })
        assert resp['configuration'], f'configuration not found'

        validators.validate_single_extension({
            'type': type_slug,
            'extension_params': params,
        })

        ex_params = []
        for ep in params:
            ex_params.append({
                'name': ep['name'],
                'value': ep['value'],
            })

        query = {
            'type': type_slug,
            'configuration_id': configuration_id,
            'extension_params': {
                'data': ex_params,
            }
        }

        return query

    def mutate(self, info, configuration_id, type_slug, params):
        CreateValidate.validate(info, configuration_id, type_slug, params)
        return gql_util.ValidationResponse(ok=True)


class Create(CreateValidate):
    """Validates and saves single extension."""

    Output = gql_util.OutputTypeFactory(ExtensionType, 'Create')

    def mutate(self, info, configuration_id, type_slug, params):

        query_params = CreateValidate.validate(info, configuration_id, type_slug, params)

        query = '''mutation ($data:configuration_extension_insert_input!) {
            insert_configuration_extension(objects: [$data]) {
                affected_rows
                returning {
                    id
                    type_slug:type
                    configuration_id
                    params:extension_params {
                        name
                        value
                    }
                }
            }
        }'''

        resp = hce(current_app.config, query, variable_values={'data': query_params})
        assert resp['insert_configuration_extension'], f'cannot save extension configuration ({str(resp)})'

        return gql_util.OutputValueFromFactory(Create, resp['insert_configuration_extension'])
