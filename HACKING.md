# Contributing #

We use PEP8 code style.

# Release checklist #

- [ ] Increment the version in `flapjack/__version__.py`, keep semver
      guidelines in mind.
- [ ] Add an entry for the new version in `debian/changelog`.
- [ ] Make a commit.
- [ ] Tag the commit with `git tag -a Version_x.y.z`.
- [ ] In the tag description, put some release notes.
- [ ] Push.
- [ ] Run `./setup.py publish`.
