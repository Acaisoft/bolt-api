from setuptools import setup

setup(
    name='boltapi',
    version='0.1',
    packages=['schema', 'schema.upstream', 'schema.upstream.tests', 'dev_setup', 'hasura', 'hasura.migrations'],
    url='https://bitbucket.org/acaisoft/bolt-api/',
    license='',
    author='piotr',
    author_email='',
    description='',
    install_requires=[
        'graphene',
        'gql',
        'Flask',
        'requests',
    ],
)
