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
from typing import Iterable
import subprocess
import unittest

log = getLogger()
VIEWS_GLOB = "/**/**/*.json"


class DATA_DIR(str, Enum):
	_root = os.path.join(os.path.dirname(__file__), "test_data")
	INPUT = os.path.join(_root, "input")
	OUTPUT = os.path.join(_root, "output")
	EXPECTED_RES = os.path.join(_root, "expected_results")
	nvdaAPIVersionsPath = os.path.join(INPUT, "nvdaAPIVersions.json")


class _TestDataGenerator:
	_test_nvdaAPIVersions = [
		VersionCompatibility(MajorMinorPatch(2020, 1), MajorMinorPatch(2020, 1)),
		VersionCompatibility(MajorMinorPatch(2020, 2), MajorMinorPatch(2020, 1)),
		VersionCompatibility(MajorMinorPatch(2021, 1), MajorMinorPatch(2021, 1)),
	]

	@staticmethod
	def write_mock_addon_to_files(addon: Addon, exceptedVersions: Iterable[MajorMinorPatch]):
		"""Write mock addon data to the input and expected results directories."""
		addonData = {
			"addonId": addon.addonId,
			"addonVersionNumber": addon.addonVersion._asdict(),
			"minNVDAVersion": addon.minNvdaAPIVersion._asdict(),
			"lastTestedVersion": addon.lastTestedVersion._asdict(),
			"channel": addon.channel,
		}
		addonData["minNVDAVersion"]["patch"] = 0
		addonData["lastTestedVersion"]["patch"] = 0
		addonWritePath = os.path.join(DATA_DIR.INPUT, addon.addonId)
		Path(addonWritePath).mkdir(parents=True, exist_ok=True)
		with open(f"{addonWritePath}/{str(addon.addonVersion)}.json", "w") as addonFile:
			json.dump(addonData, addonFile, indent=4)
		for nvdaAPIVersion in exceptedVersions:
			addonWritePath = os.path.join(DATA_DIR.EXPECTED_RES, str(nvdaAPIVersion), addon.addonId)
			Path(addonWritePath).mkdir(parents=True, exist_ok=True)
			with open(f"{addonWritePath}/{addon.channel}.json", "w") as addonFile:
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

	@staticmethod
	def generate_addon():
		"""Creates addon data for a lone addon which works of all NVDA API versions"""
		availableApiVersions = [v.apiVer for v in _TestDataGenerator._test_nvdaAPIVersions]
		addon = MockAddon()
		addon.addonId = "exampleAddon"
		addon.addonVersion = MajorMinorPatch(0, 1)
		addon.minNvdaAPIVersion = min(availableApiVersions)
		addon.lastTestedVersion = max(availableApiVersions)
		addon.channel = "stable"
		_TestDataGenerator.write_mock_addon_to_files(addon, availableApiVersions)

	@staticmethod
	def generate_addon_with_versions():
		"""Creates addon data to test the paths are correct across NVDA API Versions"""
		# oldest version, to remain unlisted
		addon = MockAddon()
		addon.addonId = "multipleVersionsAddon"
		addon.channel = "stable"
		addon.addonVersion = MajorMinorPatch(2, 1)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 1)
		addon.lastTestedVersion = MajorMinorPatch(2020, 4)
		_TestDataGenerator.write_mock_addon_to_files(addon, {MajorMinorPatch(2020, 1), MajorMinorPatch(2020, 2)})

		# newer version
		addon = deepcopy(addon)
		addon.addonVersion = MajorMinorPatch(13, 0)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 3)
		addon.lastTestedVersion = MajorMinorPatch(2021, 1)
		_TestDataGenerator.write_mock_addon_to_files(addon, {MajorMinorPatch(2021, 1)})


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

	def _check_expected_addons_added(self):
		"""
		Checks that all the data and files in expectedResultsPath match the test output directory.
		"""
		testOutputFiles = set(glob.glob(DATA_DIR.OUTPUT + VIEWS_GLOB))
		expectedFiles = set(glob.glob(DATA_DIR.EXPECTED_RES + VIEWS_GLOB))
		testOutputFiles = set(f.lstrip(DATA_DIR.OUTPUT) for f in testOutputFiles)
		expectedFiles = set(f.lstrip(DATA_DIR.EXPECTED_RES) for f in expectedFiles)
		self.assertEqual(testOutputFiles, expectedFiles)
		for outputFilename in testOutputFiles:
			with open(f"{DATA_DIR.OUTPUT}/{outputFilename}", "r") as outputFile:
				outputFileJson = json.load(outputFile)
			with open(f"{DATA_DIR.EXPECTED_RES}/{outputFilename}", "r") as expectedFile:
				expectedResultsJson = json.load(expectedFile)
			self.assertDictEqual(expectedResultsJson, outputFileJson, msg=outputFilename)

	def _test_transform(self) -> None:
		"""Generates NVDA API versions so that transform can run.
		"""
		_TestDataGenerator.write_nvdaAPIVersions()
		subprocess.run(
			f"python -m src.transform {DATA_DIR.nvdaAPIVersionsPath} {DATA_DIR.INPUT} {DATA_DIR.OUTPUT}",
			shell=True
		).check_returncode()  # Raise CalledProcessError if the exit code is non-zero.

	def test_transform_empty(self):
		"""Confirms an empty transformation is successful
		"""
		self._test_transform()

	def test_transform_successfully(self):
		"""Confirms an transformation of a single addon is successful
		"""
		_TestDataGenerator.generate_addon()
		self._test_transform()

	def test_throw_error_on_nonempty_output_folder(self):
		"""Confirms using an existing output directory throws an error
		"""
		# Make the folder before transform
		Path(DATA_DIR.OUTPUT.value).mkdir(parents=True, exist_ok=True)
		
		with self.assertRaises(subprocess.CalledProcessError):
			self._test_transform()

	def test_output_file_structure_matches_expected(self):
		"""Confirms that a successful transform of multiple addons
		is written as expected.
		"""
		_TestDataGenerator.generate_addon()
		_TestDataGenerator.generate_addon_with_versions()
		self._test_transform()
		self._check_expected_addons_added()
