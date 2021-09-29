# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

"""
Runs the dataView generation system on test data.
Confirms the end result data is as expected.
Creates a number of specific scenarios for the test data.
"""

from dataclasses import dataclass
import json
import glob
from logging import getLogger
import os
from pathlib import Path
import shutil
from src.tests.generateData import MockAddon
from src.transform.datastructures import Addon, MajorMinorPatch, VersionCompatibility
from typing import Iterable, Tuple
import subprocess
import unittest

TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "test_data/output")
VIEWS_GLOB = "/**/**/*.json"

log = getLogger()


@dataclass
class TestSet:
	id: int
	inputDir: str
	outputDir: str


class _GenerateSystemTestData:
	"""
	A class which generates system test data for a given testing set given.
	"""
	testSet: TestSet

	def __init__(self, testSet: TestSet) -> None:
		self.testSet = testSet
		self._test_nvdaAPIVersions = [
			VersionCompatibility(MajorMinorPatch(2020, 1), MajorMinorPatch(2020, 1)),
			VersionCompatibility(MajorMinorPatch(2020, 2), MajorMinorPatch(2020, 1)),
			VersionCompatibility(MajorMinorPatch(2020, 3), MajorMinorPatch(2020, 1)),
			VersionCompatibility(MajorMinorPatch(2020, 4), MajorMinorPatch(2020, 4)),
			VersionCompatibility(MajorMinorPatch(2021, 1), MajorMinorPatch(2021, 1)),
		]
		if self.testSet.id == 1:
			self._test_nvdaAPIVersions.append(
				VersionCompatibility(MajorMinorPatch(2021, 2), MajorMinorPatch(2021, 1))
			)
		if Path(self.testSet.inputDir).exists():
			shutil.rmtree(self.testSet.inputDir)
		if Path(self.testSet.outputDir).exists():
			shutil.rmtree(self.testSet.outputDir)
		self.write_nvdaAPIVersions()

	def generate_testData(self):
		"""
		Generates system test data.
		"""
		self.test_addon_to_be_downgraded()
		self.test_addon_versions()
		self.test_stable_from_beta()
		self.test_addon_to_be_fully_removed()
		self.test_nvdaAPIVersions()

	def write_mock_addon_to_files(self, addon: Addon, exceptedVersions: Iterable[MajorMinorPatch]):
		addonData = {
			"addonId": addon.addonId,
			"addonVersionNumber": addon.addonVersion._asdict(),
			"minNVDAVersion": addon.minNvdaAPIVersion._asdict(),
			"lastTestedVersion": addon.lastTestedVersion._asdict(),
			"channel": addon.channel,
		}
		if addonData["minNVDAVersion"]["patch"] is False:
			addonData["minNVDAVersion"]["patch"] = 0
		if addonData["lastTestedVersion"]["patch"] is False:
			addonData["lastTestedVersion"]["patch"] = 0
		addonWritePath = f"{self.testSet.inputDir}/{addon.addonId}"
		Path(addonWritePath).mkdir(parents=True, exist_ok=True)
		with open(f"{addonWritePath}/{str(addon.addonVersion)}.json", "w") as addonFile:
			json.dump(addonData, addonFile, indent=4)
		for nvdaAPIVersion in exceptedVersions:
			addonWritePath = f"{self.testSet.outputDir}/{str(nvdaAPIVersion)}/{addon.addonId}"
			Path(addonWritePath).mkdir(parents=True, exist_ok=True)
			with open(f"{addonWritePath}/{addon.channel}.json", "w") as addonFile:
				json.dump(addonData, addonFile, indent=4)

	def write_nvdaAPIVersions(self):
		Path(self.testSet.inputDir).mkdir(parents=True, exist_ok=True)
		with open(f"{self.testSet.inputDir}/nvdaAPIVersions.json", "w") as nvdaAPIVersionFile:
			nvdaAPIVersionsJson = [{
				"description": str(version.apiVer),
				"apiVer": version.apiVer._asdict(),
				"backCompatTo": version.backCompatTo._asdict(),
			} for version in self._test_nvdaAPIVersions]
			json.dump(nvdaAPIVersionsJson, nvdaAPIVersionFile)

	def test_addon_to_be_fully_removed(self):
		"""Creates addon data for an addon to be fully removed in subsequent datasets"""
		if self.testSet.id != 0:
			return
		addon = MockAddon()
		addon.addonId = "fullyRemoved"
		addon.addonVersion = MajorMinorPatch(0, 1)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 1)
		addon.lastTestedVersion = MajorMinorPatch(2021, 1)
		addon.channel = "stable"
		self.write_mock_addon_to_files(addon, [v.apiVer for v in self._test_nvdaAPIVersions])

	def test_addon_to_be_downgraded(self):
		"""Creates addon data for an addon to be downgraded in subsequent datasets"""
		# stable version
		addon = MockAddon()
		addon.addonId = "downgraded"
		addon.addonVersion = MajorMinorPatch(0, 9)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 1)
		addon.lastTestedVersion = MajorMinorPatch(2020, 4)
		addon.channel = "stable"
		exceptedStableVersions = [MajorMinorPatch(2020, 1), MajorMinorPatch(2020, 2)]
		if self.testSet.id == 1:
			exceptedStableVersions.extend((MajorMinorPatch(2020, 3), MajorMinorPatch(2020, 4)))
		self.write_mock_addon_to_files(addon, exceptedStableVersions)

		if self.testSet.id == 0:
			# version to be downgraded, removed in the second set
			addon = MockAddon()
			addon.addonId = "downgraded"
			addon.addonVersion = MajorMinorPatch(1, 1, 1)
			addon.minNvdaAPIVersion = MajorMinorPatch(2020, 3)
			addon.lastTestedVersion = MajorMinorPatch(2021, 1)
			addon.channel = "stable"
			self.write_mock_addon_to_files(
				addon,
				{MajorMinorPatch(2020, 3), MajorMinorPatch(2020, 4), MajorMinorPatch(2021, 1)}
			)

	def test_addon_versions(self):
		"""Creates addon data to test the newest available addon version is used"""
		# legacy version, to remain unlisted
		addon = MockAddon()
		addon.addonId = "legacyOldNewAddon"
		addon.addonVersion = MajorMinorPatch(1, 9)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 1)
		addon.lastTestedVersion = MajorMinorPatch(2020, 2)
		addon.channel = "stable"
		self.write_mock_addon_to_files(addon, set())

		# older version
		addon = MockAddon()
		addon.addonId = "legacyOldNewAddon"
		addon.addonVersion = MajorMinorPatch(2, 1)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 1)
		addon.lastTestedVersion = MajorMinorPatch(2020, 4)
		addon.channel = "stable"
		self.write_mock_addon_to_files(addon, {MajorMinorPatch(2020, 1), MajorMinorPatch(2020, 2)})

		# newer version
		addon = MockAddon()
		addon.addonId = "legacyOldNewAddon"
		addon.addonVersion = MajorMinorPatch(13, 0)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 3)
		addon.lastTestedVersion = MajorMinorPatch(2021, 1)
		addon.channel = "stable"
		expectedVersions = {MajorMinorPatch(2020, 3), MajorMinorPatch(2020, 4), MajorMinorPatch(2021, 1)}
		if self.testSet.id == 1:
			expectedVersions.add(MajorMinorPatch(2021, 2))
		self.write_mock_addon_to_files(addon, expectedVersions)

	def test_stable_from_beta(self):
		"""Generates a beta addon for the first set, and the equivalent stable addon for the second
		"""
		addon = MockAddon()
		addon.addonId = "betaToStable"
		addon.addonVersion = MajorMinorPatch(1, 1)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 1)
		addon.lastTestedVersion = MajorMinorPatch(2020, 2)
		addon.channel = "beta" if self.testSet.id == 0 else "stable"
		self.write_mock_addon_to_files(
			addon,
			{MajorMinorPatch(2020, 1), MajorMinorPatch(2020, 2), MajorMinorPatch(2020, 3)}
		)

	def test_nvdaAPIVersions(self):
		"""Creates addon data to test that the newest addon is used across various NVDA versions"""
		# older NVDA
		addon = MockAddon()
		addon.addonId = "_test_nvdaAPIVersions"
		addon.addonVersion = MajorMinorPatch(1, 0)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 1)
		addon.lastTestedVersion = MajorMinorPatch(2020, 3)
		addon.channel = "stable"
		self.write_mock_addon_to_files(addon, {MajorMinorPatch(2020, 1)})

		# middle NVDA Versions
		addon = MockAddon()
		addon.addonId = "_test_nvdaAPIVersions"
		addon.addonVersion = MajorMinorPatch(1, 1)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 2)
		addon.lastTestedVersion = MajorMinorPatch(2020, 4)
		addon.channel = "stable"
		self.write_mock_addon_to_files(addon, {MajorMinorPatch(2020, 2)})

		# newer NVDA versions
		addon = MockAddon()
		addon.addonId = "_test_nvdaAPIVersions"
		addon.addonVersion = MajorMinorPatch(1, 2)
		addon.minNvdaAPIVersion = MajorMinorPatch(2020, 3)
		addon.lastTestedVersion = MajorMinorPatch(2021, 1)
		addon.channel = "stable"
		expectedVersions = {MajorMinorPatch(2020, 3), MajorMinorPatch(2020, 4)}
		if self.testSet.id == 0:
			expectedVersions.add(MajorMinorPatch(2021, 1))
		self.write_mock_addon_to_files(addon, expectedVersions)

		if self.testSet.id == 1:
			addon = MockAddon()
			addon.addonId = "_test_nvdaAPIVersions"
			addon.addonVersion = MajorMinorPatch(1, 3)
			addon.minNvdaAPIVersion = MajorMinorPatch(2021, 1)
			addon.lastTestedVersion = MajorMinorPatch(2021, 2)
			addon.channel = "stable"
			self.write_mock_addon_to_files(addon, (MajorMinorPatch(2021, 1), MajorMinorPatch(2021, 2)))


