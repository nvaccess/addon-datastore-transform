# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

from dataclasses import dataclass
from typing import Dict, Literal, NamedTuple, Union

# These values are validated using runtime validation -> see addon_data.schema.json
AddonChannels = Literal["beta", "stable"]


class NVDAVersion(NamedTuple):
	"""
	Ensure that if a patch number is specified, it is preserved in strings, otherwised ignored.
	For example NVDAVersion(2019, 1) should not end up creating paths like /2019.1.0/.
	"""
	major: int
	minor: int
	patch: Union[int, bool] = False  # is compared as 0, but works as a flag for hiding the patch by default

	@classmethod
	def fromStr(cls, version: str):
		versionTuple = tuple(int(v) for v in version.split("."))
		return cls(*versionTuple)

	def toStr(self):
		patchStr = f".{self.patch}" if self.patch is not False else ""
		return f"{self.major}.{self.minor}{patchStr}"


class AddonVersion(NamedTuple):
	major: int
	minor: int
	patch: int = 0


@dataclass
class VersionCompatibility:
	nvdaVersion: NVDAVersion  # The NVDA version
	apiVer: NVDAVersion  # The API version for this NVDA version, normally matches the NVDA version
	backCompatTo: NVDAVersion  # The earliest API version that this NVDA version supports


@dataclass
class Addon:
	addonId: str
	addonVersion: AddonVersion
	pathToData: str
	channel: AddonChannels
	minNVDAVersion: NVDAVersion
	lastTestedVersion: NVDAVersion


AddonChannelDict = Dict[AddonChannels, Dict[str, Addon]]
WriteableAddons = Dict[NVDAVersion, AddonChannelDict]


def generateAddonChannelDict() -> AddonChannelDict:
	return {"beta": {}, "stable": {}}
