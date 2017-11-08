# Copyright 2017 Endless Mobile, Inc.

import argparse
import operator
import os
import os.path
import subprocess
import sys

from . import config, ext, state, util

"""Module that contains the base class for flapjack CLI subcommands, the
mechanism for registering them, and the built-in subcommands. (If subcommands
get more complicated, consider putting them in their own module.)"""

_command_registry = {}
_REPO = os.path.join(config.workdir(), 'repo')


def register_command(name):
    """Decorator for use with command classes, makes the command available to
    flapjack's CLI and help text."""

    def decorator(klass):
        klass.NAME = name
        _command_registry[name] = klass
        return klass
    return decorator


def get_command(name):
    """Get an instance of a registered command class, ready to call run()."""
    return _command_registry[name]()


def get_help_text():
    """One line of each command name and description."""
    retval = ''
    for cmd, klass in sorted(list(_command_registry.items()),
                             key=operator.itemgetter(0)):
        retval += '  {:10} {}\n'.format(cmd, klass.__doc__)
    return retval


class Command:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='{} {}'.format(os.path.basename(sys.argv[0]), self.NAME),
            description=self.__doc__)

    def _quick_setup(self):
        # Setup tasks that are inexpensive enough to do on every startup
        # instead of as part of "flapjack setup"
        os.makedirs(config.checkoutdir(), exist_ok=True)
        os.makedirs(_REPO, exist_ok=True)

        subprocess.check_call(['ostree', 'init', '--repo', _REPO,
                               '--mode=bare-user'])

    def run(self, argv):
        args = self.parser.parse_args(argv)
        self._quick_setup()
        return self.execute(args)

    def execute(self, args):
        raise NotImplementedError


def ensure_runtime(remote, runtime, branch):
    if ext.flatpak('info', '--show-commit', runtime, branch, code=True) != 0:
        ext.flatpak('install', remote, runtime, branch)
    ext.flatpak('update', runtime, branch)


def ensure_base_sdk():
    ext.flatpak('remote-add', '--if-not-exists', '--from',
                config.sdk_repo_name(), config.sdk_repo_definition())
    ensure_runtime(config.sdk_repo_name(), config.sdk_id(),
                   config.sdk_branch())
    ensure_runtime(config.sdk_repo_name(), config.sdk_id() + '.Debug',
                   config.sdk_branch())
    ensure_runtime(config.sdk_repo_name(), config.sdk_id() + '.Locale',
                   config.sdk_branch())


def ensure_dev_sdk():
    ext.flatpak('remote-add', '--if-not-exists', '--no-gpg-verify', 'flapjack',
                _REPO)
    ensure_runtime('flapjack', config.dev_sdk_id(), 'master')
    ensure_runtime('flapjack', config.dev_sdk_id() + '.Debug', 'master')


@register_command('build')
class Build(Command):
    """Build a development flatpak runtime"""

    def execute(self, args):
        exitcode = ext.flatpak_builder('--require-changes', '--repo', _REPO)
        if exitcode != 0:
            return exitcode

        ensure_dev_sdk()


@register_command('close')
class Close(Command):
    """Close development on a module and remove it from the runtime"""

    def __init__(self):
        super().__init__()
        self.parser.add_argument('module', help='Module to close')

    def execute(self, args):
        currently_open = state.get_open_modules()
        currently_open.remove(args.module)
        state.set_open_modules(currently_open)


@register_command('list')
class List(Command):
    """List the modules available for development"""

    def execute(self, args):
        currently_open = state.get_open_modules()
        for m in config.modules():
            print(' {} {}'.format('*' if m in currently_open else ' ', m))


@register_command('open')
class Open(Command):
    """Open a module for development, putting it in the runtime"""

    def __init__(self):
        super().__init__()
        self.parser.add_argument('module', help='Module to open')

    def execute(self, args):
        currently_open = state.get_open_modules()
        if args.module in currently_open:
            return

        source_manifest = util.get_source_manifest()
        module = next(m for m in source_manifest['modules']
                      if m['name'] == args.module)

        git_clone = os.path.join(config.checkoutdir(), args.module)
        if not os.path.exists(git_clone):
            source = config.module_url(args.module)
            if source is None:
                source = module['sources'][0]['url']

            ext.git(config.checkoutdir(), 'clone', source, args.module)
            if 'branch' in module['sources'][0]:
                ext.git(git_clone, 'checkout', module['sources'][0]['branch'])
        else:
            ext.git(git_clone, 'fetch')

        currently_open += [args.module]
        state.set_open_modules(currently_open)


@register_command('run')
class Run(Command):
    """Run an app against the development runtime"""

    def __init__(self):
        super().__init__()
        self.parser.add_argument('app', help='ID of app to run')
        self.parser.add_argument('options', nargs=argparse.REMAINDER,
                                 help='Command-line options to pass to app')

    def execute(self, args):
        ensure_dev_sdk()
        opts = (['run', '--devel'] + config.shell_permissions() +
                ['--runtime={}//master'.format(config.dev_sdk_id()),
                 args.app] +
                args.options)
        ext.flatpak(*opts, code=True)
        # COMPAT: unpacking two lists supported in py3.5


@register_command('setup')
class Setup(Command):
    """Get set up to use flapjack for the first time"""

    def execute(self, args):
        if not os.path.exists(config.upstream_sdk_checkout()):
            ext.git(config.checkoutdir(), 'clone', '--branch',
                    config.sdk_upstream_branch(), config.sdk_upstream())
        else:
            ext.git(config.upstream_sdk_checkout(), 'checkout',
                    config.sdk_upstream_branch())

        ensure_base_sdk()


@register_command('shell')
class Shell(Command):
    """Open a shell in the development runtime's sandbox"""

    def execute(self, args):
        ensure_dev_sdk()
        opts = (['run', '--devel', '--command=bash',
                 '--filesystem={}'.format(config.workdir())] +
                config.shell_permissions() + [config.dev_sdk_id()])
        ext.flatpak(*opts, code=True)
        # COMPAT: unpacking non-final list supported in py3.5


@register_command('test')
class Test(Command):
    """Build a module and run its tests"""

    def __init__(self):
        super().__init__()
        self.parser.add_argument('module', help='Module to test')
        self.parser.add_argument('-s', '--shell', action='store_true',
                                 help='Open a debug shell in the sandbox used '
                                       'to run the tests')
        self.parser.add_argument('-d', '--distcheck', action='store_true',
                                 help='Run make distcheck instead of make '
                                      'check, for autotools modules')

    def execute(self, args):
        currently_open = state.get_open_modules()
        if args.module not in currently_open:
            print(args.module, 'is not currently opened for development. Use '
                  '"flapjack open"')
            return 1

        options = ['--build-only', '--keep-build-dirs']
        if args.shell:
            options += ['--build-shell={}'.format(args.module)]

        return ext.flatpak_builder(*options, check=args.module,
                                   distcheck=args.distcheck)


@register_command('update')
class Update(Command):
    """Update your runtimes and git checkouts"""

    def execute(self, args):
        ensure_base_sdk()

        there_were_errors = False
        for entry in os.listdir(config.checkoutdir()):
            git_clone = os.path.join(config.checkoutdir(), entry)
            if not os.path.isdir(git_clone):
                continue
            if not os.path.exists(os.path.join(git_clone, '.git')):
                continue
            if not ext.git(git_clone, 'remote', output=True):
                continue
            try:
                ext.git(git_clone, 'fetch')
            except subprocess.CalledProcessError:
                print('Error updating {}'.format(entry))
                there_were_errors = True

        if there_were_errors:
            print('Some repositories failed to update.')
            return 1
