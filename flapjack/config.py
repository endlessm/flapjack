# Copyright 2017 Endless Mobile, Inc.

import os.path

_CONFIG_FILE = os.path.expanduser('~/.config/flapjackconfig.py')

workdir = os.path.expanduser('~/flapjack')
checkoutdir = None  # compute from workdir if not specified

sdk_upstream = 'git://git.gnome.org/gnome-sdk-images'
sdk_id = 'org.gnome.Sdk'
sdk_manifest_json = None  # compute from sdk_id if not specified
sdk_repo_name = 'flapjack-source'
sdk_repo_definition = 'https://sdk.gnome.org/gnome-nightly.flatpakrepo'
dev_sdk_id = 'org.gnome.dev.Sdk'

# default modules are from meta-gnome-devel-platform in jhbuild
modules = [
    'glib',
    'pango',
    'atk',
    'at-spi2-core',
    'at-spi2-atk',
    'gtk3',
]
extra_module_config_opts = {}
dev_tools_manifest = None
test_permissions = []
shell_permissions = []

try:
    with open(_CONFIG_FILE) as f:
        code = compile(f.read(), _CONFIG_FILE, 'exec')
        exec(code)
except FileNotFoundError:
    pass  # no config file, use all defaults

# Compute variables from other variables if they have default values depending
# on other variables but weren't defined in the config file

if not checkoutdir:
    checkoutdir = os.path.join(workdir, 'checkout')
if not sdk_manifest_json:
    sdk_manifest_json = sdk_id + '.json.in'

# Functions are used to compute variables that are derived from config
# file variables


def manifest():
    """Returns the path in the workdir where the dev SDK manifest is
    located."""
    return os.path.join(workdir, dev_sdk_id + '.json')


def upstream_sdk_checkout():
    """Returns the path where the upstream SDK git repo is cloned."""
    sdk_repo_name = sdk_upstream.rsplit('/', 1)[-1]
    return os.path.join(checkoutdir, sdk_repo_name)


def source_manifest():
    """Returns the path to the manifest of the upstream SDK being developed."""
    return os.path.join(upstream_sdk_checkout(), sdk_manifest_json)