class TestTransformation(unittest.TestCase):
	testSets: Tuple[TestSet] = (
		TestSet(
			id=0,
			inputDir=os.path.join(os.path.dirname(__file__), "test_data/input/addonSet0"),
			outputDir=os.path.join(os.path.dirname(__file__), "test_data/expected_results/addonSet0"),
		),
		TestSet(
			id=1,
			inputDir=os.path.join(os.path.dirname(__file__), "test_data/input/addonSet1"),
			outputDir=os.path.join(os.path.dirname(__file__), "test_data/expected_results/addonSet1"),
		),
	)

	@classmethod
	def _execute_transformation(cls, testSet: TestSet):
		if Path(TEST_OUTPUT_DIR).exists():
			shutil.rmtree(TEST_OUTPUT_DIR)
		nvdaAPIVersionsPath = f"{testSet.inputDir}/nvdaAPIVersions.json"
		process = subprocess.run(
			f"python -m src.transform {nvdaAPIVersionsPath} {testSet.inputDir} {TEST_OUTPUT_DIR}",
			shell=True
		)
		process.check_returncode()

	@classmethod
	def setUpClass(cls) -> None:
		for testSet in cls.testSets:
			_GenerateSystemTestData(testSet).generate_testData()

	def setUp(self):
		"""
		Runs the transformation.
		"""
		self._execute_transformation(self.testSets[0])

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
		self._check_expected_addons_added(self.testSets[0].outputDir)

	def test_expected_addons_updated(self):
		"""
		Confirms that a subsequent transformation is successful, and the first transformation results are
		overwritten.
		"""
		self._check_expected_addons_added(self.testSets[0].outputDir)
		self._execute_transformation(self.testSets[1])
		self._check_expected_addons_added(self.testSets[1].outputDir)
