# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

"""
Runs the dataView generation system on test data.
Creates a number of specific scenarios for running the transformation.
"""

from enum import Enum
import json
import glob
from logging import getLogger
import os
from pathlib import Path
import re
import shutil
from typing import Iterator, Tuple
from src.transform.datastructures import MajorMinorPatch
import subprocess
import unittest

log = getLogger()

versionNumRegex = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")


class DATA_DIR(str, Enum):
	_root = os.path.join(os.path.dirname(__file__), "test_data")
	INPUT = os.path.join(_root, "input")
	OUTPUT = os.path.join(_root, "output")
	nvdaAPIVersionsPath = os.path.join(INPUT, "nvdaAPIVersions.json")


def addonJson(path: str, channel: str, *, required: str, tested: str) -> str:
	"""
	path should be of the form: `addonName/addonVersionString.json`, eg `nvdaOcr/13.1.0.json`
	All version strings should be of the form major.minor.patch.
	
	required is the minNVDAVersion as a version string
	tested is the lastTestedVersion as a version string
	"""
	pathRegex = re.compile(r"^(?P<addonId>[A-z0-9]+)/(?P<version>[0-9]+\.[0-9]+\.[0-9]+)\.json$")
	addonId = pathRegex.match(path).group('addonId')
	addonVersionStr = pathRegex.match(path).group('version')

	addonVersion = versionNumRegex.match(addonVersionStr)
	minVersion = versionNumRegex.match(required)
	testedVersion = versionNumRegex.match(tested)

	return path, f'''
	{{
		"addonId": "{addonId}",
		"channel": "{channel}",
		"addonVersionNumber": {{
			"major": {addonVersion.group(1)},
			"minor": {addonVersion.group(2)},
			"patch": {addonVersion.group(3)}
		}},
		"minNVDAVersion": {{
			"major": {minVersion.group(1)},
			"minor": {minVersion.group(2)},
			"patch": {minVersion.group(3)}
		}},
		"lastTestedVersion": {{
			"major": {testedVersion.group(1)},
			"minor": {testedVersion.group(2)},
			"patch": {testedVersion.group(3)}
		}}
	}}\n'''


def write_addons(*addons: Tuple[str, str]):
	"""Write mock addon data to the input directory.
	Arguments should be tuples of the form (path, addonDataBlob)"""
	for path, addonDataBlob in addons:
		addonWritePath = os.path.join(DATA_DIR.INPUT, path)
		Path(os.path.dirname(addonWritePath)).mkdir(parents=True, exist_ok=True)
		with open(addonWritePath, "w") as addonFile:
			addonFile.write(addonDataBlob)


def nvdaAPIVersionsJson(apiVersion: str, *, backCompatTo: str) -> Iterator[str]:
	apiVersion = versionNumRegex.match(apiVersion)
	backCompactTo = versionNumRegex.match(backCompatTo)
	return f'''
	{{
		"description": "{apiVersion}",
		"apiVer": {{
			"major": {apiVersion.group(1)},
			"minor": {apiVersion.group(2)},
			"patch": {apiVersion.group(3)}
		}},
		"backCompatTo": {{
			"major": {backCompactTo.group(1)},
			"minor": {backCompactTo.group(2)},
			"patch": {backCompactTo.group(3)}
		}}
	}}
	'''


def write_nvdaAPIVersions(*nvdaAPIVersionsBlobs: str):
	"""Write mock NVDA API Versions json blobs to the input nvdaAPIVersions json file."""
	Path(DATA_DIR.INPUT.value).mkdir(parents=True, exist_ok=True)
	with open(DATA_DIR.nvdaAPIVersionsPath.value, "w") as nvdaAPIVersionFile:
		nvdaAPIVersionFile.write("[\n" + ',\n'.join(nvdaAPIVersionsBlobs) + "\n]")


