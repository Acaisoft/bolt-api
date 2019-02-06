import string
from collections import namedtuple

from gql import gql, Client


class BaseQuery(object):
    client = None
    bulk_size = 200
    input_type = namedtuple("override_me", [
        "id",
    ])

    object_template = string.Template('''{
      id:"$id",
    },''')

    insert_template = string.Template('''
    mutation {
        insert_$classname(objects: [ $objects ]) { returning { id } } 
    }
    ''')

    def __init__(self, client: Client):
        self.client = client

    def serialize(self, input_type_object):
        if isinstance(input_type_object, str):
            return input_type_object
        if isinstance(input_type_object, self.input_type):
            return self.object_template.substitute(**input_type_object._asdict())
        if isinstance(input_type_object, dict):
            return self.object_template.substitute(**input_type_object)
        raise TypeError("input_type_object must be a dict or an instance of self.input_type type")

    def bulk_insert(self, data):
        bulk = ""
        bulked = self.bulk_size

        for i in iter(data):
            if bulked > 0:
                bulk += self.serialize(i)
                bulked -= 1
            else:
                self.insert_string(bulk)
                bulk = ""
                bulked = self.bulk_size

        if bulk:
            return self.insert_string(bulk)

    def insert_string(self, objects_string: string):
        body = self.insert_template.substitute(classname=self.input_type.__name__, objects=objects_string)
        print(body)
        query = gql(body)
        return self.client.execute(query)

    def insert(self, objects_str_or_type):
        obj = self.serialize(objects_str_or_type)
        return self.insert_string(obj)
