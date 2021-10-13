# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

"""
Runs the dataView generation system on test data.
Confirms the end result data is as expected.
Creates a number of specific scenarios for running the transformation.
"""

from copy import deepcopy
from enum import Enum
import json
import glob
from logging import getLogger
import os
from pathlib import Path
import shutil
from src.tests.generateData import MockAddon
from src.transform.datastructures import Addon, MajorMinorPatch, VersionCompatibility
import subprocess
import unittest

log = getLogger()


class DATA_DIR(str, Enum):
	_root = os.path.join(os.path.dirname(__file__), "test_data")
	INPUT = os.path.join(_root, "input")
	OUTPUT = os.path.join(_root, "output")
	nvdaAPIVersionsPath = os.path.join(INPUT, "nvdaAPIVersions.json")


class _TestDataGenerator:
	_test_nvdaAPIVersions = [
		VersionCompatibility(MajorMinorPatch(2020, 1), MajorMinorPatch(2020, 1)),
		VersionCompatibility(MajorMinorPatch(2020, 2), MajorMinorPatch(2020, 1)),
		VersionCompatibility(MajorMinorPatch(2021, 1), MajorMinorPatch(2021, 1)),
	]

	@staticmethod
	def write_mock_addon_to_input_dir(addon: Addon):
		"""Write mock addon data to the input directory."""
		addonData = {
			"addonId": addon.addonId,
			"addonVersionNumber": addon.addonVersion._asdict(),
			"minNVDAVersion": addon.minNvdaAPIVersion._asdict(),
			"lastTestedVersion": addon.lastTestedVersion._asdict(),
			"channel": addon.channel,
		}
		addonWritePath = os.path.join(DATA_DIR.INPUT, addon.addonId)
		Path(addonWritePath).mkdir(parents=True, exist_ok=True)
		with open(f"{addonWritePath}/{str(addon.addonVersion)}.json", "w") as addonFile:
			json.dump(addonData, addonFile, indent=4)

	@staticmethod
	def write_nvdaAPIVersions():
		"""Write mock NVDA API Versions data to the input."""
		Path(DATA_DIR.INPUT.value).mkdir(parents=True, exist_ok=True)
		nvdaAPIVersionsJson = [{
			"description": str(version.apiVer),
			"apiVer": version.apiVer._asdict(),
			"backCompatTo": version.backCompatTo._asdict(),
		} for version in _TestDataGenerator._test_nvdaAPIVersions]
		with open(DATA_DIR.nvdaAPIVersionsPath.value, "w") as nvdaAPIVersionFile:
			json.dump(nvdaAPIVersionsJson, nvdaAPIVersionFile)


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
		"""Generates NVDA API versions so that transform can run.
		Runs the transformation and raises a CalledProcessError on failure.
		"""
		_TestDataGenerator.write_nvdaAPIVersions()
		transformProcess = subprocess.run(
			f"python -m src.transform {DATA_DIR.nvdaAPIVersionsPath} {DATA_DIR.INPUT} {DATA_DIR.OUTPUT}",
			shell=True,
			stderr=subprocess.PIPE
		)
		transformProcess.check_returncode()  # Raise CalledProcessError if the exit code is non-zero.
		return transformProcess

	def test_transform_empty(self):
		"""Confirms an empty transformation is successful
		"""
		self.runTransformation()

	def test_transform_successfully(self):
		"""Confirms a transformation of a single addon runs successfully
		"""
		availableApiVersions = [v.apiVer for v in _TestDataGenerator._test_nvdaAPIVersions]
		addon = MockAddon()
		addon.addonId = "exampleAddon"
		addon.addonVersion = MajorMinorPatch(0, 1)
		addon.minNvdaAPIVersion = min(availableApiVersions)
		addon.lastTestedVersion = max(availableApiVersions)
		addon.channel = "stable"
		_TestDataGenerator.write_mock_addon_to_input_dir(addon)

		self.runTransformation()

	def test_throw_error_on_nonempty_output_folder(self):
		"""Confirms using an existing output directory throws an error
		"""
		# Make the folder before transform
		Path(DATA_DIR.OUTPUT.value).mkdir(parents=True, exist_ok=True)
		
		with self.assertRaises(subprocess.CalledProcessError) as transformError:
			self.runTransformation()
		doubleEscapedDir = DATA_DIR.OUTPUT.replace('\\', '\\\\')  # stderr escapes all the backslashes twice
		self.assertIn(
			"FileExistsError: [WinError 183] Cannot create a file when that file already exists: "
			f"'{doubleEscapedDir}'",
			transformError.exception.stderr.decode("utf-8")
		)

	def _assertAddonDataWritten(self, expectedPathToAddon: str, expectedAddonVersion: MajorMinorPatch):
		"""Confirms that an addon is written to a path and has an expected version."""
		self.assertTrue(Path(expectedPathToAddon).exists())
		with open(expectedPathToAddon, "r") as expectedAddon:
			addonData = json.load(expectedAddon)
		self.assertDictEqual(addonData["addonVersionNumber"], expectedAddonVersion._asdict())

	def test_output_file_structure_matches_expected(self):
		"""Confirms that a successful transform of multiple addons is written as expected."""
		# older version
		addon = MockAddon()
		addon.addonId = "multipleVersionsAddon"
		addon.channel = "stable"
		addon.addonVersion = MajorMinorPatch(2, 1)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 1)
		addon.lastTestedVersion = MajorMinorPatch(2020, 2)
		_TestDataGenerator.write_mock_addon_to_input_dir(addon)

		# newer version
		addon = deepcopy(addon)
		addon.addonVersion = MajorMinorPatch(13, 0)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 2)
		addon.lastTestedVersion = MajorMinorPatch(2021, 1)
		_TestDataGenerator.write_mock_addon_to_input_dir(addon)

		self.runTransformation()

		self.assertEqual(len(glob.glob(f"{DATA_DIR.OUTPUT}/**/**.json", recursive=True)), 3)
		self._assertAddonDataWritten(
			os.path.join(DATA_DIR.OUTPUT, '2020.1.0', addon.addonId, 'stable.json'),
			MajorMinorPatch(2, 1)
		)
		self._assertAddonDataWritten(
			os.path.join(DATA_DIR.OUTPUT, '2020.2.0', addon.addonId, 'stable.json'),
			MajorMinorPatch(13, 0)
		)
		self._assertAddonDataWritten(
			os.path.join(DATA_DIR.OUTPUT, '2021.1.0', addon.addonId, 'stable.json'),
			MajorMinorPatch(13, 0)
		)
