from observability.health import HealthStatus
from observability.watchdogs import Watchdogs
from observability.metrics_exporter import MetricsExporter


def test_observability_components():
    health = HealthStatus()
    health.set("engine", "ok")
    assert health.snapshot()["engine"] == "ok"

    watchdog = Watchdogs(max_stale_seconds=1)
    watchdog.heartbeat("feed")
    assert watchdog.is_stale("feed") is False

    exporter = MetricsExporter()
    exporter.set_metric("orders", 1)
    rendered = exporter.render_prometheus()
    assert "orders" in rendered
