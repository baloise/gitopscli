# GitOps CLI

A command line interface to perform operations on GitOps managed infrastructure repositories.

![GitOps CLI Teaser](assets/images/teaser.png){: .center}

## Features
- Update YAML values in config repository to e.g. deploy an application
- Add pull request comments
- Create and delete preview environments in the config repository for a pull request in an app repository
- Update root config repository with all apps from child config repositories

## Git Provider Support
GitOps CLI supports the following Git providers:
- **GitHub** - Full API integration
- **GitLab** - Full API integration 
- **Bitbucket Server** - Full API integration
- **Azure DevOps** - Full API integration  (Note: the git provider URL must be with org name, e.g. `https://dev.azure.com/organisation` and the --organisation parameter must be the project name, e.g. `my-project`)