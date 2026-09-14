# Mathematical & Architectural Specification: Full Spectrum Player Value (FSPV)

> **Competition:** SkillCorner Basketball Analytics Cup (Liga ACB 2025/2026)  
> **Authors:** Advanced Analytics Team  
> **Framework:** Ball Action Value (BAV) + Space Creation Index (SCI)  
> **Specification Version:** 1.0.0  

---

## 1. Overview & Analytical Philosophy

Traditional basketball box score metrics (PTS, REB, AST) and possession statistics (Points Per Possession, Effective Field Goal Percentage) disproportionately credit the player who touches the ball at the terminal instant of an action (the shooter or assister). However, modern basketball is a dynamic, multi-agent spatial game governed by **gravity**, **spacing**, and **continuous decision-making**.

The **Full Spectrum Player Value (FSPV)** framework bridges this analytical gap by decoupling offensive value creation into two orthogonal, complementary dimensions:
1. **Ball Action Value (BAV):** Measures on-ball decision-making and shot/drive execution through a probabilistic state-space model tracking shifts in possession scoring expectation $\Delta P(\text{score})$.
2. **Space Creation Index (SCI):** Measures off-ball spatial gravity and defensive distortion through an inductive Graph Neural Network (GraphSAGE) with sensitivity saliency gradients.

$$\text{FSPV} = \alpha \cdot \text{BAV}_z + (1 - \alpha) \cdot \text{SCI}_z, \quad \alpha \in [0, 1]$$

---

## 2. Ball Action Value (BAV) Mathematical Formulation

### 2.1 State-Space Action Valuation (VAEP Adaptation)
Let a basketball chance $C$ consist of an ordered sequence of on-ball micro-actions:
$$A = (a_1, a_2, \dots, a_N), \quad a_i = (\tau_i, p_i, t_i, x_i, y_i)$$
where $\tau_i \in \{\text{TOUCH}, \text{PASS}, \text{SHOT}, \text{PICK}, \text{DRIVE}, \text{DRIBBLE}\}$ represents the action type, $p_i$ is the performing player, $t_i$ is the game clock / frame timestamp, and $(x_i, y_i)$ are the court coordinates.

Each action $a_i$ transitions the game from state $S_{i-1}$ to state $S_i$. The scoring probability after action $a_i$ is parameterized by a supervised gradient-boosted model:
$$P_i = P(\text{score} \mid S_i) \in [0, 1]$$

The net value of action $a_i$ to the offense is the marginal change in scoring expectation:
$$V(a_i) = P(\text{score} \mid S_i) - P(\text{score} \mid S_{i-1})$$

#### Boundary Conditions:
- For the initial action of a possession ($i = 1$):
  $$P_0 = P(\text{score} \mid S_0) = \mathbb{E}[\text{Scored} \mid \text{Chance Start}] \approx 0.482$$
- For a successful shot conversion ($a_N$ made):
  $$P(\text{score} \mid S_N) = 1.0 \implies V(a_N) = 1.0 - P_{N-1}$$
- For a turnover or missed shot without rebound:
  $$P(\text{score} \mid S_N) = 0.0 \implies V(a_N) = 0.0 - P_{N-1} < 0$$

### 2.2 State Representation Vector ($S_i$)
The feature vector $\mathbf{x}_i \in \mathbb{R}^{28}$ represents the spatial, temporal, and tactical context of state $S_i$:

1. **Spatial Coordinates:** Court position $(x_i, y_i)$, Euclidean distance to offensive basket:
   $$d_{\text{basket}} = \sqrt{(x_i - x_{\text{rim}})^2 + (y_i - y_{\text{rim}})^2}$$
   and azimuth angle $\theta_{\text{basket}} = \arctan2(y_i - y_{\text{rim}}, x_i - x_{\text{rim}})$.
2. **Shot Zone Categorization:** One-hot encoding of official FIBA regions (Restricted Area, Paint Non-RA, Mid-Range, Corner 3 Left/Right, Above the Break 3).
3. **Temporal Dynamics:** Sequence index within chance ($i$), duration of action ($\Delta t = t_i - t_{\text{start}}$), elapsed chance time.
4. **Action Hierarchy:** One-hot indicators for current and predecessor action types:
   $$\mathbf{1}_{\tau_i = \text{DRIVE}}, \mathbf{1}_{\tau_i = \text{PICK}}, \mathbf{1}_{\tau_i = \text{PASS}}, \dots$$
