from sentinelflow.observability.metrics import Metrics


def test_metrics_render_prometheus_metadata_and_labels() -> None:
    metrics = Metrics()
    metrics.set_model_ready(True)
    metrics.record_prediction("approve", "v1", 0.01)
    metrics.record_http(
        method="POST",
        path="/v1/risk-score",
        status_code=200,
        duration=0.02,
    )
    output = metrics.render_prometheus()
    assert "# HELP sentinelflow_predictions_total" in output
    assert 'sentinelflow_predictions_total{decision="approve",model_version="v1"} 1.0' in output
    assert "sentinelflow_model_ready 1.0" in output
    assert 'status_code="200"' in output
