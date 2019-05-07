from schematics.exceptions import ValidationError

from services import const
from schematics import types


def validate_extensions(confs: list):
    """
    Validate and convert extension configuration from hasura to deployer format.
    :param confs: extension configuration list in hasura format
    :return: extension arguments map suitable for bolt-deployer
    """
    out = []
    for conf in confs:
        out.append(validate_single_extension(conf))

    return out


def validate_single_extension(conf: dict):
    assert conf.get('type', None) in const.EXTENSION_CHOICE, f'invalid extension type'

    if conf['type'] == const.EXTENSION_NFS:
        return validate_nfs(conf.get('extension_params', {}))
    else:
        raise NotImplemented(f'extension type "{conf["type"]}" validation is not implemented')


def validate_nfs(conf: list):
    single_nfs_params = ('server', 'path')
    multi_nfs_params = ('mount_options',)
    all_nfs_params = single_nfs_params + multi_nfs_params
    out = {
        'name': const.EXTENSION_NFS,
    }
    m_opts = []
    for i in conf:
        if i['name'] in single_nfs_params:
            out[i['name']] = i['value']
        elif i['name'] in multi_nfs_params:
            m_opts.append(i['value'])
        else:
            raise AssertionError(f'invalid option for "{const.EXTENSION_NFS}": "{i["name"]}", valid choices are: {all_nfs_params}')

    types.IPAddressType().validate(out.get('server', ''))
    assert out.get('path', '').startswith('/'), f'missing or invalid NFS resource path'
    out['mount_options'] = m_opts
    return out