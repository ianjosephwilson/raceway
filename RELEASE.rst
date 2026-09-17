DEPLOY
======

Notes about deploying a new build.

- `hatch run testit`
- `hatch run lintit`
- `hatch run shapeit`
- Bump the version
  - `hatch version {major,minor,etc.}`
- Update changelog
  - add version below unreleased and make sure unreleased still empty.
- Commit it
  - `git commit -m "Prepare for release." src/raceway/__version__.py CHANGELOG.rst`
- Tag repo with new version
  - `hatch run tagit`
- Build the distributions ( and run twine check )
  - `hatch run buildit`
- Relase it
  - `hatch run releaseit`


