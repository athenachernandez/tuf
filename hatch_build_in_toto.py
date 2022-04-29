#!/usr/bin/env python

# Copyright 2022, TUF contributors
# SPDX-License-Identifier: MIT OR Apache-2.0

"""Hatch plugin to generate in-toto link metadata for a build.

Hooks into the hatch build process to record the used sources as materials and the built
artifact(s) as products, signing the resulting link metadata with a configured
functionary key.

"""
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from in_toto.models.link import FILENAME_FORMAT, Link
from in_toto.models.metadata import Metablock
from in_toto.runlib import record_artifacts_as_dict


class InTotoBuildHook(BuildHookInterface):
    def _record_artifacts(self, path):
        return record_artifacts_as_dict(
            [path],
            exclude_patterns=[".*", "*~", "*.link*", "*.pyc"],
            normalize_line_endings=True,
            lstrip_paths=[f"{self.root}/"],
        )

    def initialize(self, version, build_data):
        self.materials = self._record_artifacts(self.root)

    def finalize(self, version, build_data, artifact_path):
        products = self._record_artifacts(artifact_path)

        name = self.target_name

        link = Metablock(
            signed=Link(
                name=self.target_name,
                materials=self.materials,
                products=products,
            )
        )

        sig = link.sign_gpg()
        link.dump(
            FILENAME_FORMAT.format(
                step_name=self.target_name, keyid=sig["keyid"]
            )
        )
