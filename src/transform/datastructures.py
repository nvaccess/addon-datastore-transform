# Copyright (C) 2021-2023 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

from dataclasses import dataclass
from typing import (
	Dict,
	List,
	Literal,
	NamedTuple,
)

from requests.structures import CaseInsensitiveDict

# These values are validated using runtime validation -> see addon_data.schema.json
AddonChannels = Literal["beta", "stable", "dev"]


class MajorMinorPatch(NamedTuple):
	major: int
	minor: int
	patch: int = 0

	def __str__(self) -> str:
		return f"{self.major}.{self.minor}.{self.patch}"


@dataclass
class VersionCompatibility:
	apiVer: MajorMinorPatch  # The API version for this NVDA version, normally matches the NVDA version
	backCompatTo: MajorMinorPatch  # The earliest API version that this NVDA version supports


@dataclass
class Addon:
	addonId: str
	addonVersion: MajorMinorPatch
	pathToData: str
	channel: AddonChannels
	minNvdaAPIVersion: MajorMinorPatch
	lastTestedVersion: MajorMinorPatch
	translations: List[Dict[str, str]]


AddonChannelDict = Dict[AddonChannels, Dict[str, Addon]]
WriteableAddons = Dict[MajorMinorPatch, AddonChannelDict]


def generateAddonChannelDict() -> AddonChannelDict:
	# Identical add-on IDs may have different casing
	# due to legacy add-on submissions.
	# This can be removed when old submissions are given updated casing.
	return {
		"beta": CaseInsensitiveDict(),
		"stable": CaseInsensitiveDict(),
		"dev": CaseInsensitiveDict(),
	}
