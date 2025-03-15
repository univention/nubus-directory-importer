# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

from univention.testing.helm.secret import SecretPasswords


class TestSourceDirectory(SecretPasswords):
    template_file = "templates/secret-source-directory.yaml"

    def values(self, localpart: dict) -> dict:
        return {"sourceDirectory": localpart}


class TestUDM(SecretPasswords):
    template_file = "templates/secret-udm.yaml"

    def values(self, localpart: dict) -> dict:
        return {"udm": localpart}
