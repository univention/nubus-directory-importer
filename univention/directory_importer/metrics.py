# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2026 Univention GmbH

"""
univention.directory_importer.metrics - Prometheus metrics
"""

import logging
import time
from typing import NamedTuple

from prometheus_client import (
    REGISTRY,
    Counter,
    Info,
    disable_created_metrics,
    start_http_server,
)
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import Collector

from .__about__ import __version__

PREFIX = "nubus_directory_importer"

# the *_created series of counters are of no use here
disable_created_metrics()


class ModelStats(NamedTuple):
    """
    counters of syncing the entries of a single UDM model
    """

    source_entries: int
    errors: int
    deleted_entries: int


class RunSnapshot(NamedTuple):
    """
    result of the last finished sync run
    """

    success: bool
    finished_at: float
    duration: float
    last_success_at: float | None
    # UDM model name -> counters, only models synced completely in this run
    models: dict[str, ModelStats]


class LastRunCollector(Collector):
    """
    exposes the result of the last finished sync run as one consistent
    snapshot, which is replaced as a whole at the end of every run
    """

    MODEL_METRICS = (
        (
            "last_run_source_entries",
            "Number of source entries processed in the last sync run",
            "source_entries",
        ),
        (
            "last_run_errors",
            "Number of errors when processing source entries in the last sync run",
            "errors",
        ),
        (
            "last_run_deleted_entries",
            "Number of obsolete target entries removed in the last sync run",
            "deleted_entries",
        ),
    )

    def __init__(self):
        self.snapshot: RunSnapshot | None = None

    def collect(self):
        # read the reference once, publish() replaces it as a whole
        snapshot = self.snapshot
        if snapshot is None:
            return
        yield GaugeMetricFamily(
            f"{PREFIX}_last_run_success",
            "Whether the last sync run finished completely (1) or was aborted (0)",
            value=int(snapshot.success),
        )
        yield GaugeMetricFamily(
            f"{PREFIX}_last_run_timestamp_seconds",
            "Unix time when the last sync run finished, successful or not",
            value=snapshot.finished_at,
        )
        yield GaugeMetricFamily(
            f"{PREFIX}_last_run_duration_seconds",
            "Duration of the last sync run in seconds",
            value=snapshot.duration,
        )
        if snapshot.last_success_at is not None:
            yield GaugeMetricFamily(
                f"{PREFIX}_last_success_timestamp_seconds",
                "Unix time when the last successful sync run finished",
                value=snapshot.last_success_at,
            )
        for name, documentation, field in self.MODEL_METRICS:
            family = GaugeMetricFamily(
                f"{PREFIX}_{name}",
                documentation,
                labels=["model"],
            )
            for model, stats in snapshot.models.items():
                family.add_metric([model], getattr(stats, field))
            yield family

    def publish(self, snapshot: RunSnapshot):
        self.snapshot = snapshot


BUILD_INFO = Info(
    f"{PREFIX}_build",
    "Directory importer build information",
)
BUILD_INFO.info({"version": __version__})

RUNS = Counter(
    f"{PREFIX}_runs",
    "Number of finished sync runs by result",
    ["result"],
)
for _result in ("success", "failed"):
    RUNS.labels(_result)

LAST_RUN = LastRunCollector()
REGISTRY.register(LAST_RUN)

UDM_REQUESTS = Counter(
    f"{PREFIX}_udm_requests",
    "Number of requests sent to the UDM REST API",
    ["method", "model"],
)
UDM_RESPONSES = Counter(
    f"{PREFIX}_udm_responses",
    "Number of responses received from the UDM REST API by HTTP status code",
    ["method", "model", "status"],
)


def start_server(port: int, addr: str = "0.0.0.0") -> None:
    """
    start the HTTP server exposing the metrics in a background thread
    """
    start_http_server(port, addr=addr)
    logging.info("Serving Prometheus metrics on %s:%d", addr, port)


def record_run(sync_start_time: float, success: bool, models: dict):
    """
    publish the result of a finished sync run

    A run is successful if it was not aborted by an exception, errors when
    processing single source entries are counted in `models` instead.
    `models` maps UDMModel to ModelStats and contains only the models which
    were synced completely, models not reached in an aborted run have no
    values afterwards.
    """
    now = time.time()
    previous = LAST_RUN.snapshot
    if success:
        last_success_at = now
    elif previous is not None:
        last_success_at = previous.last_success_at
    else:
        last_success_at = None
    LAST_RUN.publish(
        RunSnapshot(
            success=success,
            finished_at=now,
            duration=now - sync_start_time,
            last_success_at=last_success_at,
            models={model.value: stats for model, stats in models.items()},
        ),
    )
    RUNS.labels("success" if success else "failed").inc()
