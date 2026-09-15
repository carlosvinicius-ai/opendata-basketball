# ADR 0006 — Feature Engineering Strategy: Static Gradient-Boosted vs. Temporal Sequential BAV

**Date:** 2026-09-15  
**Status:** Accepted  
**Deciders:** Project Team  
**Layer:** `use_cases/bav`  

---

## Context

In valuing sequential basketball actions within a chance (possession), two dominant machine learning paradigms exist:
1. **Markovian / State-Transition Decision Trees (e.g., XGBoost / CatBoost):** The state $S_i$ is explicitly parameterized as a feature vector containing spatial, kinematic, and historical context features (e.g., current action type, predecessor action type, elapsed time, ball speed, nearest defender distance).
2. **Recurrent / Attention-Based Deep Sequence Models (e.g., LSTM, GRU, Transformers):** The sequence of actions $(a_1, a_2, \dots, a_i)$ is fed as a variable-length token/vector sequence to capture arbitrary long-range temporal dependencies.

We must evaluate which approach maximizes **Methodology**, **Model Interpretability (SHAP)**, and **Sample Efficiency** within the constraints of the 10-game dataset.

---

## Evaluation of Alternatives

| Criteria | XGBoost with Contextual Feature Engineering | Sequence Deep Learning (LSTM / Transformer) |
|---|---|---|
| **Sample Efficiency (10 games)** | **High:** 15,087 tabular actions provide strong, non-overfitting training data with gradient regularization. | **Low:** Deep sequence models are prone to overfitting on small match splits (8 train / 2 test). |
| **Model Explainability** | **High:** Exact Shapley Additive Explanations (TreeExplainer) decomposed per feature and per action. | **Low / Approximate:** Integrated Gradients or attention weights, which can be noisy and less intuitive for coaches/scouts. |
| **Computational Footprint** | **Minimal:** Trains in seconds on standard CPU; trivial CI integration. | **Heavy:** Requires PyTorch sequence padding, batching, GPU tuning. |
| **Handling Action Granularity** | **Flexible:** Seamlessly integrates spatial distances, FIBA zone one-hots, and predecessor lag features. | **Complex:** Requires heterogeneous embedding layers for discrete action types combined with continuous spatial coordinates. |

---

## Decision

**We adopt XGBoost with Lagged Contextual Feature Engineering as the primary BAV model.**

Key Architectural Decisions:
1. **First-Order Temporal Memory:** We engineer lagged state features ($a_{i-1}$ type, time elapsed since $a_{i-1}$, spatial vector displacement) directly into the feature matrix $\mathbf{x}_i \in \mathbb{R}^{28}$, capturing sequential Markovian context without deep sequence overhead.
2. **Deterministic Prior ($P_0$):** We anchor the initial state expectation at empirical chance start ($P_0 \approx 0.482$), establishing a mathematically sound baseline.
3. **Future Extension Roadmap:** Deep sequence architectures (such as Transformer encoder over possession tokens) are retained as a designated future research track when full-season broadcast tracking (>100 games) becomes available.

---

## Consequences

- **Positive:** Guaranteed calibration (Brier Score $< 0.25$), instant execution in CLI, 100% test reproducibility, and exact SHAP tree explanations.
- **Trade-off:** Very long-range dependencies (e.g., action 1 affecting action 8) are summarized through possession-level aggregates rather than learned internal hidden states.
