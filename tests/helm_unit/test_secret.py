# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

from pytest_helm.manifests.secret import Secret


class TestSourceDirectory(Secret):
    manifest = "templates/secret-source-directory.yaml"

    def values(self, localpart: dict) -> dict:
        return {"sourceDirectory": localpart}


class TestUDM(Secret):
    manifest = "templates/secret-udm.yaml"

    def values(self, localpart: dict) -> dict:
        return {"udm": localpart}
