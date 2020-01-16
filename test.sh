#!/bin/bash

# Just a simple script for testing during dev.
# Should be replaced by proper tests...

# create test repo
rm -rf testrepo
mkdir testrepo
cd testrepo
git init
echo "a:" >> values.yaml
echo "  # comment" >> values.yaml
echo "  c: latest # comment" >> values.yaml
echo "  b: 1.0 # comment" >> values.yaml
git add .
git commit -m "intial"

# deploy changes
gitopscli deploy -r . -f values.yaml -b deployment -v "{a.c: foo, a.b: '1'}" 

# check repo changes
git log --graph --oneline --decorate --all 
git checkout deployment
git diff master
