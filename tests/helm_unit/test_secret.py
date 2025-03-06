# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

from pytest_helm.helm import Helm
from pytest_helm.utils import findone
from yaml import safe_load


class Labels:
    manifest = None

    def test_add_another_label(self, helm, chart_path):
        values = safe_load(
            """
            additionalLabels:
              local.test/name: "value"
        """,
        )
        result = helm.helm_template(chart_path, values, self.manifest)
        assert len(result) == 1
        labels = findone(result[0], "metadata.labels")

        assert labels["local.test/name"] == "value"

    def test_modify_a_common_label(self, helm, chart_path):
        values = safe_load(
            """
            additionalLabels:
              app.kubernetes.io/name: "replaced value"
        """,
        )
        result = helm.helm_template(chart_path, values, self.manifest)
        assert len(result) == 1
        labels = findone(result[0], "metadata.labels")

        assert labels["app.kubernetes.io/name"] == "replaced value"

    def test_value_is_templated(self, helm: Helm, chart_path):
        values = safe_load(
            """
            global:
              test: "stub-value"
            additionalLabels:
              local.test/name: "{{ .Values.global.test }}"
        """,
        )
        result = helm.helm_template(chart_path, values, self.manifest)
        assert len(result) == 1
        labels = findone(result[0], "metadata.labels")

        assert labels["local.test/name"] == "stub-value"


class TestSourceDirectory(Labels):
    manifest = "templates/secret-source-directory.yaml"


class TestUDM(Labels):
    manifest = "templates/secret-udm.yaml"
