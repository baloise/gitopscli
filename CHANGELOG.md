# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


## [3.0.1] - 2020-04-09

### Added
- Improved error handling while reading `gitops.config.yaml`

### Changed
- Fixed bug in `sync-apps` that always added a `test-app`

## [3.0.0] - 2020-03-20

### Added
- Added `--verbose` arg to print stack traces in case of errors
- Automatic git provider detection. If `--git-provider-url` contains "github" or "bitbucket" the `--git-provider` arg is not needed anymore. Until now, `bitbucket` was used as default if `--git-provider` was missing.
- Improved error handling and log outputs

### Changed
- Throw an error if a key is not found in the YAML file for `deploy` and `create-preview` commands. Until now, the missing key was silently added.
- `--username` and `--pasword` are always required
- Read `.gitops.config.yaml` from the master branch for `delete-preview`
- The `--branch` arg of the `delete-preview` command now only refers to the app repo branch. The config repo changes are pushed to `master` by default or to a randomly created branch name if `--create_pr` is given.

### Removed
- Arg shortcuts (except `-v` verbose and `-h` help)
- The `requirements.txt` was removed in favor of requirements in `setup.py`. This allows installation with only `pip3 install .`
- The `--branch` arg was removed for commands `deploy` and `create-preview`. For `create-preview` the app repo branch is detected via the `--pr_id`. All changes in the config repo are pushed to `master` by default, or to a randomly created branch name if `--create_pr` is given.

## [2.1.0] - 2020-02-09

### Added
- New command `delete-preview`
- Added initial Changelog.md
