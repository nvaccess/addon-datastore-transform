# transformAddonDataToViews
This repository primarily exists to transform data from [nvaccess/addon-store-submission:master](https://github.com/nvaccess/addon-store-submission) to views located at [nvaccess/addon-store-submission:views](https://github.com/nvaccess/addon-store-submission/tree/views).

## Overview

For each version of NVDA, the meta-data of the most recent (the highest version number) of each Addon is automatically
added, based on the data in `addon-store-submission`.

## Setup
```sh
pip install -r requirements.txt
```

## Usage
```
python -m src.transform {nvdaVersionsPath} {inputPath} {outputPath} [logLevel]
```

### nvdaVersionsPath
A path to the NVDAVersions, see the schema: `src\validate\NVDAVersions_schema.json` and current values `NVDAVersions.json`.
This is an array of NVDA Versions, which include their NVDA API Version, and what API Version they are backwards compatible to.
This allows us to list which versions an addon is compatible for.

### inputPath
Expects a directory.

#### Input file structure
As this repo consumes data from `nvaccess/addon-store-submission`, see [nvaccess/addon-store-submission README layout](https://github.com/nvaccess/addon-store-submission/blob/master/README.md#layout).

#### Input file data
The expected input schema for each file can be found at [nvaccess/validateNvdaAddonMetadata](https://github.com/nvaccess/validateNvdaAddonMetadata/blob/main/_validate/addonVersion_schema.json).

### outputPath
Expects a directory.
- WARNING: Deletes all json data from the directory.
   - This is so new data can be loaded.

#### Output file structure
Given the directory, the following subdirectories and files are created:
- `/NVDA API Version/addon-1-ID/stable.json`
- `/NVDA API Version/addon-1-ID/beta.json`
- `/NVDA API Version/addon-2-ID/stable.json`
eg: `/2020.3/nvdaOCR/stable.json`

#### Output file data
Each addon file is the addon data taken from input that is the latest compatible version, with the given requirements `(NVDA API Version, addon-ID, stable|beta)`.
The transformed data file content will be the same as the input.
The contents for each addon file includes all the technical details required for NVDA to download, verify file integrity, and install.
It also contains the information necessary for a store entry.
Later, translated versions will become available.

#### Output notes
This structure simplifies the processing on the hosting (e.g. NV Access) server.
To fetch the latest add-ons for `<NVDA API Version X>`, the server can concatenate the appropriate JSON files that match a glob: `/<NVDA API Version X>/*/stable.json`.
Similarly, to fetch the latest version of an add-on with `<Addon-ID>` for `<NVDA API Version X>`. The server can return the data at `/<NVDA API Version X>/<addon-ID>/stable.json`.
Using the NV Access server as the endpoint for this is important in case the implementation has to change or be migrated away from GitHub for some reason.

## Run linting and tests
[Tox](https://tox.readthedocs.io/) configures the environment, runs the tests and linting.

```sh
tox
```

## Validating data files

Data files can be validated using the following script:
```sh
python -m src.validate {pathToSchema} {pathToDataFile}
```

### NVDAVersions.json

This file serves as source of truth for the NVDA versions and NVDA API versions supported by the views transformation.

To validate this file, run the following:
```sh
python -m src.validate src/validate/NVDAVersions_schema.json NVDAVersions.json
```
