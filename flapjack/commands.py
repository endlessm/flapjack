# Copyright 2017 Endless Mobile, Inc.

import argparse
import operator
import os
import os.path
import shutil
import subprocess
import sys

from . import config, ext, state, util

"""Module that contains the base class for flapjack CLI subcommands, the
mechanism for registering them, and the built-in subcommands. (If subcommands
get more complicated, consider putting them in their own module.)"""

_command_registry = {}
_REPO = os.path.join(config.workdir(), 'repo')

_NON_GIT_SOURCE_MESSAGE = """
Only sources of type "git" are currently supported. You can override this
module with a git repository by setting a key in your config file:
[{module}]
url = ...
"""


def set_verbose(level):
    ext.verbose_level = level


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


def get_all_commands():
    """Get all commands grouped by their parameter requirements."""
    commands = {
        'all': _command_registry.keys(),
        'requiring module': [],
        'requiring app': [],
        'no params': [],
    }
    for name in commands['all']:
        command = get_command(name)
        action_dests = []
        for action in command.parser._actions:
            action_dests.append(action.dest)

        if 'module' in action_dests:
            commands['requiring module'].append(name)
        elif 'app' in action_dests:
            commands['requiring app'].append(name)
        else:
            commands['no params'].append(name)

    return commands


def get_help_text():
    """One line of each command name and description."""
    retval = ''
    for cmd, klass in sorted(list(_command_registry.items()),
                             key=operator.itemgetter(0)):
        retval += '  {:12} {}\n'.format(cmd, klass.__doc__)
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


def find_remote_for_runtime(runtime, branch):
    """Search for the runtime in all configured remotes. Expensive check."""
    remotes_list = ext.flatpak('remotes', output=True).split('\n')[1:-1]
    remotes = [line.split(maxsplit=1) for line in remotes_list if line]
    for candidate_remote in remotes:
        candidate_remote_name = candidate_remote[0]
        runtimes_list = ext.flatpak('remote-ls', candidate_remote_name,
                                    '--runtime', '-d', output=True)
        runtimes_list = runtimes_list.split('\n')[1:]
        for line in runtimes_list:
            if not line:
                continue
            quad = line.split(maxsplit=1)[0]
            candidate_id, _, candidate_branch = quad.split('/')[1:]
            if candidate_id == runtime and candidate_branch == branch:
                return candidate_remote

    raise RuntimeError('{} not found in any remotes: I checked {}'.format(
        runtime, ', '.join(remotes)))


def ensure_runtime(remote, runtime, branch, subpaths=False):
    if ext.flatpak('info', '--show-commit', runtime, branch, code=True) != 0:
        if remote is None:
            remote_name, remote_type = find_remote_for_runtime(runtime, branch)
            # Don't assume yes here, since Flapjack picked an arbitrary remote
            ext.flatpak('install', '--{}'.format(remote_type), remote_name,
                        runtime, branch)
        else:
            ext.flatpak('install', '--assumeyes', remote, runtime, branch)
    if subpaths:
        ext.flatpak('update', '--assumeyes', '--subpath=', runtime, branch)
    else:
        ext.flatpak('update', '--assumeyes', runtime, branch)


def ensure_base_sdk():
    ext.flatpak('remote-add', '--if-not-exists', '--from',
                config.sdk_repo_name(), config.sdk_repo_definition())
    ensure_runtime(config.sdk_repo_name(), config.sdk_id(),
                   config.sdk_branch())
    ensure_runtime(config.sdk_repo_name(), config.sdk_id() + '.Debug',
                   config.sdk_branch())
    ensure_runtime(config.sdk_repo_name(), config.sdk_id() + '.Locale',
                   config.sdk_branch(), subpaths=True)


def ensure_dev_sdk():
    ext.flatpak('remote-add', '--if-not-exists', '--no-gpg-verify', 'flapjack',
                _REPO)
    ensure_runtime('flapjack', config.dev_sdk_id(), 'master')
    ensure_runtime('flapjack', config.dev_sdk_id() + '.Debug', 'master')


def ensure_add_extensions():
    """Examines the add_extensions config key, and the manifest's add-extensions
    key, and attempts to install any extensions mentioned there. Looks through
    all the configured remotes."""
    for add_extension in config.add_extensions():
        ext_id = add_extension.split(':', 1)[0]
        branch = None
        if '/' in ext_id:
            ext_id, _, branch = ext_id.split('/', 2)
        ensure_runtime(None, ext_id, 'master' if branch is None else branch)


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
                if module['sources'][0]['type'] != 'git':
                    print(_NON_GIT_SOURCE_MESSAGE.format(module=args.module))
                    return 1
                source = module['sources'][0]['url']

            ext.git(config.checkoutdir(), 'clone', source, args.module)
            if 'branch' in module['sources'][0]:
                ext.git(git_clone, 'checkout', module['sources'][0]['branch'])
        else:
            try:
                ext.git(git_clone, 'fetch')
            except subprocess.CalledProcessError:
                # Don't error if offline
                pass

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
        ensure_add_extensions()


@register_command('shell')
class Shell(Command):
    """Open a shell in the development runtime's sandbox"""

    def execute(self, args):
        env_vars = {
            # This will be used as $PS1 if the users don't have a
            # custom $PS1 in their .bashrc
            'PS1': "[($FLAPJACK_PROMPT_PREFIX) \\u@\\h \\W]\\$ ",

            # If the users do have a custom $PS1, it will override the
            # previous setting.  So we export this environment
            # variable that they can add to their custom $PS1.
            'FLAPJACK_PROMPT_PREFIX': config.shell_prefix(),
        }

        env_vars_list = list("--env={}={}".format(_key, val)
                             for _key, val in env_vars.items())

        opts = (['run', '--devel', '--command=bash',
                 '--filesystem={}'.format(config.workdir())] +
                config.shell_permissions() + env_vars_list +
                [config.dev_sdk_id()])
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

        options = ['--build-only']
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


@register_command('clean-cache')
class CleanCache(Command):
    """Clean the flatpak-builder cache"""

    def execute(self, args):
        cache_dir = os.path.join(config.workdir(), '.flatpak-builder')
        if os.path.isdir(cache_dir):
            shutil.rmtree(cache_dir, ignore_errors=True)
        return 0
