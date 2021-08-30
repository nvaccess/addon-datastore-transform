# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

"""
Runs the dataView generation system on test data.
Confirms the end result data is as expected.
Runs a number of specific checks for scenarios within the test data.
"""

import json
import glob
import os
from pathlib import Path
from src.tests.generateData import MockAddon
from src.transform.transform import emptyDirectory
from src.transform.datastructures import Addon, AddonVersion, NVDAVersion, VersionCompatibility
import src
from typing import Iterable
import subprocess
import unittest

TEST_DATASET_0_DIR = os.path.join(os.path.dirname(__file__), "test_data/input/addonSet0")
TEST_DATASET_1_DIR = os.path.join(os.path.dirname(__file__), "test_data/input/addonSet1")
TEST_DATASET_0_EXPECTED_DIR = os.path.join(os.path.dirname(__file__), "test_data/expected_results/addonSet0")
TEST_DATASET_1_EXPECTED_DIR = os.path.join(os.path.dirname(__file__), "test_data/expected_results/addonSet1")
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "test_data/output")
VIEWS_GLOB = "/**/**/*.json"


class _GenerateSystemTestData:
	testSet: int

	def __init__(self, testSet: int) -> None:
		self.testNVDAVersions = [
			VersionCompatibility(NVDAVersion(2020, 1), NVDAVersion(2020, 1), NVDAVersion(2020, 1)),
			VersionCompatibility(NVDAVersion(2020, 2), NVDAVersion(2020, 2), NVDAVersion(2020, 1)),
			VersionCompatibility(NVDAVersion(2020, 3), NVDAVersion(2020, 3), NVDAVersion(2020, 1)),
			VersionCompatibility(NVDAVersion(2020, 4), NVDAVersion(2020, 4), NVDAVersion(2020, 4)),
			VersionCompatibility(NVDAVersion(2021, 1), NVDAVersion(2021, 1), NVDAVersion(2021, 1)),
		]
		self.testSet = testSet
		if testSet == 0:
			self.inputDir = TEST_DATASET_0_DIR
			self.outputDir = TEST_DATASET_0_EXPECTED_DIR
		else:
			self.inputDir = TEST_DATASET_1_DIR
			self.outputDir = TEST_DATASET_1_EXPECTED_DIR
			self.testNVDAVersions.append(
				VersionCompatibility(NVDAVersion(2021, 2), NVDAVersion(2021, 2), NVDAVersion(2021, 1))
			)
		emptyDirectory(self.inputDir)
		emptyDirectory(self.outputDir)
		self.writeNVDAVersions()

	def generate_testData(self):
		self.test_addon_to_be_downgraded()
		self.test_addon_versions()
		self.test_stable_from_beta()
		self.test_addon_to_be_fully_removed()
		self.test_NVDAVersions()

	def write_mock_addon_to_files(self, addon: Addon, exceptedVersions: Iterable[NVDAVersion]):
		addonData = {
			"displayName": addon.name,
			"description": "",
			"homepage": f"https://example.com/{addon.name}",
			"publisher": "nvdaexamples",
			"minNVDAVersion": addon.minNVDAVersion.toJson(),
			"lastTestedVersion": addon.lastTestedVersion.toJson(),
			"channel": addon.channel,
			"URL": f"https://example.com/{addon.name}/{addon.version.toStr()}.nvda-addon",
			"sha256-comment": f"SHA for the {addon.name}.nvda-addon file",
			"sha256": "1234567BAC89FC24602245F4B8B750BCF2B72AFDF2DF54A0B07467FF4983F872",
			"sourceURL": f"https://example.com/{addon.name}",
			"license": "GPL v2",
			"licenseURL": "https://www.gnu.org/licenses/gpl-2.0.html"
		}
		addonWritePath = f"{self.inputDir}/{addon.name}"
		Path(addonWritePath).mkdir(parents=True, exist_ok=True)
		with open(f"{addonWritePath}/{addon.version.toStr()}.json", "w") as addonFile:
			json.dump(addonData, addonFile, indent=4)
		addonData["version"] = addon.version.toJson()
		for nvdaVersion in exceptedVersions:
			addonWritePath = f"{self.outputDir}/{nvdaVersion.toStr()}/{addon.name}"
			Path(addonWritePath).mkdir(parents=True, exist_ok=True)
			with open(f"{addonWritePath}/{addon.channel}.json", "w") as addonFile:
				json.dump(addonData, addonFile, indent=4)

	def writeNVDAVersions(self):
		Path(self.inputDir).mkdir(parents=True, exist_ok=True)
		with open(f"{self.inputDir}/NVDAVersions.json", "w") as NVDAVersionFile:
			nvdaVersionsJson = [{
				"NVDAVersion": version.nvdaVersion.toStr(),
				"apiVer": version.apiVer.toStr(),
				"backCompatTo": version.backCompatTo.toStr(),
			} for version in self.testNVDAVersions]
			json.dump(nvdaVersionsJson, NVDAVersionFile)

	def test_addon_to_be_fully_removed(self):
		"""Creates addon data for an addon to be fully removed in subsequent datasets"""
		if self.testSet != 0:
			return
		addon = MockAddon()
		addon.name = "fullyRemoved"
		addon.version = AddonVersion(0, 1)
		addon.minNVDAVersion = NVDAVersion(2020, 1)
		addon.lastTestedVersion = NVDAVersion(2021, 1)
		addon.channel = "stable"
		self.write_mock_addon_to_files(addon, [v.nvdaVersion for v in self.testNVDAVersions])

	def test_addon_to_be_downgraded(self):
		"""Creates addon data for an addon to be downgraded in subsequent datasets"""
		# stable version
		addon = MockAddon()
		addon.name = "downgraded"
		addon.version = AddonVersion(0, 9)
		addon.minNVDAVersion = NVDAVersion(2020, 1)
		addon.lastTestedVersion = NVDAVersion(2020, 4)
		addon.channel = "stable"
		exceptedStableVersions = [NVDAVersion(2020, 1), NVDAVersion(2020, 2)]
		if self.testSet == 1:
			exceptedStableVersions.extend((NVDAVersion(2020, 3), NVDAVersion(2020, 4)))
		self.write_mock_addon_to_files(addon, exceptedStableVersions)

		if self.testSet == 0:
			# version to be downgraded, removed in the second set
			addon = MockAddon()
			addon.name = "downgraded"
			addon.version = AddonVersion(1, 1, 1)
			addon.minNVDAVersion = NVDAVersion(2020, 3)
			addon.lastTestedVersion = NVDAVersion(2021, 1)
			addon.channel = "stable"
			self.write_mock_addon_to_files(addon, {NVDAVersion(2020, 3), NVDAVersion(2020, 4), NVDAVersion(2021, 1)})

	def test_addon_versions(self):
		"""Creates addon data to test the newest available addon version is used"""
		# legacy version, to remain unlisted
		addon = MockAddon()
		addon.name = "legacyOldNewAddon"
		addon.version = AddonVersion(1, 9)
		addon.minNVDAVersion = NVDAVersion(2020, 1)
		addon.lastTestedVersion = NVDAVersion(2020, 2)
		addon.channel = "stable"
		self.write_mock_addon_to_files(addon, set())

		# older version
		addon = MockAddon()
		addon.name = "legacyOldNewAddon"
		addon.version = AddonVersion(2, 1)
		addon.minNVDAVersion = NVDAVersion(2020, 1)
		addon.lastTestedVersion = NVDAVersion(2020, 4)
		addon.channel = "stable"
		self.write_mock_addon_to_files(addon, {NVDAVersion(2020, 1), NVDAVersion(2020, 2)})

		# newer version
		addon = MockAddon()
		addon.name = "legacyOldNewAddon"
		addon.version = AddonVersion(13, 0)
		addon.minNVDAVersion = NVDAVersion(2020, 3)
		addon.lastTestedVersion = NVDAVersion(2021, 1)
		addon.channel = "stable"
		expectedVersions = {NVDAVersion(2020, 3), NVDAVersion(2020, 4), NVDAVersion(2021, 1)}
		if self.testSet == 1:
			expectedVersions.add(NVDAVersion(2021, 2))
		self.write_mock_addon_to_files(addon, expectedVersions)

	def test_stable_from_beta(self):
		"""Generates a beta addon for the first set, and the equivalent stable addon for the second
		"""
		addon = MockAddon()
		addon.name = "betaToStable"
		addon.version = AddonVersion(1, 1)
		addon.minNVDAVersion = NVDAVersion(2020, 1)
		addon.lastTestedVersion = NVDAVersion(2020, 2)
		addon.channel = "beta" if self.testSet == 0 else "stable"
		self.write_mock_addon_to_files(addon, {NVDAVersion(2020, 1), NVDAVersion(2020, 2), NVDAVersion(2020, 3)})

	def test_NVDAVersions(self):
		"""Creates addon data to test that the newest addon is used across various NVDA versions"""
		# older NVDA
		addon = MockAddon()
		addon.name = "testNVDAVersions"
		addon.version = AddonVersion(1, 0)
		addon.minNVDAVersion = NVDAVersion(2020, 1)
		addon.lastTestedVersion = NVDAVersion(2020, 3)
		addon.channel = "stable"
		self.write_mock_addon_to_files(addon, {NVDAVersion(2020, 1)})

		# middle NVDA Versions
		addon = MockAddon()
		addon.name = "testNVDAVersions"
		addon.version = AddonVersion(1, 1)
		addon.minNVDAVersion = NVDAVersion(2020, 2)
		addon.lastTestedVersion = NVDAVersion(2020, 4)
		addon.channel = "stable"
		self.write_mock_addon_to_files(addon, {NVDAVersion(2020, 2)})

		# newer NVDA versions
		addon = MockAddon()
		addon.name = "testNVDAVersions"
		addon.version = AddonVersion(1, 2)
		addon.minNVDAVersion = NVDAVersion(2020, 3)
		addon.lastTestedVersion = NVDAVersion(2021, 1)
		addon.channel = "stable"
		expectedVersions = {NVDAVersion(2020, 3), NVDAVersion(2020, 4)}
		if self.testSet == 0:
			expectedVersions.add(NVDAVersion(2021, 1))
		self.write_mock_addon_to_files(addon, expectedVersions)

		if self.testSet == 1:
			addon = MockAddon()
			addon.name = "testNVDAVersions"
			addon.version = AddonVersion(1, 3)
			addon.minNVDAVersion = NVDAVersion(2021, 1)
			addon.lastTestedVersion = NVDAVersion(2021, 2)
			addon.channel = "stable"
			self.write_mock_addon_to_files(addon, (NVDAVersion(2021, 1), NVDAVersion(2021, 2)))


