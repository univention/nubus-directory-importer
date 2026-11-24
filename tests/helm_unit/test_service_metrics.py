# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2026 Univention GmbH

import pytest

from univention.testing.helm.base import Base


def metrics_values(**kwargs):
    return {"metrics": {"enabled": True, **kwargs}}


class TestMetrics(Base):
    def render(self, helm, chart_path, values, template_file):
        return self.helm_template_file(helm, chart_path, values, template_file)

    @pytest.mark.parametrize(
        "template_file",
        ["templates/service-metrics.yaml", "templates/servicemonitor.yaml"],
    )
    def test_disabled_by_default(self, helm, chart_path, template_file):
        assert self.render(helm, chart_path, {}, template_file) == {}

    def test_disabled_by_default_container_port(self, helm, chart_path):
        deployment = self.render(helm, chart_path, {}, "templates/deployment.yaml")
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        assert "ports" not in container

    def test_container_port(self, helm, chart_path):
        deployment = self.render(
            helm,
            chart_path,
            metrics_values(port=9999),
            "templates/deployment.yaml",
        )
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        assert container["ports"] == [
            {"name": "metrics", "containerPort": 9999, "protocol": "TCP"},
        ]

    def test_service(self, helm, chart_path):
        service = self.render(
            helm,
            chart_path,
            metrics_values(port=9999, service={"annotations": {"foo": "bar"}}),
            "templates/service-metrics.yaml",
        )
        assert service["kind"] == "Service"
        assert service["metadata"]["annotations"] == {"foo": "bar"}
        assert service["spec"]["ports"] == [
            {"name": "metrics", "port": 9999, "targetPort": "metrics", "protocol": "TCP"},
        ]
        deployment = self.render(
            helm,
            chart_path,
            metrics_values(),
            "templates/deployment.yaml",
        )
        assert (
            service["spec"]["selector"]
            == deployment["spec"]["selector"]["matchLabels"]
        )

    def test_service_monitor_requires_metrics(self, helm, chart_path):
        values = {"metrics": {"enabled": False, "serviceMonitor": {"enabled": True}}}
        assert self.render(helm, chart_path, values, "templates/servicemonitor.yaml") == {}

    def test_service_monitor(self, helm, chart_path):
        values = metrics_values(
            serviceMonitor={
                "enabled": True,
                "interval": "30s",
                "scrapeTimeout": "10s",
                "labels": {"release": "prometheus"},
            },
        )
        service_monitor = self.render(
            helm,
            chart_path,
            values,
            "templates/servicemonitor.yaml",
        )
        service = self.render(helm, chart_path, values, "templates/service-metrics.yaml")

        assert service_monitor["kind"] == "ServiceMonitor"
        assert service_monitor["metadata"]["labels"]["release"] == "prometheus"
        assert service_monitor["spec"]["endpoints"] == [
            {
                "port": "metrics",
                "path": "/metrics",
                "interval": "30s",
                "scrapeTimeout": "10s",
            },
        ]
        selector = service_monitor["spec"]["selector"]["matchLabels"]
        assert selector.items() <= service["metadata"]["labels"].items()
        assert (
            service_monitor["metadata"]["namespace"]
            == service["metadata"]["namespace"]
            == service_monitor["spec"]["namespaceSelector"]["matchNames"][0]
        )

    def test_service_monitor_namespace(self, helm, chart_path):
        values = metrics_values(
            serviceMonitor={"enabled": True, "namespace": "monitoring"},
        )
        service_monitor = self.render(
            helm,
            chart_path,
            values,
            "templates/servicemonitor.yaml",
        )
        service = self.render(helm, chart_path, values, "templates/service-metrics.yaml")

        assert service_monitor["metadata"]["namespace"] == "monitoring"
        assert service_monitor["spec"]["namespaceSelector"]["matchNames"] == [
            service["metadata"]["namespace"],
        ]
