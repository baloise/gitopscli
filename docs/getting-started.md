# Getting started

The GitOps CLI provides several commands which can be used to perform typical operations on GitOps managed infrastructure repositories. You can print a help page listing all available commands with `gitopscli --help`:

```
usage: gitopscli [-h]
                 {deploy,sync-apps,add-pr-comment,create-preview,create-pr-preview,delete-preview,delete-pr-preview,version}
                 ...

GitOps CLI

options:
  -h, --help            show this help message and exit

commands:
  {deploy,sync-apps,add-pr-comment,create-preview,create-pr-preview,delete-preview,delete-pr-preview,version}
    deploy              Trigger a new deployment by changing YAML values
    sync-apps           Synchronize applications (= every directory) from apps
                        config repository to apps root config
    add-pr-comment      Create a comment on the pull request
    create-preview      Create a preview environment
    create-pr-preview   Create a preview environment for a pull request
    delete-preview      Delete a preview environment
    delete-pr-preview   Delete a preview environment for a pull request
    version             Show the GitOps CLI version information
```

A detailed description of the individual commands including some examples can be found in the [CLI Commands](/gitopscli/commands/add-pr-comment/) section.
