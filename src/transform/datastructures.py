# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

from dataclasses import dataclass
from typing import Dict, Literal, NamedTuple, Optional, OrderedDict, Union

AddonChannels = Literal["beta", "stable"]


class MajorMinorPatch(NamedTuple):
	""" The MajorMinorPatch datastructure is used by NVDAVersions and AddonVersions.
	Ensure that if a patch number is specified, it is preserved in strings, otherwised ignored.
	For example NVDAVersion(2019, 1) should not end up creating paths like /2019.1.0/.
	However, AddonVersion.fromStr("1.3.0") should preserve the patch number.
	"""
	major: int
	minor: int
	patch: Union[int, bool] = False  # is compared as 0, but works as a flag for hiding the patch by default

	@classmethod
	def fromStr(cls, version: str):
		versionTuple = tuple(int(v) for v in version.split("."))
		return MajorMinorPatch(*versionTuple)

	@classmethod
	def fromDict(cls, version: Dict[str, Optional[str]]):
		if "patch" in version and version["patch"]:
			return MajorMinorPatch(
				int(version["major"]),
				int(version["minor"]),
				int(version["patch"]),
			)
		else:
			return MajorMinorPatch(
				int(version["major"]),
				int(version["minor"]),
			)

	def toStr(self):
		patchStr = f".{self.patch}" if self.patch is not False else ""
		return f"{self.major}.{self.minor}{patchStr}"

	def toJson(self) -> OrderedDict[str, int]:
		return {
			"major": self.major,
			"minor": self.minor,
			"patch": int(self.patch),  # ensure this is an int for json schema
		}


class NVDAVersion(MajorMinorPatch):
	pass


class AddonVersion(MajorMinorPatch):
	pass


@dataclass
class VersionCompatibility:
	nvdaVersion: NVDAVersion  # The NVDA version
	apiVer: NVDAVersion  # The API version for this NVDA version, normally matches the NVDA version
	backCompatTo: NVDAVersion  # The earliest API version that this NVDA version supports


@dataclass
class Addon:
	name: str  # set from source path
	version: AddonVersion  # set from source path
	pathToData: str  # set from source path
	channel: AddonChannels  # read from data
	minNVDAVersion: NVDAVersion  # read from data
	lastTestedVersion: NVDAVersion  # read from data


AddonChannelDict = Dict[AddonChannels, Dict[str, Addon]]
WriteableAddons = Dict[NVDAVersion, AddonChannelDict]


def generateAddonChannelDict() -> AddonChannelDict:
	return {"beta": {}, "stable": {}}
