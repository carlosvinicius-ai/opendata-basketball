# Analytical & Practical Limitations

> **Project:** Full Spectrum Player Value (FSPV)  
> **Dataset:** SkillCorner Basketball Open Data — Liga ACB 2025/2026  
> **Document Status:** Accepted  

---

## 1. Sample Size Constraints (10 Games vs. Full Season)

- **Dataset Scope:** The granular broadcast tracking and dynamic events dataset provided covers **10 games** (totaling ~15,087 sequenced on-ball actions and hundreds of offensive chances). While rich in micro-actions, this sample represents approximately **3.4%** of the 293 total regular season and playoff games.
- **Analytical Impact:** Individual player ratings (especially for rotational or bench players with low minutes) may exhibit high variance due to small possession counts. Although possession normalization (BAV per possession) and z-scoring mitigate minute disparities, full-season stability requires broader tracking ingestion.
- **External Benchmarking:** The external validation against the 293-game aggregate CSVs (`shots`, `picks`, `drives`) provides macro-level confirmation ($ho = +0.141$ vs. `points_per_shot`), but cannot fully substitute for 293 games of granular frame tracking.

---

## 2. Broadcast Tracking Extrapolation & Camera Occlusion

- **Broadcast Vision Constraints:** Unlike dedicated multi-camera in-stadium optical systems (such as Second Spectrum or Hawk-Eye), broadcast tracking is captured from the single main TV broadcast camera.
- **Extrapolation Rate:** Across the 10 sample games, approximately **17% to 24%** of player frame positions are flagged as extrapolated (`is_extrapolated = True`). This occurs during close-up replays, director cutaways, rapid full-court transition sprints where trailing players are out of frame, and heavy paint scrums where player IDs are briefly occluded.
- **Methodological Mitigation:** 
  1. Centroid spatial aggregation was used for chance-level graph node features ($ar{x}_v, ar{y}_v$), smoothing out single-frame jitter.
  2. BAV state extraction bounds coordinate distances to the active playing court and skips non-tracking possessions gracefully.

---

## 3. Graph Neural Network (GNN) Sample Dynamics

- **Graph Dataset Size:** The inductive GraphSAGE GNN was trained on **100 sampled chance spatial graphs** (balanced across 10 games).
- **Overfitting Risk:** In deep learning on non-Euclidean geometries, small graph datasets can lead to representation collapse or memorization of specific team spacing schemes. 
- **Architectural Safeguards:** We implemented:
  1. A compact 2-layer GraphSAGE architecture with low hidden dimensionality ($D = 32$).
  2. Strong dropout ($p = 0.20$) and weight decay ($L_2 = 1e-4$).
  3. Inductive neighborhood sampling rather than transductive full-graph learning.

---

## 4. Scope of On-Ball vs. Off-Ball Representation

- **BAV Scope:** BAV explicitly evaluates discrete on-ball micro-actions (`TOUCH`, `PASS`, `SHOT`, `PICK`, `DRIVE`, `DRIBBLE`). It does not directly attribute value to off-ball cuts or flare screens that do not culminate in a ball touch.
- **SCI Complementarity:** SCI addresses this gap by measuring spatial gravity via node sensitivity saliency ($Input \times Gradient$) and Voronoi area dominance. However, SCI cannot quantify intangible actions like vocal defensive communication, screening legality, or tactical decoy intent.
- **Synthesis Balance:** The default equal weighting $\alpha = 0.5$ balances on-ball efficiency with spacing gravity, but custom weightings (e.g., $\alpha = 0.7$ for primary ball-handlers or $\alpha = 0.3$ for spot-up wings) may be appropriate depending on the scout's specific tactical inquiry.

---

## 5. Roadmap & Recommendations for Future Open-Source Extensions

1. **Full-Season Tracking Pipeline:** If SkillCorner releases broadcast tracking for additional ACB matches, the modular architecture permits immediate batch ingestion with zero code modifications.
2. **Temporal Sequence Models:** Exploring Graph Temporal Networks (GCRN / Spatio-Temporal Graph Transformers) to model continuous trajectory dynamics rather than chance-level centroid snapshots.
3. **Defensive Value Inversion:** Inverting BAV to compute *Defensive Action Value (DAV)*, measuring how individual defenders suppress offensive scoring expectation.
