# GitOps CLI

## Usage
```bash
gitopscli deploy -repo git@github.com:ora/repo.git \
                 -file namespace/values.yaml \
                 -branch deployment-xyz 
                 -values "{a.c: foo, a.b: '1'}" 
```

## Dev
Install via

```bash
make install
```

The use it normally like

```bash
gitopscli deploy --help
```