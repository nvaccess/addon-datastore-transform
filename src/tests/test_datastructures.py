# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

from src.transform.datastructures import NVDAVersion
import unittest


class TestNVDAVersion(unittest.TestCase):
	"""
	Ensure that if a patch number is specified, it is preserved in strings, otherwised ignored.
	For example NVDAVersion(2019, 1) should not end up creating paths like /2019.1.0/.
	"""
	def test_compare(self):
		"""Test comparing versions"""
		self.assertEqual(NVDAVersion(13, 2, 0), NVDAVersion(13, 2))
		self.assertLess(NVDAVersion(13, 2), NVDAVersion(13, 2, 1))
		self.assertGreater(NVDAVersion(3, 2, 1), NVDAVersion(1, 2, 3))

	def test_toStr(self):
		"""Test converting versions to string"""
		self.assertEqual(NVDAVersion(1, 3, 4).toStr(), "1.3.4")
		self.assertEqual(NVDAVersion(13, 2).toStr(), "13.2")
		self.assertEqual(NVDAVersion(13, 2, 0).toStr(), "13.2.0")

	def test_fromStr(self):
		"""Test creating versions from strings"""
		self.assertEqual(NVDAVersion.fromStr("1.0.4"), (1, 0, 4))
		self.assertEqual(NVDAVersion.fromStr("13.2.0"), NVDAVersion(13, 2, 0))
		self.assertEqual(NVDAVersion.fromStr("1.0.4"), NVDAVersion(1, 0, 4))
		self.assertEqual(NVDAVersion.fromStr("0.7"), NVDAVersion(0, 7, 0))
	
	def test_fromStr_throws(self):
		"""Test creating versions from invalid strings"""
		with self.assertRaises(TypeError):
			NVDAVersion.fromStr("0.7.0.3")
		with self.assertRaises(TypeError):
			NVDAVersion.fromStr("2")
		with self.assertRaises(ValueError):
			NVDAVersion.fromStr("foo")

	def test_fromStrToStr(self):
		"""Test creating versions to and from strings preserves itself"""
		self.assertEqual(NVDAVersion.fromStr("13.2").toStr(), "13.2")
		self.assertEqual(NVDAVersion.fromStr("13.2.0").toStr(), "13.2.0")
		self.assertEqual(NVDAVersion.fromStr("13.2.3").toStr(), "13.2.3")

	def test_fromDict(self):
		"""Test creating versions from dictionaries"""
		self.assertEqual(NVDAVersion(2, 3, 4), NVDAVersion.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "4",
		}))
		self.assertEqual(NVDAVersion(2, 3, 0), NVDAVersion.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "0",
		}))
		self.assertEqual(NVDAVersion(2, 1), NVDAVersion.fromDict({
			"major": "2",
			"minor": "1",
		}))
		self.assertEqual(NVDAVersion(2, 3), NVDAVersion.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "",
		}))

	def test_fromDict_throws(self):
		"""Test creating versions from invalid dictionaries"""
		with self.assertRaises(ValueError):
			NVDAVersion.fromDict({
				"major": "2.3",
				"minor": "23",
			})

	def test_fromDictToStr(self):
		"""Test creating versions from dictionaries preserves patch information to strings"""
		self.assertEqual("2.3.0", NVDAVersion.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "0",
		}).toStr())
		self.assertEqual("2.1", NVDAVersion.fromDict({
			"major": "2",
			"minor": "1",
		}).toStr())
		self.assertEqual("2.3.4", NVDAVersion.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "4",
		}).toStr())
		self.assertEqual("2.3", NVDAVersion.fromDict({
			"major": "2",
			"minor": "3",
			"patch": "",
		}).toStr())
