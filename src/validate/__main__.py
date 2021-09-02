
import sys
import json
from .validate import validateJson

"""Validate NVDAVersions file
Usage: python -m src.validate {pathToSchema} {pathToDataFile}
"""

pathToSchema = sys.argv[1]
pathToDataFile = sys.argv[2]
with open(pathToDataFile, "r") as jsonDataFile:
	jsonData = json.load(jsonDataFile)
validateJson(jsonData, pathToSchema)
