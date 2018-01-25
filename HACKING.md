# Contributing #

We use PEP8 code style.

# Release checklist #

- [ ] Increment the version in `flapjack/__version__.py`, keep semver
      guidelines in mind.
- [ ] Add an entry for the new version in `debian/changelog`.
- [ ] Add release notes to `NEWS.md`.
- [ ] Make a commit.
- [ ] Tag the commit with `git tag -a Version_x.y.z`.
- [ ] In the tag description, copy the release notes.
- [ ] Push.
- [ ] Run `./setup.py publish`.
