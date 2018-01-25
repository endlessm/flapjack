Version 0.1.0
=============

- Added module-specific `extra_build_args`, `extra_make_args`,
  `extra_test_args`, and `extra_make_install_args` config keys with
  shell-style quoting.
- Added module-specific `[module_name.extra_env]` section where the
  config keys are interpreted as extra environment variables.
- Config keys are case-insensitive now.
- Allows shell-style quoting in the `extra_config_opts` config key.
- Made `flapjack open` print a warning when opening a module with a
  non-git source, with a suggestion of what to do.
- Now doesn't use rofiles when building, in order to accommodate
  modules that overwrite instead of replace files on install.
- Made `flapjack build` discard the build directories of successful
  builds.
- Fixed bugs around defaults for keys not specified in the config file.

Version 0.0.2
=============

- Now makes sure that the Locale extensions are completely installed,
  in order to avoid the dreaded "Locale only partially installed" error.

Version 0.0.1
=============

- Added `sdk_branch` config key to allow picking the branch of the
  SDK that you want to base your dev SDK on.
- Added `user_installation` config key to allow operating with
  `flatpak --user`.
- Added module-specific `url`, `extra_cflags`, `extra_cppflags`,
  `extra_cxxflags`, and `extra_ldflags` config keys to allow a bit more
  customization of a module's build.
- Switched the config file format to Python's "configparser" INI-style
  format.
- Made `flapjack update` keep going when failing to fetch one repo.
- Now installs the Debug extension of your dev SDK automatically.
- Fixed using a custom location for the checkout path.
- Fixed `flapjack update` trying to fetch a git repo with no remote.
- Fixed not having a `dev_tools_manifest` key in the config file.
- Fixed `flapjack build` when some SDK extensions aren't installed.

Version 0.0.0
=============

Initial release.