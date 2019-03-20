import json

import graphene
from flask import current_app
from gql import gql

from app.appgraph.util import get_request_role_userid, ValidationInterface, OutputValueFromFactory, \
    OutputInterfaceFactory
from app import validators, const
from app.hasura_client import hasura_client


class ScaffoldInterface(graphene.Interface):
    id = graphene.UUID()


class CreateUpdateValidateScaffold:
    """
    Define and init an instance of this class as mutation implementations.
    """

    # inputs:
    TableName = ''
    BaseName = 'CUV'
    # Output interface class
    InterfaceClass = None
    # respective class Arguments
    CreateArgumentsClass = None
    UpdateArgumentsClass = None
    # respective allowed roles
    create_allowed_roles = (const.ROLE_ADMIN,)
    update_allowed_roles = (const.ROLE_ADMIN,)

    # output mutation implementations, call init() first
    CreateMutation = None
    UpdateMutation = None
    CreateValidateMutation = None
    UpdateValidateMutation = None
    # TODO:
    DeleteMutation = None
    # TODO: maybe
    DeleteValidateMutation = None

    def __init__(self):
        assert self.TableName, 'table name not set'
        assert self.InterfaceClass, 'Output interface class not set'
        assert issubclass(self.InterfaceClass, (graphene.Interface,)), 'Output interface class must implement graphene.Interface'
        assert self.CreateArgumentsClass, 'undefined input arguments for Create class'
        assert self.UpdateArgumentsClass, 'undefined input arguments for Update class'

        self.CreateMutation = self.create_class_factory()
        self.CreateValidateMutation = self.create_validate_class_factory()
        self.UpdateMutation = self.update_class_factory()
        self.UpdateValidateMutation = self.update_validate_class_factory()

    def user_role_create_allowed(self, info):
        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert role in self.create_allowed_roles, f'user with role {role} cannot create objects'
        return role, user_id

    @classmethod
    def user_role_update_allowed(cls, info):
        role, user_id = get_request_role_userid(info)
        assert user_id, f'unauthenticated request'
        assert role in cls.update_allowed_roles, f'user with role {role} cannot update objects'
        return role, user_id

    def create_validate(self, info, role, user_id, **kwargs):
        """This is valled from both Create and CreateValidate mutations.
        Must return validated data as dict: {'column_name': value}
        """
        raise NotImplementedError('please provide your own create validation logic')

    def update_validate(self, info, role, user_id, id, **kwargs):
        """This is valled from both Create and CreateValidate mutations.
        Must return validated data as dict: {'column_name': value}
        """
        raise NotImplementedError('please provide your own update validation logic')

    def create(self, info, role, user_id, validated_data):
        gclient = hasura_client(current_app.config)

        validated_keys = ' '.join(validated_data.keys())

        query = '''mutation ($data:[%(TableName)s_insert_input!]!) {
            insert_%(TableName)s(
                objects: $data
            ) {
                returning { %(returning)s } 
            }
        }''' % {'TableName': self.TableName, 'returning': validated_keys}

        conf_response = gclient.execute(gql(query), variable_values={'data': validated_data})
        assert conf_response[f'insert_{self.TableName}'], f'cannot save {self.TableName} ({str(conf_response)})'

        return OutputValueFromFactory(self.InterfaceClass, conf_response[f'insert_{self.TableName}'])

    def _do_create_validate(self, info, **kwargs):
        role, user_id = self.user_role_create_allowed(info)
        return self.create_validate(info, role, user_id, **kwargs)

    def _do_create(self, info, **kwargs):
        role, user_id = self.user_role_create_allowed(info)
        validated_data = self.create_validate(info, role, user_id, **kwargs)
        self.create(info, role, user_id, validated_data)

    def update(self, info, role, user_id, id, validated_data):
        gclient = hasura_client(current_app.config)

        validated_keys = ' '.join(validated_data.keys())

        query = '''mutation ($id:uuid!, $data:%(TableName)s_set_input!) {
            update_%(TableName)s(
                where:{id:{_eq:$id}},
                _set: $data
            ) {
                returning { %(returning)s } 
            }
        }''' % {'TableName': self.TableName, 'returning': validated_keys}

        conf_response = gclient.execute(gql(query), variable_values={'id': str(id), 'data': validated_data})
        assert conf_response[f'update_{self.TableName}'], f'cannot update {self.TableName} ({str(conf_response)})'

        return OutputValueFromFactory(self.InterfaceClass, conf_response[f'update_{self.TableName}'])

    @classmethod
    def _do_update_validate(cls, info, **kwargs):
        role, user_id = cls.user_role_update_allowed(info)
        obj_id = kwargs.pop('id', None)
        return cls.update_validate(info, role, user_id, obj_id, **kwargs)

    def _do_update(self, info, id, **kwargs):
        role, user_id = self.user_role_update_allowed(info)
        validated_data = self.update_validate(info, role, user_id, **kwargs)
        self.update(info, role, user_id, id, validated_data)

    # factories, overwrite here if necessary
    def create_class_factory(self):
        return type(self.BaseName + 'Create', (graphene.Mutation,), {
            'Output': OutputInterfaceFactory(self.InterfaceClass, 'Create'),
            'Arguments': self.CreateArgumentsClass,
            'mutate': self._do_create,
            'create_validate': self.create_validate,
        })

    def create_validate_class_factory(self):
        return type(self.BaseName + 'CreateValidate', (graphene.Mutation,), {
            'Output': ValidationInterface,
            'Arguments': self.CreateArgumentsClass,
            'mutate': self._do_create_validate,
            'create_validate': self.create_validate,
        })

    def update_class_factory(self):
        return type(self.BaseName + 'Update', (graphene.Mutation,), {
            'Output': OutputInterfaceFactory(self.InterfaceClass, 'Update'),
            'Arguments': self.UpdateArgumentsClass,
            'mutate': self._do_update,
            'update_validate': self.update_validate,
        })

    @classmethod
    def update_validate_class_factory(cls):
        return type(cls.BaseName + 'UpdateValidate', (graphene.Mutation,), {
            'Output': ValidationInterface,
            'Arguments': cls.UpdateArgumentsClass,
            'mutate': cls._do_update_validate,
            'update_validate': cls.update_validate,
        })
