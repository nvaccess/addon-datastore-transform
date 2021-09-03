# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

import glob
import json
import logging
import os
from pathlib import Path
import re
from typing import Iterable, Tuple
from .datastructures import (
	generateAddonChannelDict,
	Addon,
	AddonVersion,
	NVDAVersion,
	VersionCompatibility,
	WriteableAddons
)
from src.validate.validate import (
	ValidationError,
	validateJson,
	JSON_ADDON_DATA_SCHEMA,
	JSON_NVDA_VERSIONS_SCHEMA,
)

log = logging.getLogger()

addonInputPathSchema = re.compile(
	r"^.*/"  # parent path to addon directory
	r"(?P<name>[^/]*)"  # name of addon
	r"/(?P<major>[0-9]+)\.(?P<minor>[0-9]+)"  # version info
	r"\.?(?P<patch>[0-9]*)"  # optional patch info
	r"\.json$"  # file extension
)


def isAddonCompatible(addon: Addon, nvdaVersion: VersionCompatibility) -> bool:
	"""
	Confirms that the addon has been tested with an API version that the nvdaVersion is compatible with.
	"""
	return nvdaVersion.backCompatTo <= addon.lastTestedVersion and addon.minNVDAVersion <= nvdaVersion.apiVer


def getLatestAddons(addons: Iterable[Addon], NVDAVersions: Tuple[VersionCompatibility]) -> WriteableAddons:
	"""
	Given a set of addons and NVDA versions, create a dictionary mapping each nvdaAPIVersion and channel
	to the newest compatible addon.
	"""
	uniqueApiVersions = set(nvdaVersion.apiVer for nvdaVersion in NVDAVersions)
	latestAddons: WriteableAddons = dict(
		(nvdaAPIVersion, generateAddonChannelDict())
		for nvdaAPIVersion in uniqueApiVersions
	)
	for addon in addons:
		for nvdaVersion in NVDAVersions:
			NVDAVersionChannel = latestAddons[nvdaVersion.apiVer][addon.channel]
			if (
				isAddonCompatible(addon, nvdaVersion)
				and (
					addon.name not in NVDAVersionChannel
					or addon.version > NVDAVersionChannel[addon.name].version
				)
			):
				NVDAVersionChannel[addon.name] = addon
				log.debug(f"added {addon.name} {addon.version.toStr()}")
			else:
				log.debug(f"ignoring {addon.name} {addon.version.toStr()}")
	return latestAddons


def writeAddons(addonDir: str, addons: WriteableAddons) -> None:
	"""
	Given a unique mapping of (nvdaAPIVersion, channel) -> addon, write the addons to file.
	Throws a ValidationError and exits if writeable data does not match expected schema.
	"""
	for nvdaAPIVersion in addons:
		for channel in addons[nvdaAPIVersion]:
			for addonName in addons[nvdaAPIVersion][channel]:
				addon = addons[nvdaAPIVersion][channel][addonName]
				addonWritePath = f"{addonDir}/{nvdaAPIVersion.toStr()}/{addonName}"
				with open(addon.pathToData, "r") as oldAddonFile:
					addonData = json.load(oldAddonFile)
				Path(addonWritePath).mkdir(parents=True, exist_ok=True)
				with open(f"{addonWritePath}/{channel}.json", "w") as newAddonFile:
					validateJson(addonData, JSON_ADDON_DATA_SCHEMA)
					json.dump(addonData, newAddonFile)


def normalizePathStyleToUnix(path: str) -> str:
	"""Use to make regex and other string checks simpler and standardized."""
	return path.replace("\\", "/")


def readAddons(addonDir: str) -> Iterable[Addon]:
	"""
	Read addons from a directory and capture required data for processing.
	Works as a generator to minimize memory usage, as such, each use of iteration should call readAddons.
	Skips addons and logs errors if the naming schema or json schema do not match what is expected.
	"""
	for fileName in glob.glob(f"{addonDir}/**/*.json"):
		fileName = normalizePathStyleToUnix(fileName)
		addonPathMatch = re.match(addonInputPathSchema, fileName)
		if addonPathMatch is None:
			log.error(f"{fileName} doesn't match regex")
			continue
		addonData = addonPathMatch.groupdict()
		addonName = addonData["name"]
		addonVersion = AddonVersion.fromDict(addonData)
		with open(fileName, "r") as addonFile:
			addonData = json.load(addonFile)
		try:
			validateJson(addonData, JSON_ADDON_DATA_SCHEMA)
		except ValidationError as e:
			log.error(f"{fileName} doesn't match schema: {e}")
			continue
		yield Addon(
			name=addonName,
			version=addonVersion,
			pathToData=fileName,
			channel=addonData["channel"],
			minNVDAVersion=NVDAVersion.fromDict(addonData["minNVDAVersion"]),
			lastTestedVersion=NVDAVersion.fromDict(addonData["lastTestedVersion"]),
		)


def readNVDAVersionInfo(pathToFile: str) -> Tuple[VersionCompatibility]:
	"""
	Reads and captures NVDA version information from file.
	"""
	with open(pathToFile, "r") as NVDAVersionFile:
		NVDAVersionData = json.load(NVDAVersionFile)
	validateJson(NVDAVersionData, JSON_NVDA_VERSIONS_SCHEMA)
	return tuple(
		VersionCompatibility(
			nvdaVersion=NVDAVersion.fromStr(version["NVDAVersion"]),
			apiVer=NVDAVersion.fromStr(version["apiVer"]),
			backCompatTo=NVDAVersion.fromStr(version["backCompatTo"]),
		) for version in NVDAVersionData
	)


def emptyDirectory(dir: str) -> None:
	for filename in glob.glob(dir + "/**/*.json", recursive=True):
		if os.path.isfile(filename):
			os.remove(filename)


def runTransformation(nvdaVersionsPath: str, sourceDir: str, outputDir: str) -> None:
	"""
	Performs the transformation of addon data described in the readme.
	Takes addon data found in sourceDir that fits the schema and writes the transformed data to outputDir.
	Uses the NVDA API Versions found in nvdaVersionsPath.
	"""
	NVDAVersionInfo = readNVDAVersionInfo(nvdaVersionsPath)
	latestAddons = getLatestAddons(readAddons(sourceDir), NVDAVersionInfo)
	emptyDirectory(outputDir)
	writeAddons(outputDir, latestAddons)
