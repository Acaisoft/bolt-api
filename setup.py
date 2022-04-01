from setuptools import setup, find_packages

setup(
    name='boltapi',
    version='0.2',
    packages=find_packages('upstream', 'upstream.tests', 'dev_setup'),
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
