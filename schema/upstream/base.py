import string
from collections import namedtuple

from gql import gql, Client


class BaseQuery(object):
    client = None
    bulk_size = 40
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

    def bulk_insert(self, data):
        bulk = ""
        bulked = self.bulk_size

        for i in iter(data):
            if bulked > 0:
                bulk += self.object_template.substitute(**i._asdict())
                bulked -= 1
            else:
                self.insert(bulk)
                bulk = ""
                bulked = self.bulk_size

        if bulk:
            return self.insert(bulk)

    def insert(self, bulk_objects: string):
        if isinstance(bulk_objects, self.input_type):
            # TODO: solve without selfreference
            return self.bulk_insert([bulk_objects])
        body = self.insert_template.substitute(classname=self.input_type.__name__, objects=bulk_objects)
        query = gql(body)
        return self.client.execute(query)
