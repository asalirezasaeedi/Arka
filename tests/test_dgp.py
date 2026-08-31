import numpy as np
import pytest

from dgp_plus_plus import (
    AnomalyAdapter,
    BenchmarkSuite,
    CausalDataset,
    FederatedDataset,
    Gate0Validator,
    GeneratorConfig,
    MultiManifoldGenerator,
    StreamingGenerator,
    split_views,
)


def small_config(**kwargs):
    base = dict(n_samples=64, n_features=5, latent_dim=5, manifolds=3, episodes=2, seed=123)
    base.update(kwargs)
    return GeneratorConfig(**base)


def test_config_validation():
    with pytest.raises(ValueError):
        GeneratorConfig(n_samples=1).validate()
    small_config().validate()


def test_msb_shape():
    gen = MultiManifoldGenerator(small_config())
    state = gen.msb()
    assert state["centers"].shape == (3, 5)
    assert state["thetas"].shape == (3, 5, 5)
    assert state["coupling"].shape == (3, 3)


def test_tae_determinism():
    cfg = small_config(seed=9)
    a = MultiManifoldGenerator(cfg).generate().analysis[["time", "manifold_id"]].to_string()
    b = MultiManifoldGenerator(cfg).generate().analysis[["time", "manifold_id"]].to_string()
    assert a == b


def test_ige_clip_bounds():
    result = MultiManifoldGenerator(small_config()).generate()
    features = result.analysis[[c for c in result.analysis.columns if c.startswith("x")]].to_numpy()
    assert np.max(features) <= 10.0
    assert np.min(features) >= -10.0


def test_single_path_generation():
    result = MultiManifoldGenerator(small_config()).generate()
    assert len(result.analysis["z_true"]) == len(result.analysis["y_obs"])
    assert all(len(z) == small_config().latent_dim for z in result.analysis["z_true"])


def test_split_views_disjoint_columns():
    result = MultiManifoldGenerator(small_config()).generate()
    blind, semi, analysis = split_views(result.analysis)
    assert "z_true" not in blind.columns
    assert "z_true" not in semi.columns
    assert "z_true" in analysis.columns


def test_gate0_all_metrics_present():
    result = MultiManifoldGenerator(small_config()).generate()
    for key in ["SV", "DDC", "AES", "DI", "TPI"]:
        assert key in result.metrics


def test_anomaly_contamination_rate():
    result = MultiManifoldGenerator(small_config()).generate(AnomalyAdapter())
    rate = result.analysis["is_anomaly"].mean()
    assert 0.02 <= rate <= 0.12


def test_drift_annotation_count():
    result = MultiManifoldGenerator(small_config()).generate()
    out = __import__("dgp_plus_plus").DriftAdapter().apply(result.analysis, result.latent, result.manifold_id, np.random.default_rng(1))
    assert out["regime"].nunique() == 3


def test_causal_cate_range():
    result = MultiManifoldGenerator(small_config()).generate(CausalDataset())
    assert result.analysis["cate"].between(0.2, 3.0).all()


def test_federated_dirichlet_sum():
    adapter = FederatedDataset(clients=4, alpha=0.5)
    result = MultiManifoldGenerator(small_config()).generate(adapter)
    assert adapter.last_client_distribution is not None
    assert abs(float(adapter.last_client_distribution.sum()) - 1.0) < 1e-8
    assert result.analysis["client_id"].nunique() <= 4


def test_streaming_batch_shape():
    result = MultiManifoldGenerator(small_config()).generate(StreamingGenerator())
    batches = list(StreamingGenerator().batches(result.analysis, batch_size=10))
    assert len(batches[0]) == 10
    assert sum(len(b) for b in batches) == len(result.analysis)


def test_benchmark_grid_shape():
    grid = BenchmarkSuite.grid()
    assert grid.shape[0] == 9
    assert {"scenario", "manifolds", "drift_scale", "task"}.issubset(grid.columns)


def test_full_pipeline_smoke():
    result = MultiManifoldGenerator(small_config()).generate(BenchmarkSuite())
    metrics = Gate0Validator.evaluate(result.analysis, result.config)
    verdict = Gate0Validator.verdict(metrics)
    assert verdict in {"PASS", "FAIL"}

from dgp_plus_plus import (
    ArtifactRegistry,
    AutonomousCalibrationEngine,
    DGPXPlatform,
    ExperimentConfig,
    ExperimentManager,
    ObservabilityLayer,
    StatisticalMetrics,
)


def test_statistical_extension_metrics_present(tmp_path):
    result = MultiManifoldGenerator(small_config()).generate(CausalDataset())
    assert "mean_abs" in StatisticalMetrics.distribution_summary(result.analysis)
    assert "mean_shift" in StatisticalMetrics.distribution_drift(result.analysis)
    assert StatisticalMetrics.causal_validity(result.analysis)["available"] is True
    assert "speed_cv" in StatisticalMetrics.temporal_consistency(result.analysis)


def test_reproducibility_check_true():
    report = StatisticalMetrics.reproducibility_check(small_config(n_samples=32, episodes=1), "benchmark")
    assert report["same_seed_reproducible"] is True


def test_artifact_registry_manifest(tmp_path):
    result = MultiManifoldGenerator(small_config(n_samples=32, episodes=1)).generate(BenchmarkSuite())
    registry = ArtifactRegistry(str(tmp_path))
    manifest = registry.write_manifest(result, "unit")
    assert manifest.endswith("unit_manifest.json")
    assert manifest in registry.list_manifests()


def test_observability_prometheus_text():
    result = MultiManifoldGenerator(small_config(n_samples=32, episodes=1)).generate()
    text = ObservabilityLayer().prometheus_text(result)
    assert "dgp_info" in text
    assert "dgp_gate0_sv" in text


def test_calibration_loop_report():
    report = AutonomousCalibrationEngine(small_config(n_samples=32, episodes=1), max_iterations=2).run()
    assert "history" in report
    assert len(report["history"]) >= 1


def test_experiment_manager_runs(tmp_path):
    manager = ExperimentManager(ArtifactRegistry(str(tmp_path)))
    table = manager.run(ExperimentConfig("unit", small_config(n_samples=32, episodes=1), "benchmark", repeats=2))
    assert len(table) == 2
    assert {"SV", "DDC", "AES", "DI", "TPI"}.issubset(table.columns)


def test_platform_generate_manifest(tmp_path):
    platform = DGPXPlatform(str(tmp_path))
    summary = platform.generate(small_config(n_samples=32, episodes=1), "benchmark")
    assert "manifest" in summary
    assert summary["verdict"] in {"PASS", "FAIL"}
