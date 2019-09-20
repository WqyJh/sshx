#!/bin/bash

dep="pipenv"

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
    brew upgrade python
    pip3 install $dep
    pipenv install --dev --system
    python3 setup.py install
else
    pip install $dep
    pipenv install --dev --system
    python setup.py install
fi 
