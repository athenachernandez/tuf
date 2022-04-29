#!/usr/bin/env python

# Copyright 2022, TUF contributors
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Hatch plugin to generate in-toto link metadata for a build.

Hooks into the hatch build process to record the used sources as materials and the built
artifact(s) as products, signing the resulting link metadata with a configured
functionary key.

"""
import json
import os

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from in_toto.models.link import FILENAME_FORMAT, Link
from in_toto.models.metadata import Metablock
from in_toto.runlib import record_artifacts_as_dict


class EnvVars:
    KEY = "HATCH_IN_TOTO_KEY"
    GPG_KEYID = "HATCH_IN_TOTO_GPG_KEYID"


# Define filters for recording materials in the project directory
# NOTE: No filters needed for products, because they are recorded explicitly
# NOTE: Leading wildcards for path fragments that seemingly start at root are needed,
# because the actual root of the path is /. in-toto only strips the left part in the end.
# paths
MATERIAL_EXCLUDES = [
    "dist",
    "*/docs/build",
    "*/tests/htmlcov",
    ".*",
    "*~",
    "*.egg-info",
    "*.link*",
    "*.pyc",
]


class InTotoBuildHook(BuildHookInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Common config for artifact recording
        self.lstrip = [f"{self.root}/"]

        # Parse config from envvars
        key_data = os.environ.get(EnvVars.KEY)
        self.gpg_keyid = os.environ.get(EnvVars.GPG_KEYID)
        if (key_data is not None) == (self.gpg_keyid is not None):
            raise ValueError(
                f"Exactly one of `{EnvVars.KEY} or {EnvVars.GPG_KEYID}` must be set"
            )

        if key_data:
            self.key = json.loads(key_data)

    def initialize(self, version, build_data):
        self.materials = record_artifacts_as_dict(
            [self.root],
            exclude_patterns=MATERIAL_EXCLUDES,
            lstrip_paths=self.lstrip,
        )

    def finalize(self, version, build_data, artifact_path):
        products = record_artifacts_as_dict(
            [artifact_path], lstrip_paths=self.lstrip
        )

        link = Metablock(
            signed=Link(
                name=self.target_name,
                materials=self.materials,
                products=products,
            )
        )
        if self.key:
            sig = link.sign(self.key)
        elif self.gpg_keyid:
            sig = link.sign_gpg(self.gpg_keyid)
        else:
            raise RuntimeError("No signing key")

        link_filename = FILENAME_FORMAT.format(
            step_name=self.target_name, keyid=sig["keyid"]
        )

        link.dump(os.path.join(self.directory, link_filename))
