#!/bin/sh

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <version>"
  exit 1
fi

sed -i "s/^__version__.*$/__version__ = '$1'/" sshx/__init__.py

sed -i "s/^version.*$/version = '$1'/" doc/source/conf.py

git add -A
git commit -m "Bump version to $1"
