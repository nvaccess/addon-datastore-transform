# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

from transform.datastructures import MajorMinorPatch
import unittest


class TestMajorMinorPatch(unittest.TestCase):
	""" Tests the MajorMinorPatch datastructure used by NVDAVersions and AddonVersions.
	Ensure that if a patch number is specified, it is preserved in strings, otherwised ignored.
	For example NVDAVersion(2019, 1) should not end up creating paths like /2019.1.0/.
	However, AddonVersion.fromStr("1.3.0") should preserve the patch number.
	"""
	def test_compare(self):
		"""Test comparing versions"""
		self.assertEqual(MajorMinorPatch(13, 2, 0), MajorMinorPatch(13, 2))
		self.assertLess(MajorMinorPatch(13, 2), MajorMinorPatch(13, 2, 1))
		self.assertGreater(MajorMinorPatch(3, 2, 1), MajorMinorPatch(1, 2, 3))

	def test_toStr(self):
		"""Test converting versions to string"""
		self.assertEqual(MajorMinorPatch(1, 3, 4).toStr(), "1.3.4")
		self.assertEqual(MajorMinorPatch(13, 2).toStr(), "13.2")
		self.assertEqual(MajorMinorPatch(13, 2, 0).toStr(), "13.2.0")

	def test_fromStr(self):
		"""Test creating versions from strings"""
		self.assertEqual(MajorMinorPatch.fromStr("1.0.4"), (1, 0, 4))
		self.assertEqual(MajorMinorPatch.fromStr("13.2.0"), MajorMinorPatch(13, 2, 0))
		self.assertEqual(MajorMinorPatch.fromStr("1.0.4"), MajorMinorPatch(1, 0, 4))
		self.assertEqual(MajorMinorPatch.fromStr("0.7"), MajorMinorPatch(0, 7, 0))
	
	def test_fromStr_throws(self):
		"""Test creating versions from invalid strings"""
		with self.assertRaises(TypeError):
			MajorMinorPatch.fromStr("0.7.0.3")
		with self.assertRaises(TypeError):
			MajorMinorPatch.fromStr("2")
		with self.assertRaises(ValueError):
			MajorMinorPatch.fromStr("foo")

	def test_fromStrToStr(self):
		"""Test creating versions to and from strings preserves itself"""
		self.assertEqual(MajorMinorPatch.fromStr("13.2").toStr(), "13.2")
		self.assertEqual(MajorMinorPatch.fromStr("13.2.0").toStr(), "13.2.0")
		self.assertEqual(MajorMinorPatch.fromStr("13.2.3").toStr(), "13.2.3")

	def test_fromDict(self):
		"""Test creating versions from dictionaries"""
		self.assertEqual(MajorMinorPatch(2, 3, 4), MajorMinorPatch.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "4",
		}))
		self.assertEqual(MajorMinorPatch(2, 3, 0), MajorMinorPatch.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "0",
		}))
		self.assertEqual(MajorMinorPatch(2, 1), MajorMinorPatch.fromDict({
			"major": "2",
			"minor": "1",
		}))
		self.assertEqual(MajorMinorPatch(2, 3), MajorMinorPatch.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "",
		}))

	def test_fromDict_throws(self):
		"""Test creating versions from invalid dictionaries"""
		with self.assertRaises(ValueError):
			MajorMinorPatch.fromDict({
				"major": "2.3",
				"minor": "23",
			})

	def test_fromDictToStr(self):
		"""Test creating versions from dictionaries preserves patch information to strings"""
		self.assertEqual("2.3.0", MajorMinorPatch.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "0",
		}).toStr())
		self.assertEqual("2.1", MajorMinorPatch.fromDict({
			"major": "2",
			"minor": "1",
		}).toStr())
		self.assertEqual("2.3.4", MajorMinorPatch.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "4",
		}).toStr())
		self.assertEqual("2.3", MajorMinorPatch.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "",
		}).toStr())
