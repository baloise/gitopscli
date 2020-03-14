# Getting started

The GitOps CLI provides several commands which can be used to perform typical operations on GitOps managed infrastructure repositories. You can print a help page listing all available commands with `gitopscli --help`:

```
usage: gitopscli [-h]
                 {deploy,sync-apps,add-pr-comment,create-preview,delete-preview}
                 ...

GitOps CLI

optional arguments:
  -h, --help            show this help message and exit

commands:
  {deploy,sync-apps,add-pr-comment,create-preview,delete-preview}
    deploy              Trigger a new deployment by changing YAML values
    sync-apps           Synchronize applications (= every directory) from apps
                        config repository to apps root config
    add-pr-comment      Create a comment on the pull request
    create-preview      Create a preview environment
    delete-preview      Delete a preview environment
```

A detailed description of the individual commands including some examples can be found in the [CLI Commands](/gitopscli/commands/add-pr-comment/) section.
