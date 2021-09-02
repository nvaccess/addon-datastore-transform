# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

import unittest


class Test_isAddonCompatible(unittest.TestCase):
	def test_valid_with_api(self):
		"""Confirm an addon is compatible with a fully tested API"""
		pass

	def test_valid_with_backwards_compatible_api(self):
		"""Confirm an addon is compatible with a backwards compatible API"""
		pass

	def test_not_valid_because_breaking_api(self):
		"""Confirm an addon is not compatible with a breaking API"""
		pass

	def test_not_valid_because_old_api(self):
		"""Confirm an addon is not compatible with an old API"""
		pass


class Test_getLatestAddons(unittest.TestCase):
	def test_beta_stable(self):
		"""Ensure addons are added to the correct channels"""
		pass

	def test_onlyNewerUsed(self):
		"""Ensure only the newest addon is used for an NVDA API version+channel"""
		pass

	def test_some_in_range(self):
		"""Confirm that an addon is only added for the correct NVDA API Versions"""
		pass

	def test_nvda_versions_shared_api_version(self):
		"""Ensure that two NVDA versions that have the same API version only create one entry"""
		pass