5. **Tracking Context:** Ball speed $\|\mathbf{v}_{\text{ball}}\|_2$, instantaneous acceleration, nearest defender Euclidean distance $d_{\text{def}}$, and defender velocity vector.

### 2.3 Model Architecture & Training Objective
- **Algorithm:** XGBoost Decision Trees (`XGBClassifier`).
- **Loss Function:** Binary Cross-Entropy with Log Loss:
  $$\mathcal{L}(\theta) = -\frac{1}{M} \sum_{m=1}^M \left[ y_m \log(\hat{p}_m) + (1 - y_m) \log(1 - \hat{p}_m) \right] + \Omega(\theta)$$
  where $\Omega(\theta) = \gamma T + \frac{1}{2}\lambda \sum_{j=1}^T w_j^2$ enforces regularization.
- **Hyperparameters:** $T=150$ trees, maximum depth $D=4$, learning rate $\eta=0.05$, sub-sample ratio $0.8$.
- **Model Explainability:** Shapley Additive Explanations (SHAP TreeExplainer):
  $$V(a_i) - \mathbb{E}[V] = \sum_{k=1}^K \phi_k(a_i)$$

---

## 3. Space Creation Index (SCI) Mathematical Formulation

### 3.1 Dynamic Spatial Graph Construction ($G$)
For each offensive chance $C$, player tracking data over the active frame window $[f_{\text{start}}, f_{\text{end}}]$ is mapped to a geometric proximity graph:
$$G = (V, E, \mathbf{X}, \mathbf{A})$$

- **Node Set ($V$):** $|V| = 11$ nodes representing 5 offensive players, 5 defenders, and the basketball.
- **Node Feature Matrix ($\mathbf{X} \in \mathbb{R}^{11 \times 4}$):**
  $$\mathbf{x}_v = \begin{bmatrix} \bar{x}_v & \bar{y}_v & \bar{s}_v & b_v \end{bmatrix}^T$$
  where $(\bar{x}_v, \bar{y}_v)$ is the centroid position across the chance, $\bar{s}_v = \frac{1}{T}\sum_{t=1}^T \|\mathbf{v}_v(t)\|_2$ is the mean movement speed, and $b_v \in \{0, 1\}$ indicates whether node $v$ represents the ball.
- **Edge Set ($E$ & Adjacency $\mathbf{A}$):** Proximity graph with cutoff radius $\varepsilon = 5.0\text{ m}$:
  $$e_{uv} \in E \iff \|(\bar{x}_u, \bar{y}_u) - (\bar{x}_v, \bar{y}_v)\|_2 \le 5.0$$

### 3.2 GraphSAGE Inductive Neighborhood Aggregation
Information propagates through local neighborhoods using a 2-layer GraphSAGE architecture:

$$\mathbf{h}_{\mathcal{N}(v)}^{(k)} = \text{Mean}\left( \left\{ \mathbf{h}_u^{(k-1)}, \forall u \in \mathcal{N}(v) \right\} \right)$$
$$\mathbf{h}_v^{(k)} = \text{ReLU}\left( \mathbf{W}^{(k)} \cdot \left[ \mathbf{h}_v^{(k-1)} \parallel \mathbf{h}_{\mathcal{N}(v)}^{(k)} \right] \right)$$

for layers $k \in \{1, 2\}$, where $\mathbf{h}_v^{(0)} = \mathbf{x}_v$, $\mathbf{W}^{(1)} \in \mathbb{R}^{32 \times 8}$, $\mathbf{W}^{(2)} \in \mathbb{R}^{32 \times 64}$.

### 3.3 Graph Readout & Chance Scoring Estimation
Graph-level representation is pooled via global permutation-invariant mean pooling:
$$\mathbf{h}_G = \frac{1}{|V|} \sum_{v \in V} \mathbf{h}_v^{(2)} \in \mathbb{R}^{32}$$
$$\hat{y}_G = \sigma\left( \mathbf{w}_{\text{out}}^T \mathbf{h}_G + b_{\text{out}} \right) = P(\text{Score} \mid G)$$

