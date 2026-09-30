DEPLOY
======

Notes about deploying a new build.

- `hatch run testit`
- `hatch run lintit`
- `hatch run shapeit`
- Bump the version
  - `hatch version {major,minor,micro,etc.}`
- Update changelog
  - change unreleased to version
- Commit it
  - `git commit -m "Prepare for release." src/raceway/__version__.py CHANGELOG.rst`
- Tag repo with new version
  - `hatch run tagit`
- Build the distributions ( and run twine check )
  - `hatch run buildit`
- Relase it
  - `hatch run releaseit`
- Reset changelog
  - add unreleased back to top of changelog
- Reset to dev
  - `hatch version dev`
- Commit it
  - `git commit -m "Back to dev" src/raceway/__version__.py CHANGELOG.rst`

