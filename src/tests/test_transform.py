# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

from src.transform.datastructures import AddonVersion, NVDAVersion, VersionCompatibility
from src.transform.transform import getLatestAddons, _isAddonCompatible
from src.tests.generateData import MockAddon
import unittest

V_2020_1 = NVDAVersion(2020, 1)
V_2020_2 = NVDAVersion(2020, 2)
V_2020_3 = NVDAVersion(2020, 3)
V_2021_1 = NVDAVersion(2021, 1)
V_2021_1_1 = NVDAVersion(2021, 1, 1)
V_2021_2 = NVDAVersion(2021, 2)
V_2022_1 = NVDAVersion(2022, 1)
nvdaVersion2020_2 = VersionCompatibility(V_2020_2, V_2020_2, V_2020_1)
nvdaVersion2020_3 = VersionCompatibility(V_2020_3, V_2020_3, V_2020_1)
nvdaVersion2021_1 = VersionCompatibility(V_2021_1, V_2021_1, V_2021_1)
nvdaVersion2021_1_1 = VersionCompatibility(V_2021_1_1, V_2021_1, V_2021_1)
nvdaVersion2022_1 = VersionCompatibility(V_2022_1, V_2022_1, V_2022_1)


class Test_isAddonCompatible(unittest.TestCase):
	def test_valid_with_api(self):
		"""Confirm an addon is compatible with a fully tested API"""
		addon = MockAddon()
		addon.minNVDAVersion = V_2020_1
		addon.lastTestedVersion = V_2020_2
		self.assertTrue(_isAddonCompatible(addon, nvdaVersion2020_2))

	def test_valid_with_backwards_compatible_api(self):
		"""Confirm an addon is compatible with a backwards compatible API"""
		addon = MockAddon()
		addon.minNVDAVersion = V_2020_1
		addon.lastTestedVersion = V_2020_2
		self.assertTrue(_isAddonCompatible(addon, nvdaVersion2020_3))

	def test_not_valid_because_breaking_api(self):
		"""Confirm an addon is not compatible with a breaking API"""
		addon = MockAddon()
		addon.minNVDAVersion = V_2020_1
		addon.lastTestedVersion = V_2020_2
		self.assertFalse(_isAddonCompatible(addon, nvdaVersion2021_1))

	def test_not_valid_because_old_api(self):
		"""Confirm an addon is not compatible with an old API"""
		addon = MockAddon()
		addon.minNVDAVersion = V_2021_1
		addon.lastTestedVersion = V_2021_2
		self.assertFalse(_isAddonCompatible(addon, nvdaVersion2020_3))


class Test_getLatestAddons(unittest.TestCase):
	def test_beta_stable(self):
		"""Ensure addons are added to the correct channels"""
		NVDAVersions = (nvdaVersion2020_2, nvdaVersion2020_3)
		betaAddon = MockAddon()
		betaAddon.minNVDAVersion = V_2020_1
		betaAddon.lastTestedVersion = V_2020_3
		betaAddon.channel = "beta"
		betaAddon.addonVersionNumber = AddonVersion(0, 2, 1)
		stableAddon = MockAddon()
		stableAddon.minNVDAVersion = V_2020_1
		stableAddon.lastTestedVersion = V_2020_2
		stableAddon.channel = "stable"
		stableAddon.addonVersionNumber = AddonVersion(0, 2)
		self.assertDictEqual(getLatestAddons([betaAddon, stableAddon], NVDAVersions), {
			V_2020_2: {"beta": {betaAddon.addonId: betaAddon}, "stable": {stableAddon.addonId: stableAddon}},
			V_2020_3: {"beta": {betaAddon.addonId: betaAddon}, "stable": {stableAddon.addonId: stableAddon}},
		})

	def test_onlyNewerUsed(self):
		"""Ensure only the newest addon is used for a version+channel"""
		NVDAVersions = (nvdaVersion2020_2, nvdaVersion2020_3)
		newAddon = MockAddon()
		newAddon.addonId = "foo"
		newAddon.minNVDAVersion = V_2020_1
		newAddon.lastTestedVersion = V_2020_3
		newAddon.channel = "beta"
		newAddon.addonVersionNumber = AddonVersion(0, 2)
		oldAddon = MockAddon()
		oldAddon.addonId = "foo"
		oldAddon.minNVDAVersion = V_2020_1
		oldAddon.lastTestedVersion = V_2020_2
		oldAddon.channel = "beta"
		oldAddon.addonVersionNumber = AddonVersion(0, 1)
		self.assertDictEqual(getLatestAddons([oldAddon, newAddon], NVDAVersions), {
			V_2020_2: {"beta": {"foo": newAddon}, "stable": {}},
			V_2020_3: {"beta": {"foo": newAddon}, "stable": {}},
		})

	def test_some_in_range(self):
		"""Confirm that an addon is only added for the correct NVDAVersions"""
		NVDAVersions = (nvdaVersion2020_3, nvdaVersion2021_1, nvdaVersion2022_1)
		addon = MockAddon()
		addon.minNVDAVersion = V_2021_1
		addon.lastTestedVersion = V_2021_2
		addon.channel = "beta"
		self.assertDictEqual(getLatestAddons([addon], NVDAVersions), {
			V_2020_3: {"beta": {}, "stable": {}},
			V_2021_1: {"beta": {addon.addonId: addon}, "stable": {}},
			V_2022_1: {"beta": {}, "stable": {}},
		})

	def test_nvda_versions_shared_api_version(self):
		"""Ensure that two NVDA versions that have the same API version only create one entry"""
		NVDAVersions = (nvdaVersion2021_1, nvdaVersion2021_1_1)
		addon = MockAddon()
		addon.minNVDAVersion = V_2021_1
		addon.lastTestedVersion = V_2021_2
		addon.channel = "beta"
		addon.addonVersionNumber = AddonVersion(0, 1)
		self.assertDictEqual(getLatestAddons([addon], NVDAVersions), {
			V_2021_1: {"beta": {addon.addonId: addon}, "stable": {}},
		})
