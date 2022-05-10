#!/usr/bin/env python

# Copyright 2022, TUF contributors
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Hatch plugin to generate in-toto link metadata for a build.

Hooks into the hatch build process to record the used sources as materials and the built
artifact(s) as products, signing the resulting link metadata with a configured
functionary key.


    export HATCH_BUILD_HOOK_ENABLE_CUSTOM=true
    export HATCH_IN_TOTO_GPG_KEYID=<gpg key id>
        **OR** export HATCH_IN_TOTO_KEY=<encrypted ed25519 private key data>
               export HATCH_IN_TOTO_KEY_PW=<decryption password>
    python -m build

"""
import os

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from in_toto.models.link import FILENAME_FORMAT, Link
from in_toto.models.metadata import Metablock
from in_toto.runlib import record_artifacts_as_dict
from securesystemslib.keys import decrypt_key

IN_TOTO_DIR = ".in_toto"

# TODO: Is there a better way to configure this? KEY makes sense as envvar, but
# non-confidential config would be nice as arg. Can we use `build`s `--config-setting`?
class EnvVars:
    KEY = "HATCH_IN_TOTO_KEY"
    KEY_PW = "HATCH_IN_TOTO_KEY_PW"
    GPG_KEYID = "HATCH_IN_TOTO_GPG_KEYID"


# Define exclude filters for recording materials in the project directory
# NOTE: No filters needed for products, because they are recorded explicitly
# TODO: Consider configuration via pyproject.toml
# see https://ofek.dev/hatch/latest/config/build/#build-hooks
MATERIAL_EXCLUDES = [
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    ".*",
    "*~",
    "*.egg-info",
    "*.pyc",
]


class InTotoBuildHook(BuildHookInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Common config for artifact recording
        self.lstrip = [f"{self.root}/"]

        # Parse config from envvars
        key_data = os.environ.get(EnvVars.KEY)
        key_pw = os.environ.get(EnvVars.KEY_PW)
        self.gpg_keyid = os.environ.get(EnvVars.GPG_KEYID)

        if key_data and self.gpg_keyid:
            raise ValueError(
                f"Set only one of {EnvVars.KEY} or {EnvVars.GPG_KEYID}"
            )

        if not (key_data or self.gpg_keyid):
            raise ValueError(
                f"Requires one of {EnvVars.KEY} or {EnvVars.GPG_KEYID}"
            )

        self.key = None
        if key_data:
            if not key_pw:
                raise ValueError(
                    f"Requires {EnvVars.KEY_PW} if {EnvVars.KEY} is set"
                )

            self.key = decrypt_key(key_data, key_pw)

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

        link.dump(os.path.join(IN_TOTO_DIR, link_filename))
