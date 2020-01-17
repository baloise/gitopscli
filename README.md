# GitOps CLI
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

## Usage
```bash
gitopscli deploy \
--repo git@github.com:ora/repo.git \
--file namespace/values.yaml \
--branch deployment-xyz \
--values "{a.c: foo, a.b: '1'}" 
```
### Basic Auth
To use Basic Auth when HTTP(S) is used, simply add the arguments
```bash
gitopscli deploy \
[...]
--username $GIT_USERNAME
--password $GIT_PASSWORD
```

### Usage with Docker
```bash
docker run --rm -it gitopscli deploy \
--repo git@github.com:ora/repo.git \
--file namespace/values.yaml \
--branch deployment-xyz \
--values "{a.c: foo, a.b: '1'}" 
```

## Dev
Install via

```bash
make install
```

Then use it normally like

```bash
gitopscli deploy --help
```
