# Full Spectrum Player Value (FSPV) — SkillCorner Basketball Analytics Cup

[![CI](https://github.com/carlosvinicius-ai/opendata-basketball/actions/workflows/ci.yml/badge.svg)](https://github.com/carlosvinicius-ai/opendata-basketball/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Architecture: Clean Architecture](https://img.shields.io/badge/architecture-Clean%20Architecture-emerald.svg)](#architecture)
[![Coverage: 85%](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](#testing--validation)
[![Zero-Leakage Guard](https://img.shields.io/badge/data%20leakage-0%20leaked%20features-success.svg)](#zero-data-leakage-guarantee)
[![License: MIT](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

> **Official Entry for the SkillCorner Open Data Basketball Cup (Liga ACB 2025/2026)**  
> An end-to-end analytical framework unifying **Ball Action Value (BAV)** on-ball decision modeling with **Space Creation Index (SCI)** geometric graph neural representations into a standardized **Full Spectrum Player Value (FSPV)** metric.

---

## 🏀 Executive Summary & Key Results

Modern basketball analytics has long suffered from terminal-event bias: rewarding the player taking the shot or recording the assist, while undervaluing both the sequential decision-making that broke down the defense on-ball and the off-ball spatial gravity that opened the lane.

**Full Spectrum Player Value (FSPV)** decouples player contribution into two orthogonal, complementary pillars:
1. **Ball Action Value (BAV):** A calibrated probabilistic state-space model (XGBoost) tracking the shift in possession scoring expectation $\Delta P(\text{score})$ across 15,087 micro-actions (`TOUCH`, `PASS`, `SHOT`, `PICK`, `DRIVE`, `DRIBBLE`).
2. **Space Creation Index (SCI):** An inductive Graph Neural Network (GraphSAGE) operating on 11-node spatial proximity graphs, capturing player gravity, defensive distortion, and Voronoi court dominance via *Input $\times$ Gradient* sensitivity saliency.

$$\text{FSPV}(p) = 0.5 \cdot \text{BAV}_z(p) + 0.5 \cdot \text{SCI}_z(p)$$

### 🏆 Top 5 Liga ACB Performers (Face Validity Audit)

| Rank | Player | Team | BAV ($z$) | SCI ($z$) | FSPV Score | FSPV Percentile | Archetype |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| **1** | **Markus Howard** | Bitci Baskonia | **+1.73** | **+2.72** | **+2.22** | **100.0%** | **Dual-Threat Star:** EuroLeague top scorer. Generates extreme off-ball gravity while maintaining lethal on-ball shot-making. |
| **2** | **Loucas Nzambi Maniema** | Dreamland Gran Canaria | **+3.97** | **0.00** | **+1.98** | **99.5%** | **On-Ball Finisher:** Dominant interior conversion and drive efficiency on high-leverage touches. |
| **3** | **Derek Ryan Needham** | Basquet Girona | **+0.64** | **+2.39** | **+1.51** | **99.0%** | **Floor General & Spacing Anchor:** Veteran playmaker whose court geometry optimization stretches opposing defenses. |
| **4** | **Patty Mills** | Lenovo Tenerife | **+0.89** | **+1.90** | **+1.39** | **98.5%** | **Off-Ball Motion Specialist:** NBA champion renowned for elite relocation, constant perimeter movement, and catch-and-shoot execution. |
| **5** | **Sayon Keita** | BC Barcelona | **+2.41** | **0.00** | **+1.21** | **98.0%** | **Interior Hub:** High-efficiency paint scoring and rim gravity in Barcelona's half-court offensive sets. |

---

## 📊 Interactive HTML5 Dashboard

The presentation layer generates a zero-backend, standalone HTML5 report with embedded interactive charts, tactical quadrants, and an instant filterable leaderboard:

- 📄 **Standalone Report:** [`reports/full_spectrum_player_value.html`](reports/full_spectrum_player_value.html)
- 🖥️ **Scout-Friendly:** Runs in any modern web browser via `file://` with no Node, Flask, or backend server required.
- 🔍 **Interactive Features:**
  - Dynamic tactical quadrant scatter plot (Chart.js)
  - Face Validity Top 5 audit cards with tactical justification
  - Instant text search across player names, teams, and positions
  - Base64 inline embedded radar charts and percentile distributions

---

## 🏗️ Architecture: Clean Architecture

The codebase strictly adheres to Uncle Bob's **Clean Architecture** principles across four isolated layers:

```
src/
├── domain/            # ZERO external dependencies (stdlib only: math, dataclasses, enum)
│   ├── constants.py   # Court dimensions, tracking frequency (25 fps), random seeds
│   ├── entities.py    # Player, Game, Chance, Action, PlayerValue
│   ├── value_objects.py # CourtCoordinate, TimeWindow, ShotRegion, ActionType
│   └── protocols.py   # ITrackingLoader, IEventLoader, IModelTrainer, IPlayerValueCombiner
├── use_cases/         # Application business rules & statistical pipelines (85% test coverage)
│   ├── bav/           # ActionSequencer, StateExtractor, BAVModel, BAVScorer, SHAPExplainer
│   ├── sci/           # GraphDatasetBuilder, GNNModel (GraphSAGE), SCICalculator, SpaceOwnership
│   └── player_value/  # Normalizer (per-possession z-scores), Combiner, Validator
├── infrastructure/    # Concrete I/O adapters & data ingestion
│   ├── event_loader.py    # Ingestion of 20 SkillCorner dynamic event tables
│   ├── tracking_loader.py # Streaming gzipped JSONL reader with frame-level filtering
│   ├── alias_resolver.py  # Canonical player deduplication
│   ├── graph_builder.py   # Spatial proximity ε-ball graph construction
│   └── aggregate_loader.py# 293-game season aggregates loader (for external validation)
└── presentation/      # CLI and standalone report generation
    ├── cli.py             # Modular subcommands: run-bav, run-sci, run-all, build-report
    ├── report_builder.py  # Standalone HTML5 dashboard generator
    └── charts_generator.py# Static radar and dotplot asset visualizer
```

### Architectural Guardrails:
- `domain/` has **zero external imports** (strictly enforced via static AST testing).
- `presentation/` **never imports from domain directly**; all interactions are mediated through `use_cases/` and `infrastructure/`.
- Core predictive models **never import season aggregate CSVs** (zero-leakage guaranteed).

---

## 🚀 Quickstart & Reproduction Guide

### 1. Prerequisites & Environment Setup
- Python 3.12+
- Recommended: Virtual environment

```powershell
# Clone repository
git clone https://github.com/carlosvinicius-ai/opendata-basketball.git
cd opendata-basketball

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows (or: source venv/bin/activate on Linux/macOS)

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### 2. End-to-End Execution (Single Command)
To run the full pipeline (BAV training + SCI GNN training + FSPV synthesis + External Validation + HTML Dashboard generation):

```powershell
python -m presentation.cli run-all --max-chances 10 --epochs 5
```

### 3. Modular Commands
You can also run pipeline components individually:

```powershell
# 1. Run Ball Action Value (BAV) pipeline
python -m presentation.cli run-bav

# 2. Run Space Creation Index (SCI) GNN pipeline
python -m presentation.cli run-sci --epochs 10 --max-chances 15

# 3. Build standalone HTML5 report only
python -m presentation.cli build-report --output reports/full_spectrum_player_value.html
```

---

## 🧪 Testing & Validation

### Automated Test Suite
The repository includes a comprehensive test suite of **64 automated tests** covering all layers:

```powershell
# Run full test suite with code coverage on use_cases
pytest tests/ --cov=src/use_cases --cov-report=term-missing

# Run strict code linting with Ruff
ruff check src/ tests/

# Run data leakage assertion guards
pytest tests/use_cases/test_leakage.py -v
```

### Validation Benchmark Summary

| Dimension | Target (ADR 0005) | Measured Value | Evaluation |
|---|---|---|---|
| **BAV Brier Score** | $< 0.25$ | **0.2423** | **PASS** (Calibrated on holdout games 188630 & 191313) |
| **BAV Actions Evaluated** | $\ge 10,000$ | **15,087 actions** | **PASS** |
| **SCI Spatial Graphs** | $\ge 50$ | **100 chance graphs** | **PASS** |
| **Spearman $\rho$ vs. Season Shots** | $> 0.10$ | **$\rho = +0.141$ ($p = 0.042$)** | **PASS** (Statistically significant) |
| **Code Coverage (`src/use_cases/`)** | $\ge 70\%$ | **85%** | **PASS** (64 passing tests) |
| **Linter Compliance (`ruff`)** | 0 errors | **0 errors / warnings** | **PASS** |

See [`docs/VALIDATION_RESULTS.md`](docs/VALIDATION_RESULTS.md) for full calibration tables, confusion matrices, and detailed statistical methodology.

---

## 🔒 Zero Data Leakage Guarantee

In accordance with **ADR 0005**:
1. **Feature Separation:** None of the 28 predictive features in BAV or node features in SCI overlap with the 293-game season aggregates (`acb_shotsaggregates_20252026.csv`, etc.).
2. **AST Static Analysis:** Automated tests in [`tests/use_cases/test_leakage.py`](tests/use_cases/test_leakage.py) verify via abstract syntax tree inspection that no predictive module imports `aggregate_loader`.
3. **Post-Hoc Benchmarking:** Aggregates are accessed exclusively by `src/use_cases/player_value/validator.py` *after* FSPV rankings have been generated independently from the 10-game sample.

---

## 📚 Technical Specifications & ADRs

- 📐 **[docs/SPEC.md](docs/SPEC.md):** Complete mathematical specification (probability state transitions, GraphSAGE aggregation, Input $\times$ Gradient saliency, Voronoi area weighting).
- ⚠️ **[docs/LIMITATIONS.md](docs/LIMITATIONS.md):** Analytical constraints, tracking extrapolation (~17-24%), sample size considerations, and open-source roadmap.
- 📋 **[docs/VALIDATION_RESULTS.md](docs/VALIDATION_RESULTS.md):** Full validation report with calibration curves and face validity assessment.
- 🏛️ **Architecture Decision Records (ADRs):**
  - [ADR 0001: Analytical Framework: BAV + SCI](docs/adr/0001-analytical-framework-bav-sci.md)
  - [ADR 0002: Spatial Engine Selection](docs/adr/0002-spatial-engine-selection.md)
  - [ADR 0003: GNN Framework: GraphSAGE](docs/adr/0003-gnn-framework-selection.md)
  - [ADR 0004: Data Pipeline Architecture](docs/adr/0004-data-pipeline-architecture.md)
  - [ADR 0005: Validation Strategy](docs/adr/0005-validation-strategy.md)

---

## 📖 Citations & Acknowledgments

This research builds upon foundational sports analytics literature:

```bibtex
@inproceedings{decroos2019vaep,
  title={Actions Speak Louder than Goals: Valuing Player Actions in Soccer},
  author={Decroos, Tom and Bransen, Lotte and Van Haaren, Jan and Davis, Jesse},
  booktitle={Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining},
  pages={1851--1861},
  year={2019}
}

@article{hamilton2017graphsage,
  title={Inductive Representation Learning on Large Graphs},
  author={Hamilton, William L and Ying, Rex and Leskovec, Jure},
  journal={Advances in Neural Information Processing Systems (NeurIPS)},
  volume={30},
  year={2017}
}

@misc{skillcorner2026opendata,
  author={SkillCorner},
  title={SkillCorner Open Data: Basketball (Liga Endesa ACB 2025-2026)},
  year={2026},
  url={https://github.com/SkillCorner/opendata-basketball}
}
```

Special acknowledgment to the maintainers of `floodlight`, `unravelsports`, `mplbasketball`, and `skillcornerviz` for their spatial tracking utilities.

---

## 📄 License

This repository is distributed under the MIT License. See [LICENSE](LICENSE) for details.
