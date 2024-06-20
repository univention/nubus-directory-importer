#!/bin/sh

python3 setup.py clean --all
rm -rf MANIFEST .coverage dist/* build/* *.egg-info .tox .eggs docs/.build/*
rm -rf .mypy_cache
rm -f */*.py?
find -name __pycache__ | xargs -iname rm -r name