class TestTransformation(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		"""Empty the test data before the start of tests"""
		if Path(DATA_DIR._root.value).exists():
			shutil.rmtree(DATA_DIR._root.value)

	def tearDown(self):
		"""Empty the test data after each test"""
		if Path(DATA_DIR._root.value).exists():
			shutil.rmtree(DATA_DIR._root.value)

	def runTransformation(self) -> subprocess.CompletedProcess:
		"""
		Runs the transformation and raises a CalledProcessError on failure.
		"""
		transformProcess = subprocess.run(
			f"python -m src.transform {DATA_DIR.nvdaAPIVersionsPath} {DATA_DIR.INPUT} {DATA_DIR.OUTPUT}",
			shell=True,
			stderr=subprocess.PIPE  # debugging note: comment this out to log stderr from the test process
		)
		transformProcess.check_returncode()  # Raise CalledProcessError if the exit code is non-zero.
		return transformProcess

	def test_transform_empty(self):
		"""Confirms an empty transformation exits with a zero exit code (successful).
		"""
		write_nvdaAPIVersions()
		self.runTransformation()

	def test_transform_successfully(self):
		"""Confirms a transformation of a single addon exits with a zero exit code (successful).
		"""
		write_nvdaAPIVersions(nvdaAPIVersionsJson("2021.1.0", backCompatTo="2021.1.0"))
		write_addons(addonJson('foo/0.1.1.json', "stable", required="2021.1.0", tested="2021.1.0"))
		self.runTransformation()

	def test_throw_error_on_nonempty_output_folder(self):
		"""Confirms using an existing output directory throws an error
		"""
		# Make the folder before transform
		Path(DATA_DIR.OUTPUT.value).mkdir(parents=True, exist_ok=True)
		
		with self.assertRaises(subprocess.CalledProcessError) as transformError:
			write_nvdaAPIVersions()
			self.runTransformation()
		doubleEscapedDir = DATA_DIR.OUTPUT.replace('\\', '\\\\')  # stderr escapes all the backslashes twice
		self.assertIn(
			"FileExistsError: [WinError 183] Cannot create a file when that file already exists: "
			f"'{doubleEscapedDir}'",
			transformError.exception.stderr.decode("utf-8")
		)

	def _assertAddonDataWritten(self, expectedPathToAddon: str, expectedAddonVersionStr: str):
		"""Confirms that an addon is written to a path and the file contains an expected version."""
		fullPathToAddon = os.path.join(DATA_DIR.OUTPUT, expectedPathToAddon)
		self.assertTrue(Path(fullPathToAddon).exists())
		with open(fullPathToAddon, "r") as expectedAddonFile:
			addonData = json.load(expectedAddonFile)
		addonVersion = MajorMinorPatch(**addonData["addonVersionNumber"])
		self.assertEqual(expectedAddonVersionStr, str(addonVersion))

	def test_output_file_structure_matches_expected(self):
		"""Confirms that a transform of multiple addon versions is written as expected."""
		write_nvdaAPIVersions(
			nvdaAPIVersionsJson("2020.1.0", backCompatTo="2020.1.0"),
			nvdaAPIVersionsJson("2020.2.0", backCompatTo="2020.2.0"),
			nvdaAPIVersionsJson("2021.1.0", backCompatTo="2021.1.0"),
		)
		write_addons(
			addonJson("testAddon/2.1.0.json", "stable", required="2020.1.0", tested="2020.2.0"),
			addonJson("testAddon/13.0.0.json", "stable", required="2020.2.0", tested="2021.1.0"),
		)
		self.runTransformation()

		self.assertEqual(len(glob.glob(f"{DATA_DIR.OUTPUT}/**/**.json", recursive=True)), 3)
		self._assertAddonDataWritten('2020.1.0/testAddon/stable.json', '2.1.0')
		self._assertAddonDataWritten('2020.2.0/testAddon/stable.json', '13.0.0')
		self._assertAddonDataWritten('2021.1.0/testAddon/stable.json', '13.0.0')
