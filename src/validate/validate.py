# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import os
import tempfile
import typing


JSON_INPUT_SCHEMA = os.path.join(os.path.dirname(__file__), "addonInput_schema.json")
JSON_VIEW_SCHEMA = os.path.join(os.path.dirname(__file__), "addonView_schema.json")
JSON_VERSION_SCHEMA = os.path.join(os.path.dirname(__file__), "NVDAVersions_schema.json")
TEMP_DIR = tempfile.gettempdir()

JsonObjT = typing.Dict[str, typing.Any]


def validateJson(data: JsonObjT, schemaPath: str) -> None:
	""" Ensure that the loaded metadata conforms to the schema.
	Raise error if not.
	"""
	with open(schemaPath) as f:
		schema = json.load(f)
	try:
		validate(instance=data, schema=schema)
	except ValidationError as err:
		raise err