class TestTransformation(unittest.TestCase):
	@classmethod
	def _execute_transformation(cls, inputPath: str, outputPath: str = TEST_OUTPUT_DIR):
		cwd = os.getcwd()
		nvdaVersionsPath = f"{inputPath}/NVDAVersions.json"
		os.chdir(os.path.dirname(src.__file__))  # change the CWD so that we can run transform as a module
		process = subprocess.run(f"python -m transform {nvdaVersionsPath} {inputPath} {outputPath}", shell=True)
		process.check_returncode()
		os.chdir(cwd)

	@classmethod
	def setUpClass(cls) -> None:
		_GenerateSystemTestData(0).generate_testData()
		_GenerateSystemTestData(1).generate_testData()

	def setUp(self):
		"""
		Runs the transformation.
		"""
		for filename in glob.glob(TEST_OUTPUT_DIR + "/**", recursive=True):
			if os.path.isfile(filename):
				os.remove(filename)
		self._execute_transformation(TEST_DATASET_0_DIR)

	def _check_expected_addons_added(self, expectedResultsPath: str):
		"""
		Checks that all the data and files in expectedResultsPath match the test output directory.
		"""
		testOutputFiles = set(glob.glob(TEST_OUTPUT_DIR + VIEWS_GLOB))
		expectedFiles = set(glob.glob(expectedResultsPath + VIEWS_GLOB))
		testOutputFiles = set(f.lstrip(TEST_OUTPUT_DIR) for f in testOutputFiles)
		expectedFiles = set(f.lstrip(expectedResultsPath) for f in expectedFiles)
		self.assertEqual(testOutputFiles, expectedFiles)
		for outputFilename in testOutputFiles:
			with open(f"{TEST_OUTPUT_DIR}/{outputFilename}", "r") as outputFile:
				outputFileJson = json.load(outputFile)
			with open(f"{expectedResultsPath}/{outputFilename}", "r") as expectedFile:
				expectedResultsJson = json.load(expectedFile)
			self.assertDictEqual(expectedResultsJson, outputFileJson, msg=outputFilename)

	def test_expected_addons_added(self):
		"""
		Confirms the initial transformation was successful.
		"""
		self._check_expected_addons_added(TEST_DATASET_0_EXPECTED_DIR)

	def test_expected_addons_updated(self):
		"""
		Confirms that a subsequent transformation is successful, and the first transformation results are
		overwritten.
		"""
		self._check_expected_addons_added(TEST_DATASET_0_EXPECTED_DIR)
		self._execute_transformation(TEST_DATASET_1_DIR)
		self._check_expected_addons_added(TEST_DATASET_1_EXPECTED_DIR)
