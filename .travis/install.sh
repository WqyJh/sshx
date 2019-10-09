#!/bin/bash

dep="pipenv"

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
    export PATH=/usr/local/opt/python/libexec/bin:$PATH
fi

pip install $dep
pipenv install --dev --system
python setup.py install
