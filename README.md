# transformAddonDataToViews
Code to transform data so it can be accessed in nvaccess/addon-store-submission:views

## Setup
```sh
pip install -r requirements.txt
```

## Run linting and tests
[Tox](https://tox.readthedocs.io/) configures the environment, runs the tests and linting.

```sh
tox
```

## NVDAVersions.json

This file serves as source of truth for the NVDA versions and NVDA API versions supported by the views transformation.

To validate this file, run the following:
```sh
python src/validate/validate.py NVDAVersions.json
```
