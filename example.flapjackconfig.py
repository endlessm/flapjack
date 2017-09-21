# -*- mode: python -*-
# -*- coding: utf-8 -*-

# This is your Flapjack config file. It's all Python. Examples of what you can
# configure are shown commented. Copy this file to ~/.config/flapjackconfig.py
# and customize it to your liking.
# The default configuration lets you hack on the org.gnome.Sdk runtime, with
# the core GNOME platform as the default set of modules. This config file
# illustrates how you might set up the Endless OS runtime.

# -- DIRECTORIES --------------------------------------------------------------

# Set `workdir` to the directory where Flapjack does all its work. An example
# use of this is if you want to maintain two Flapjack config files in order to
# hack on two runtimes at different times.

# import os.path
# workdir = os.path.expanduser('~/flapjack')

# Set `checkoutdir` to a directory where you want Flapjack to store all your
# git checkouts of modules that you are developing. The default is a "checkout"
# subdirectory of the workdir, but some might prefer a separate directory.

# checkoutdir = os.path.expanduser('~/checkout')

# If you want to use flatpak's per-user installation instead of the system-wide
# one, set this to True:

# user_installation = False

# -- RUNTIME SETUP ------------------------------------------------------------

# This specifies the SDK runtime you want to hack on. We assume that its
# manifest comes from a git checkout.

sdk_upstream = 'https://github.com/endlessm/endless-sdk-flatpak'
# sdk_upstream_branch = 'master'
sdk_id = 'com.endlessm.apps.Sdk'
# sdk_branch = 'master'

# The manifest is assumed to be in the root of the `sdk_upstream` git
# repository, and the filename is `sdk_id` plus `.json.in`. Customize that here
# if that's not the case.

# sdk_manifest_json = sdk_id + '.json'

# Flapjack will install the base SDK's repository as "flapjack-source", using
# a .flatpakrepo definition file. If you want to use a flatpak repo that you've
# already added, so that you don't have to download everything again, set
# `sdk_repo_name` here. The .flatpakrepo file will only be added if a flatpak
# repo called `sdk_repo_name` doesn't already exist.

# sdk_repo_name = 'eos-sdk'
sdk_repo_definition = \
    'http://endlessm.github.io/eos-knowledge-lib/eos-sdk.flatpakrepo'

# This is the name of the development runtime that you are producing.

dev_sdk_id = 'com.endlessm.appsdev.Sdk'

# -- DEVELOPMENT ENVIRONMENT --------------------------------------------------

# This is the list of modules that you want to be able to open and hack on.

modules = [
    'xapian-glib',
    'eos-metrics',
    'eos-sdk',
    'eos-shard',
    'basin',
    'emeus',
    'eos-knowledge-lib',
]

# Add any extra configuration options for the modules here, that are not
# present in the original manifest but you want to change for the development
# runtime, such as including debug features or documentation.

extra_module_config_opts = {
    'xapian-glib': ['--enable-gtk-doc'],
    'eos-metrics': ['--enable-gtk-doc'],
    'eos-sdk': ['--enable-gtk-doc', '--enable-js-doc'],
    'emeus': ['-Denable-gtk-doc=true'],
    'eos-knowledge-lib': ['--enable-js-doc'],
}

# Here you can specify a manifest for any extra developer tools you want to
# build into the development runtime.

# dev_tools_manifest = os.path.join(workdir, 'devtools.json')

# Extra flatpak permissions to give to the sandbox in which `flapjack test`
# runs modules' tests. For example, you might want to run graphical tests.

test_permissions = [
    '--socket=x11',
    '--socket=wayland',
]

# Extra flatpak permissions to give to the sandbox started by `flapjack run`
# and `flapjack shell`.

shell_permissions = test_permissions + [
    '--allow=devel',
    '--filesystem=home',
]