### 3.4 Saliency Node Attribution (Input $\times$ Gradient)
To determine each player’s marginal spatial contribution to the predicted scoring chance, we compute the sensitivity gradient of the output probability with respect to node features:
$$\nabla_{\mathbf{x}_v} \hat{y}_G = \frac{\partial \hat{y}_G}{\partial \mathbf{x}_v}$$
$$\text{Attr}(v) = \left( \nabla_{\mathbf{x}_v} \hat{y}_G \odot \mathbf{x}_v \right) \cdot \mathbf{1}$$

### 3.5 Voronoi Space Ownership Weighting
Player spatial dominance is bounded by official FIBA court dimensions ($28.0\text{ m} \times 15.0\text{ m}$):
$$\mathcal{V}(p_i) = \left\{ \mathbf{x} \in \Omega_{\text{court}} \mid \|\mathbf{x} - \mathbf{r}_i\|_2 < \|\mathbf{x} - \mathbf{r}_j\|_2, \forall j \neq i \right\}$$
$$\text{Area}(p_i) = \iint_{\mathcal{V}(p_i)} \frac{1}{1 + 0.1 \cdot d(\mathbf{u}, \text{rim})} \, d\mathbf{u}$$

---

## 4. Full Spectrum Player Value (FSPV) Metric Synthesis

### 4.1 Per-Possession Standardization
To prevent bias toward high-pace teams or garbage-time minutes, raw BAV and SCI totals are scaled by played possessions:
$$\text{BAV}_{\text{poss}}(p) = \frac{\sum_{a \in A_p} V(a)}{\text{PossessionsPlayed}(p)}$$
$$\text{SCI}_{\text{poss}}(p) = \frac{1}{|C_p|} \sum_{c \in C_p} \text{Attr}_c(p)$$

### 4.2 Standardized Z-Scores
Both metrics are projected onto standard normal distributions across the player cohort:
$$\text{BAV}_z(p) = \frac{\text{BAV}_{\text{poss}}(p) - \mu_{\text{BAV}}}{\sigma_{\text{BAV}}}$$
$$\text{SCI}_z(p) = \frac{\text{SCI}_{\text{poss}}(p) - \mu_{\text{SCI}}}{\sigma_{\text{SCI}}}$$

### 4.3 Composite Score & Percentile Rank
$$\text{FSPV}(p) = \alpha \cdot \text{BAV}_z(p) + (1 - \alpha) \cdot \text{SCI}_z(p), \quad \alpha = 0.5$$
$$\text{Percentile}(p) = 100 \times \frac{N - \text{Rank}(p) + 1}{N}$$

---

## 5. Summary of Mathematical Symbols

| Symbol | Definition | Domain / Units |
|---|---|---|
| $C, A$ | Chance and action sequence | Relational event structures |
| $a_i, \tau_i$ | Action instance and action type | $\tau \in \{\text{TOUCH, PASS, SHOT, PICK, DRIVE, DRIBBLE}\}$ |
| $S_i$ | Observable game state vector | $\mathbb{R}^{28}$ |
| $P_i$ | Scoring expectation $P(\text{score} \mid S_i)$ | $[0, 1]$ |
| $V(a_i)$ | Ball Action Value of action $a_i$ | Expected Points $(\Delta P)$ |
| $G = (V, E)$ | Dynamic chance spatial graph | $|V| = 11, e_{uv} \iff d \le 5.0\text{ m}$ |
| $\mathbf{x}_v$ | Node feature vector | $[ar{x}, \bar{y}, \bar{s}, b]^T \in \mathbb{R}^4$ |
| $\mathbf{h}_v^{(k)}$ | Layer $k$ node embedding in GraphSAGE | $\mathbb{R}^{32}$ |
| $\text{Attr}(v)$ | Sensitivity attribution (Input $\times$ Gradient) | Arbitrary units |
| $\text{FSPV}$ | Full Spectrum Player Value combined metric | Z-score (Mean=0, Std=1) |
