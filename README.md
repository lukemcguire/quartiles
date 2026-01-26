# quartiles

[![Release](https://img.shields.io/github/v/release/lukemcguire/quartiles)](https://img.shields.io/github/v/release/lukemcguire/quartiles)
[![Build status](https://img.shields.io/github/actions/workflow/status/lukemcguire/quartiles/main.yml?branch=main)](https://github.com/lukemcguire/quartiles/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/lukemcguire/quartiles/branch/main/graph/badge.svg)](https://codecov.io/gh/lukemcguire/quartiles)
[![Commit activity](https://img.shields.io/github/commit-activity/m/lukemcguire/quartiles)](https://img.shields.io/github/commit-activity/m/lukemcguire/quartiles)
[![License](https://img.shields.io/github/license/lukemcguire/quartiles)](https://img.shields.io/github/license/lukemcguire/quartiles)

My version of the Quartiles game from Apple News+.

- **Github repository**: <https://github.com/lukemcguire/quartiles/>
- **Documentation** <https://lukemcguire.github.io/quartiles/>

## Getting started with your project

First, create a repository on GitHub with the same name as this project, then:

```bash
git init -b main
make install
git add .
git commit -m "init commit"
# If pre-commit modifies files, add them and commit again:
git add . && git commit -m "init commit"
git remote add origin git@github.com:lukemcguire/quartiles.git
git push -u origin main
```

The `make install` command will:
- Create a virtual environment using uv
- Install all dependencies and generate `uv.lock`
- Install pre-commit hooks

**Note:** Pre-commit hooks run automatically on `git commit` and may modify files to fix formatting. If this happens, just add the changes again and recommit.

You are now ready to start development on your project!
The CI/CD pipeline will be triggered when you open a pull request, merge to main, or when you create a new release.

To finalize the set-up for publishing to PyPI, see [here](https://lukemcguire.github.io/cookiecutter-uv/features/publishing/#set-up-for-pypi).
For activating the automatic documentation with MkDocs, see [here](https://lukemcguire.github.io/cookiecutter-uv/features/mkdocs/#enabling-the-documentation-on-github).
To enable the code coverage reports, see [here](https://lukemcguire.github.io/cookiecutter-uv/features/codecov/).

## Releasing a new version



---

Repository initiated with [lukemcguire/cookiecutter-uv](https://github.com/lukemcguire/cookiecutter-uv).
