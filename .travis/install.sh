#!/bin/bash

dep="codecov mock twine"

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then

    # Install some custom requirements on OS X
    # e.g. brew install pyenv-virtualenv

    case "${PY}" in
        py27)
            brew install python@2
            brew link --overwrite python@2
            pip install $dep
            python setup.py install
            ;;
        py36)
            brew upgrade python
            pip3 install $dep
            python3 setup.py install
            ;;
    esac
else
    pip install $dep
    python setup.py install
fi 
