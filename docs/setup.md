# Setup

Currently there are two different ways to setup and use the GitOps CLI.

## Docker

The official GitOps CLI Docker image comes with all dependencies pre-installed and ready-to-use. Pull it with:
```bash
docker pull baloiseincubator/gitopscli
```
Start the CLI and the print the help page with:
```bash
docker run --rm -it baloiseincubator/gitopscli --help
```

## From Source

Clone the repository and install the GitOps CLI on your machine:
```bash
git clone https://github.com/baloise/gitopscli.git
pip3 install gitopscli/
```
You can now use it from the command line:
```bash
gitopscli --help
```
If you don't need the CLI anymore, you can uninstall it with
```bash
pip3 uninstall gitopscli
```