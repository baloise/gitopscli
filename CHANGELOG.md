# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- The `--branch` arg of the `delete-preview` command now only refers to the app repo branch. The config repo changes are pushed to `master` by default or to a randomly created branch name if `--create_pr` is given.

### Removed
- The `--branch` arg was removed for commands `deploy` and `create-preview`. For `create-preview` the app repo branch is detected via the `--pr_id`. All changes in the config repo are pushed to `master` by default, or to a randomly created branch name if `--create_pr` is given.

## [2.1.0] - 2020-02-09
### Added
- New command `delete-preview`
- Added initial Changelog.md
- Added `--verbose` arg
- Improved git error handling
- Improved yaml update error handling
### Removed
- arg shortcuts (except -v verbose and -h help)