# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

"""
Runs the dataView generation system on test data.
Confirms the end result data is as expected.
Creates a number of specific scenarios for the test data.
"""

from dataclasses import dataclass
from typing import Iterable
import unittest


@dataclass
class TestSet:
	inputDir: str
	outputDir: str


class _GenerateSystemTestData:
	"""
	A class which generates system test data for a given testing set given.
	"""
	def __init__(self, testSet: TestSet) -> None:
		pass

	def generate_testData(self):
		"""
		Generates system test data.
		"""
		self.test_addon_to_be_downgraded()
		self.test_addon_versions()
		self.test_stable_from_beta()
		self.test_addon_to_be_fully_removed()
		self.test_NVDAVersions()

	def test_addon_to_be_fully_removed(self):
		"""Creates addon data for an addon to be fully removed in subsequent datasets"""
		pass

	def test_addon_to_be_downgraded(self):
		"""Creates addon data for an addon to be downgraded in subsequent datasets"""
		pass

	def test_addon_versions(self):
		"""Creates addon data to test the newest available addon version is used"""
		pass

	def test_stable_from_beta(self):
		"""Generates a beta addon for the first set, and the equivalent stable addon for the second
		"""
		pass

	def test_NVDAVersions(self):
		"""Creates addon data to test that the newest addon is used across various NVDA versions"""
		pass


class TestTransformation(unittest.TestCase):
	testSets: Iterable[TestSet] = []

	@classmethod
	def _execute_transformation(cls, inputPath: str, outputPath: str):
		pass

	@classmethod
	def setUpClass(cls) -> None:
		for set in cls.testSets:
			_GenerateSystemTestData(set).generate_testData()

	def setUp(self):
		"""
		Runs the transformation.
		"""
		pass

	def _check_expected_addons_added(self, expectedResultsPath: str):
		"""
		Checks that all the data and files in expectedResultsPath match the test output directory.
		"""
		pass

	def test_expected_addons_added(self):
		"""
		Confirms the initial transformation was successful.
		"""
		pass

	def test_expected_addons_updated(self):
		"""
		Confirms that a subsequent transformation is successful, and the first transformation results are
		overwritten.
		"""
		pass
