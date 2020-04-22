# Contributing

**Thank you for your interest in _GitOps CLI_. Your contributions are highly welcome.**

There are multiple ways of getting involved:

- [Report a bug](#report-a-bug) 
- [Suggest a feature](#suggest-a-feature) 
- [Contribute code](#contribute-code) 

Below are a few guidelines we would like you to follow.
If you need help, please reach out to us by opening an issue.

## Report a bug 
Reporting bugs is one of the best ways to contribute. Before creating a bug report, please check that an [issue](https://github.com/baloise/gitopscli/issues) reporting the same problem does not already exist. If there is such an issue, you may add your information as a comment.

To report a new bug you should open an issue that summarizes the bug and set the label to ![bug](https://img.shields.io/badge/-bug-d73a4a).

If you want to provide a fix along with your bug report: That is great! In this case please send us a pull request as described in section [Contribute code](#contribute-code).

## Suggest a feature
To request a new feature you should open an [issue](https://github.com/baloise/gitopscli/issues/new) and summarize the desired functionality and its use case. Set the issue label to ![enhancement](https://img.shields.io/badge/-enhancement-52d13e).  

## Contribute code
This is an outline of what the workflow for code contributions looks like

- Check the list of open [issues](https://github.com/baloise/gitopscli/issues). Either assign an existing issue to yourself, or 
create a new one that you would like work on and discuss your ideas and use cases. 

It is always best to discuss your plans beforehand, to ensure that your contribution is in line with our goals.

- Fork the repository on GitHub
- Create a topic branch from where you want to base your work. This is usually master.
- Open a new pull request, label it ![work in progress](https://img.shields.io/badge/-work%20in%20progress-fc9979) and outline what you will be contributing
- Make commits of logical units.
- Make sure you sign-off on your commits `git commit -s -m "feat(xyz): added feature xyz"`
- Write good commit messages (see below).
- Push your changes to a topic branch in your fork of the repository.
- As you push your changes, update the pull request with new information and tasks as you complete them
- Project maintainers might comment on your work as you progress
- When you are done, remove the ![work in progress](https://img.shields.io/badge/-work%20in%20progress-fc9979) label and ping the maintainers for a review
- Your pull request must receive a :thumbsup: from two [MAINTAINERS](https://github.com/baloise/gitopscli/blob/master/docs/CODEOWNERS)

Thanks for your contributions!

### Commit messages
We are using the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary) convention for our commit messages. This convention dovetails with [SemVer](https://semver.org/), by describing the features, fixes, and breaking changes made in commit messages.

When creating a pull request, its description should reference the corresponding issue id.

### Sign your work / Developer certificate of origin
All contributions (including pull requests) must agree to the Developer Certificate of Origin (DCO) version 1.1. This is exactly the same one created and used by the Linux kernel developers and posted on [http://developercertificate.org/](http://developercertificate.org/). This is a developer's certification that he or she has the right to submit the patch for inclusion into the project. Simply submitting a contribution implies this agreement, however, please include a `Signed-off-by` tag in every patch (this tag is a conventional way to confirm that you agree to the DCO) - you can automate this with a [Git hook](https://stackoverflow.com/questions/15015894/git-add-signed-off-by-line-using-format-signoff-not-working)

```
git commit -s -m "feat(xyz): added feature xyz"
```

**Have fun, and happy hacking!**
