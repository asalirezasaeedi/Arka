# DGP++ v3.0

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Deps](https://img.shields.io/badge/deps-numpy%20%7C%20pandas%20%7C%20pyarrow-green)
![License](https://img.shields.io/badge/license-MIT-black)
![Gate-0](https://img.shields.io/badge/Gate--0-SV%20DDC%20AES%20DI%20TPI-purple)

DGP++ v3.0 is a single-file, importable synthetic data engine for multi-manifold non-stationary benchmarks. It combines a clean MSB → TAE → IGE research pipeline with episode-based Ornstein-Uhlenbeck dynamics, active skew-symmetric theta rotations, cross-manifold coupling, real streaming, reproducible splits, vectorized Gate-0 metrics, and seven use-case adapters for anomaly, drift, causal, federated, RL, streaming, and benchmark datasets.

## Architecture

```text
+------------------+    +----------------------+    +---------------------+    +------------------+
| MSB              | -> | TAE                  | -> | IGE                 | -> | Adapters UC1-UC7 |
| centers, tau,    |    | OU dynamics, theta,  |    | y_obs + x0..xN,     |    | labels, clients, |
| horizons, theta, |    | coupling, shocks,    |    | z clipping, single  |    | actions, stream  |
| coupling matrix  |    | center drift         |    | latent path         |    | metadata         |
+------------------+    +----------------------+    +---------------------+    +------------------+
                                     |
                                     v
                         blind / semi / analysis views
                                     |
                                     v
                         Gate-0: SV, DDC, AES, DI, TPI
```

## Install

```bash
pip install .
pip install -r requirements.txt
```

## Quick start

```python
from dgp_plus_plus import BenchmarkSuite, GeneratorConfig, MultiManifoldGenerator
config = GeneratorConfig(n_samples=128, episodes=2, seed=7)
result = MultiManifoldGenerator(config).generate(BenchmarkSuite())
print(result.verdict)
print(result.metrics["SV"], result.metrics["DDC"])
```

## CLI reference

| Command | Purpose | Example |
| --- | --- | --- |
| `generate` | Generate blind/semi/analysis artifacts | `dgp-plus-plus generate --adapter benchmark --dashboard` |
| `gate0` | Run default Gate-0 validation | `dgp-plus-plus gate0` |
| `validate` | Validate a saved analysis CSV/Parquet | `dgp-plus-plus validate artifacts/outputs/analysis_x.csv` |
| `adapters` | List adapters | `dgp-plus-plus adapters` |
| `menu` | Print use-case menu | `dgp-plus-plus menu` |
| `anomaly` | Run UC1 shortcut | `dgp-plus-plus anomaly` |
| `drift` | Run UC2 shortcut | `dgp-plus-plus drift` |
| `causal` | Run UC3 shortcut | `dgp-plus-plus causal` |
| `federated` | Run UC4 shortcut | `dgp-plus-plus federated` |
| `rl` | Run UC5 shortcut | `dgp-plus-plus rl` |
| `stream` | Run UC6 shortcut | `dgp-plus-plus stream` |
| `benchmark` | Print benchmark grid and run UC7 | `dgp-plus-plus benchmark` |

## Use cases

| UC | Adapter | Generates | Algorithms that need it |
| --- | --- | --- | --- |
| UC1 | `AnomalyAdapter` | point, contextual, collective anomaly labels | isolation forest, autoencoders, robust forecasting |
| UC2 | `DriftAdapter` | regime and drift score annotations | drift detectors, online learners |
| UC3 | `CausalDataset` | propensity, treatment, CATE, outcome | causal forests, doubly robust estimators |
| UC4 | `FederatedDataset` | Dirichlet non-IID client partitions | federated averaging, personalization |
| UC5 | `ManifoldEnv` | action, reward, done transitions | offline RL and contextual bandits |
| UC6 | `StreamingGenerator` | event time, watermark, batches | streaming learners and online monitoring |
| UC7 | `BenchmarkSuite` | labels, difficulty, grid table | classifier and representation benchmarks |

## Gate-0 metric definitions

Let `C_t^k` be manifold center `k` at time `t`, `y_t` the observation, and `z_t` the latent path.

- **SV**: separation volatility, `std_t(mean_{i<j} ||C_t^i-C_t^j||) / mean_t(mean_{i<j} ||C_t^i-C_t^j||)` plus a minimum-separation violation rate.
- **DDC**: drift direction coherence, `(1 + mean cos(ΔC_t, ΔC_{t+1})) / 2`, with velocity gating.
- **AES**: attack effect score, `E[||y-z|| | shock] / E[||y-z|| | normal]`, reported with shock ratio.
- **DI**: normalized Shannon diversity, `H(manifold_id) / log(K)`.
- **TPI**: temporal predictability index, mean absolute lag-one autocorrelation of episode observations.

## Calibration

| Parameter | Effect | Recommended range |
| --- | --- | --- |
| `n_samples` | temporal resolution per episode | 128–10,000 |
| `manifolds` | diversity and separation difficulty | 2–10 |
| `latent_dim` | hidden process complexity | 3–32 |
| `drift_scale` | non-stationarity and DDC difficulty | 0.001–0.02 |
| `shock_rate` | anomaly/attack density | 0.10–0.35 |
| `coupling` | cross-manifold transfer strength | 0.2–1.5 |
| `noise` | observation corruption | 0.01–0.20 |

## Citation

```bibtex
@software{dgp_plus_plus_2026,
  title = {DGP++ v3.0: Multi-Manifold Non-Stationary Data Generation},
  author = {DGP++ Authors},
  year = {2026},
  url = {https://example.com/dgp-plus-plus}
}
```

## DGP++ X platform layers

DGP++ X keeps the generator local and dependency-light while adding production/research platform layers that are relevant to synthetic intelligence workflows:

| Layer | Implemented component | Purpose |
| --- | --- | --- |
| Core Engine | `MultiManifoldGenerator` | MSB+/TAE+/IGE+ synthetic data generation |
| Dynamic Simulation | `tae`, `generate_episode`, `stream` | episode and streaming evolution |
| Manifold Intelligence | adaptive separation, theta, coupling matrix | multi-manifold latent state construction |
| Causal Engine | `CausalDataset`, `StatisticalMetrics.causal_validity` | treatment, propensity, CATE and validity checks |
| Streaming Engine | `StreamingGenerator`, `stream` | event-time and iterator/batch simulation |
| Federated Engine | `FederatedDataset` | Dirichlet non-IID client simulation |
| RL Environment | `ManifoldEnv` | offline RL transition generation |
| Benchmark Framework | `BenchmarkSuite`, `ExperimentManager.benchmark` | reproducible benchmark grid |
| Validation Framework | `Gate0Validator`, `StatisticalMetrics` | Gate-0 plus statistical, drift, causal and temporal checks |
| Experiment Manager | `ExperimentManager` | repeated seeded runs and result comparison |
| Artifact System | `ArtifactRegistry` | manifests and artifact audit trail |
| Observability | `ObservabilityLayer` | health, diagnostics and Prometheus text metrics |
| CLI Interface | `main` | generation, validation, calibration, diagnostics and benchmark commands |
| API Layer | `DGPXPlatform` | Python facade for platform workflows |
| Deployment Layer | `pyproject.toml`, `requirements.txt` | pip-installable local deployment |

## Additional CLI commands

| Command | Purpose |
| --- | --- |
| `dgp-plus-plus doctor` | Dependency/runtime health check |
| `dgp-plus-plus diagnostics` | Health plus same-seed reproducibility diagnostics |
| `dgp-plus-plus calibrate --adapter benchmark` | Autonomous generate → evaluate → adjust loop |
| `dgp-plus-plus experiment --name paper --repeats 3` | Repeated experiment with manifests |
| `dgp-plus-plus benchmark-run` | Execute the built-in benchmark grid |
| `dgp-plus-plus metrics --adapter benchmark` | Emit Prometheus-compatible text metrics |

## Engineering mission statement

DGP++ X exists to provide a reproducible, auditable and production-friendly synthetic intelligence platform for studying multi-manifold non-stationary data, causal effects, federated heterogeneity, offline RL transitions, streaming evolution and benchmark reliability without pulling in heavyweight UI or distributed consensus dependencies.

## Risk analysis and mitigations

| Risk | Mitigation |
| --- | --- |
| Numerical instability | hard z-clipping, bounded propensities, local RNG and validation checks |
| Unrealistic benchmark assumptions | explicit metadata, multiple adapters and documented calibration knobs |
| Invalid causal conclusions | CATE/probensity output plus causal validity checks |
| Poor reproducibility | seed-only local RNG and same-seed diagnostics |
| Artifact ambiguity | manifest files include config, metrics, verdict and saved paths |
| Dependency explosion | limited runtime dependencies: numpy, pandas and pyarrow |
