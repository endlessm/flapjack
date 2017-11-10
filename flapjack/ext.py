# Copyright 2017 Endless Mobile, Inc.

import collections
import contextlib
import copy
import json
import os.path
import subprocess

from . import config, state, util

"""Module for running external commands."""

_BUILD = os.path.join(config.workdir(), 'runtime-build')


def git(path, command, *args, output=False, code=False):
    """Run a git command in the git clone specified by `path`."""

    cmdline = ['git', command] + list(args)
    if output:
        return subprocess.check_output(cmdline, cwd=path)
    if code:
        return subprocess.call(cmdline, cwd=path)
    subprocess.check_call(cmdline, cwd=path)


def _takes_user_arg(command):
    """Only certain flatpak commands take the --user argument, but we want to
    ensure it's applied consistently throughout flapjack."""
    return command in ('install', 'update', 'uninstall', 'list', 'info',
                       'remote-add', 'remote-modify', 'remote-delete',
                       'remote-ls', 'remotes', 'make-current')


def flatpak(command, *args, output=False, code=False):
    """Run a flatpak command."""

    user_arg = []
    if config.user_installation() and _takes_user_arg(command):
        user_arg = ['--user']

    cmdline = (['flatpak', command] + user_arg + list(args))
    if output:
        return subprocess.check_output(cmdline)
    if code:
        return subprocess.call(cmdline)
    subprocess.check_call(cmdline)


def _generate_manifest():
    source = util.get_source_manifest()
    manifest = copy.deepcopy(source)

    # Put any changes here that are necessary to remove stuff that only applies
    # to the original runtime's flatpak-builder manifest
    manifest['separate-locales'] = False
    manifest['id'] = config.dev_sdk_id()
    manifest.pop('id-platform', None)
    manifest['branch'] = 'master'
    manifest['runtime'] = manifest['sdk'] = config.sdk_id()
    manifest['runtime-version'] = config.sdk_branch()
    manifest.pop('metadata', None)
    manifest.pop('metadata-platform', None)
    manifest['sdk-extensions'] = [config.sdk_id() + '.Debug',
                                  config.sdk_id() + '.Locale']
    manifest.pop('platform-extensions', None)
    manifest.pop('inherit-extensions', None)
    manifest.pop('add-extensions', None)
    manifest.pop('cleanup-platform', None)
    manifest.pop('cleanup-platform-commands', None)
    build_options = manifest.setdefault('build-options', {})
    build_options['strip'] = False
    build_options['no-debuginfo'] = True
    manifest['finish-args'] = \
        [arg for arg in manifest.setdefault('finish-args', [])
         if (not arg.startswith('--sdk') and
             not arg.startswith('--runtime'))]

    # Make sure to maintain order of modules in the output manifest
    open_modules = [m for m in manifest['modules']
                    if (m['name'] in state.get_open_modules() and
                        m['name'] in config.modules())]
    for m in open_modules:
        m['sources'] = [collections.OrderedDict([
            ('type', 'git'),
            ('branch', 'flapjack'),
            ('url', '{}/{}'.format(config.checkoutdir(), m['name'])),
        ])]

        build_options = m.get('build-options', {})
        m['build-options'] = build_options

        for flags_key in ('cflags', 'cppflags', 'cxxflags', 'ldflags'):
            flags = getattr(config, 'module_extra_' + flags_key)(m['name'])
            if flags:
                old_flags = build_options.get(flags_key, '')
                build_options[flags_key] = ' '.join([old_flags, flags])

        config_opts = config.module_extra_config_opts(m['name'])
        if config_opts:
            m['config-opts'] = m.get('config-opts', []) + config_opts

    manifest['modules'] = util.get_dev_tools_manifest() + open_modules

    return manifest


@contextlib.contextmanager
def _branch_state(path):
    """Switches a git clone to the "flapjack" branch and makes a temporary
    commit if necessary. Restores the previous state when exiting the with
    block. Used in several commands."""

    rev = None
    changes = False

    if (git(path, 'diff', '--quiet', '--cached', '--exit-code',
            code=True) != 0):
        raise RuntimeError('{} has staged changes. Currently, "flapjack build"'
                           ' will clobber them. Please either commit or '
                           'unstage.'.format(path))

    if os.path.exists(os.path.join(path, '.git', 'MERGE_HEAD')):
        raise RuntimeError('{} is in the middle of a merge. Please finish it '
                           'before building.'.format(path))

    rev = git(path, 'rev-parse', '--abbrev-ref', 'HEAD', output=True)
    rev = rev.decode().strip()

    git(path, 'checkout', '-B', 'flapjack')

    changes = bool(git(path, 'status', '--porcelain', output=True))
    if changes:
        git(path, 'add', '.')
        git(path, 'commit', '--message', 'Temporary commit for Flapjack')

    try:
        yield
    finally:
        if changes:
            git(path, 'reset', 'HEAD^')
        git(path, 'checkout', rev)


class _BranchAllModules(contextlib.ExitStack):
    def __enter__(self):
        for module in state.get_open_modules():
            git_clone = os.path.join(config.checkoutdir(), module)
            self.enter_context(_branch_state(git_clone))


def flatpak_builder(*args, check=None, distcheck=False):
    """Run flatpak-builder to build the dev runtime, generating and writing a
    flatpak-builder manifest. @check specifies a module for which to run the
    tests."""

    manifest = _generate_manifest()

    stop_arg = []
    if check:
        check_index, check_module = next(
            (ix, m) for ix, m in enumerate(manifest['modules'])
            if m['name'] == check)
        testcmd = 'make distcheck' if distcheck else 'make check'
        if check_module.get('buildsystem', None) == 'meson':
            testcmd = 'ninja test'

        build_commands = check_module.setdefault('build-commands', [])
        build_commands.insert(0, testcmd)

        build_options = check_module.setdefault('build-options', {})
        build_options['build-args'] = (config.test_permissions() +
                                       build_options.get('build-args', []))

        try:
            next_module = manifest['modules'][check_index + 1]['name']
            stop_arg = ['--stop-at={}'.format(next_module)]
        except IndexError:
            pass  # checked module was the last module

    with open(config.manifest(), 'w') as f:
        json.dump(manifest, f, indent=4)

    cmdline = (['flatpak-builder', '--force-clean'] + list(args) + stop_arg +
               [_BUILD, config.manifest()])

    with _BranchAllModules():
        return subprocess.call(cmdline, cwd=config.workdir())
