# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

from transform.datastructures import Addon
from unittest.mock import create_autospec, Mock


def MockAddon() -> Addon:
	"""Mocks the creation of an Addon. Specific required data for testing should be overwritten."""
	return Mock(spec=create_autospec(Addon))()
