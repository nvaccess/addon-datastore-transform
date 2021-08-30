# transformAddonDataToViews
Code to transform data so it can be accessed in nvaccess/addon-store-submission:views

## Run tests
```sh
python -m nose -sv --traverse-namespace -w src/tests
```

# Run linting
```sh
python -m flake8 --config=flake8.ini
```

# Run transformation of addon data
```sh
cd src
python -m transform {nvdaVersionsPath} {inputPath} {outputPath} [logLevel]
```
