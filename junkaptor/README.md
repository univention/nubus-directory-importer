# junkaptor - Python module for sanitizing data

-- Garbage in, sanitized data out...  --

This module package allows to sanitize data records provided as key-values
dictionaries, allowing attribute mapping etc.

Mainly this is used in meta-directory connectors.

# Dependencies

Only Python 3.6+ and its standard library.

# Installation

## From PyPI

```
pip install junkaptor
```

## Debian package

You can build a Debian package by using setuptools helper
[stdeb](https://github.com/astraw/stdeb). A custom configuration
file _stdeb.cfg_ is provided.

See repo
[container-stdeb](https://code.stroeder.com/pymod/container-stdeb)
for easy containerized builds.

# Configuration parameters

The following configuration paramaters can be optionally provided to
configure some transformation steps applied in same the order the
parameters are described herein:

## decompose_attrs

## recode_attrs

## remove_values

## replace_values

## sanitizer

## rename_attrs

## fallback_attrs

## fixed_attrs

## remove_attrs

## compose_attrs

## single_val_attrs

## name_suffix
