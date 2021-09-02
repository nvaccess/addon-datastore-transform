# Copyright (C) 2021 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

"""
Usage: python -m transform {nvdaVersionsPath} {inputPath} {outputPath} [logLevel]
"""

import logging
import sys
from .transform import runTransformation

log = logging.getLogger()

nvdaVersionsPath = sys.argv[1]
sourceDir = sys.argv[2]
outputDir = sys.argv[3]
handler = logging.StreamHandler(sys.stdout)  # always log to stdout
if len(sys.argv) == 5:
	log.setLevel(sys.argv[4])
else:
	log.setLevel(logging.WARNING)
log.addHandler(handler)
runTransformation(nvdaVersionsPath, sourceDir, outputDir)
