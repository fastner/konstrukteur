#!/usr/bin/env bash

cd `dirname $0`/..
version=`python3 -c "import konstrukteur; print(konstrukteur.__version__)"`

git tag -d $version
git tag -a $version -m "Release of version $version"

git push origin :$version
git push origin $version