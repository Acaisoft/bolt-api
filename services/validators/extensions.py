from services import const
from schematics import types


def validate_extensions(confs:list):
    """
    Validate and convert extension configuration from hasura to deployer format.
    :param conf: extension configuration in hasura format
    :return: extension arguments map suitable for bolt-deployer
    """
    out = []
    for conf in confs:
        assert conf.get('type', None) in const.EXTENSION_CHOICE, f'invalid extension type'

        if conf['type'] == const.EXTENSION_NFS:
            out.append(validate_nfs(conf.get('extension_params', {})))

    return out


def validate_nfs(conf:list):
    nfs_params = ('server', 'path')
    out = {
        'type': const.EXTENSION_NFS,
    }
    m_opts = []
    for i in conf:
        if i['name'] in nfs_params:
            out[i['name']] = i['value']
        elif i['name'] == 'mount_options':
            m_opts.append(i['value'])

    types.IPAddressType().validate(out.get('server', None))
    assert out.get('path', '').startswith('/'), f'missing or invalid NFS resource path'
    out['mount_options'] = m_opts
    return out
