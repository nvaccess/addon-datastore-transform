# transformAddonDataToViews
Code to transform data so it can be accessed in nvaccess/addon-store-submission:views

## Run tests
```sh
python -m nose -sv --traverse-namespace -w src/tests
```

## Run linting
```sh
python -m flake8 --config=flake8.ini
```

## NVDAVersions.json

This file serves as source of truth for the NVDA versions and NVDA API versions supported by the views transformation.

To validate this file, run the following:
```sh
python src/validate/validate.py NVDAVersions.json
```
