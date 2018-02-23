# Copyright 2017 Endless Mobile, Inc.

import configparser
import os.path
import shlex

_CONFIG_FILE = os.path.expanduser('~/.config/flapjack.ini')
_DEFAULTS = {
    'Common': {
        'workdir': '~/flapjack',
        'checkoutdir': '${workdir}/checkout',
        'shell_prefix': 'flapjack',
        'user_installation': 'no',

        'sdk_upstream': 'git://git.gnome.org/gnome-sdk-images',
        'sdk_upstream_branch': 'master',
        'sdk_id': 'org.gnome.Sdk',
        'sdk_branch': 'master',
        'sdk_manifest_json': '${sdk_id}.json.in',
        'sdk_repo_name': 'flapjack-source',
        'sdk_repo_definition':
            'https://sdk.gnome.org/gnome-nightly.flatpakrepo',
        'dev_sdk_id': 'org.gnome.dev.Sdk',

        # default modules are from meta-gnome-devel-platform in jhbuild
        'modules': 'glib pango atk at-spi2-core at-spi2-atk gtk3',
    },
}

_interp = configparser.ExtendedInterpolation()
_config = configparser.ConfigParser(interpolation=_interp)
# Default is case-insensitive keys, we need case-sensitive for the environment
# variable sections
_config.optionxform = lambda option: option
_config.read_dict(_DEFAULTS)
try:
    with open(_CONFIG_FILE) as f:
        _config.read_file(f, source=_CONFIG_FILE)
except FileNotFoundError:
    pass  # no config file, use all defaults


class _Getter:
    """Helper to reduce tedium of defining a getter for every config option."""
    def __init__(self, key, op=_config.get):
        self.key = key
        self.op = op

    def __call__(self):
        return self.op('Common', self.key, fallback=None)


def _string_expandtilde(*args, **kw):
    val = _config.get(*args, **kw)
    if val is not None:
        return os.path.expanduser(val)
    return val


def _ws_sep_list(*args, **kw):
    val = _config.get(*args, **kw)
    if val is not None:
        return val.split()
    return []


def _shell_list(*args, **kw):
    val = _config.get(*args, **kw)
    if val is not None:
        return shlex.split(val)
    return []


workdir = _Getter('workdir', _string_expandtilde)
checkoutdir = _Getter('checkoutdir', _string_expandtilde)
shell_prefix = _Getter('shell_prefix')
user_installation = _Getter('user_installation', _config.getboolean)
sdk_upstream = _Getter('sdk_upstream')
sdk_upstream_branch = _Getter('sdk_upstream_branch')
sdk_id = _Getter('sdk_id')
sdk_branch = _Getter('sdk_branch')
sdk_manifest_json = _Getter('sdk_manifest_json')
sdk_repo_name = _Getter('sdk_repo_name')
sdk_repo_definition = _Getter('sdk_repo_definition')
dev_sdk_id = _Getter('dev_sdk_id')
dev_tools_manifest = _Getter('dev_tools_manifest', _string_expandtilde)
modules = _Getter('modules', _ws_sep_list)
test_permissions = _Getter('test_permissions', _ws_sep_list)
shell_permissions = _Getter('shell_permissions', _ws_sep_list)


class _ModuleGetter(_Getter):
    """Similar to _Getter but for a module-specific config option."""
    def __call__(self, module):
        if not _config.has_section(module):
            return None
        return self.op(module, self.key, fallback=None)


module_url = _ModuleGetter('url')
module_extra_cflags = _ModuleGetter('extra_cflags')
module_extra_cppflags = _ModuleGetter('extra_cppflags')
module_extra_cxxflags = _ModuleGetter('extra_cxxflags')
module_extra_ldflags = _ModuleGetter('extra_ldflags')
module_extra_config_opts = _ModuleGetter('extra_config_opts', _shell_list)
module_extra_build_args = _ModuleGetter('extra_build_args', _shell_list)
module_extra_make_args = _ModuleGetter('extra_make_args', _shell_list)
module_extra_test_args = _ModuleGetter('extra_test_args', _shell_list)
module_extra_make_install_args = _ModuleGetter('extra_make_install_args',
                                               _shell_list)


def module_extra_env(module):
    """Returns a dictionary of environment variables to add to the build
    environment for a specific module, specified by a [$MODULE.extra_env]
    section in the config file."""
    section = module + '.extra_env'
    if not _config.has_section(section):
        return None
    return {key: value for key, value in _config.items(section)}


def manifest():
    """Returns the path in the workdir where the dev SDK manifest is
    located."""
    return os.path.join(workdir(), dev_sdk_id() + '.json')


def upstream_sdk_checkout():
    """Returns the path where the upstream SDK git repo is cloned."""
    sdk_repo_name = sdk_upstream().rsplit('/', 1)[-1]
    return os.path.join(checkoutdir(), sdk_repo_name)


def source_manifest():
    """Returns the path to the manifest of the upstream SDK being developed."""
    return os.path.join(upstream_sdk_checkout(), sdk_manifest_json())
