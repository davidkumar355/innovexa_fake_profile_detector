# Innovexa: Research & System Memory Context
**Paper Title:** *INNOVEXA: Fake Profile Detection Using GNN*  
**Affiliation:** Department of Computer Science & Engineering – Data Science (CSE-DS), ABES Engineering College, Ghaziabad, India  
**Authors:**
- **Krishnkant** (`Krishnkant.24b15410160@abes.ac.in`)
- **Harshit Singh Chahar** (`Harshitsinghchahar.24b154084@abes.ac.in`)
- **Khushi Upadhyay** (`khushiupadhyay.24b15410099@abes.ac.in`)
- **Hemant Chaubey** (`HemantChaubey@abes.ac.in`)

---

## 1. Executive Summary & Research Motivation

Online Social Networks (OSNs) continuously generate multimodal data comprising user profiles, follower–following dynamics, activity histories, and interaction graphs. Detecting fake accounts, bots, and Sybil profiles is increasingly difficult because modern malicious actors:
1. **Mimic genuine user metadata:** Fabricate realistic profile bios, profile pictures, posting frequencies, and activity schedules (*Feature Mimicking*).
2. **Execute relation camouflage:** Strategically follow, like, or interact with legitimate, verified, or high-reputation accounts to conceal suspicious structures (*Relation Camouflage*).
3. **Operate in coordinated rings:** Coordinate actions across botnets or Sybil clusters where individual accounts appear benign in isolation but exhibit collective malicious patterns.

**Core Thesis of Innovexa:**  
Traditional machine learning classifiers (Logistic Regression, Support Vector Machines, Random Forest, Multi-Layer Perceptrons) process accounts as independent, isolated feature vectors. They fail to capture relational topology and multi-hop neighborhood dynamics.  
**Innovexa** models the social network as an attributed graph $G = (V, E, X)$ and leverages **Graph Neural Networks (GNNs)** (GCN, GraphSAGE, GAT) with multi-hop message-passing to fuse account-level behavioral features with structural network topology for resilient, adversarial-aware fake profile detection.

---

## 2. Core Technical Challenges & Research Gaps

| Challenge | Nature & Impact on Detection | Innovexa Solution Strategy |
|---|---|---|
| **Feature Mimicking** | Fake accounts construct legitimate-looking metadata (bios, avatars, post cadence). Metadata-only classifiers fail. | Augment node attributes with multi-hop neighborhood aggregation. |
| **Relation Camouflage** | Malicious users create artificial edges to verified/legitimate accounts to distort degree/centrality metrics. | Deep message passing ($l \ge 2$) and attention-based relational weighting (GAT/GraphSAGE). |
| **Changing User Behavior** | Dynamic attack strategies and drifting posting cadences over time. | Chronological data partitioning and temporal feature engineering. |
| **Data Quality & Leakage** | Noisy social graphs, duplicate profiles, and risk of test-label leakage during graph compilation. | Strict test-set isolation during preprocessing and inductive graph partitioning. |
| **Adversarial Manipulation** | Intentional perturbations by attackers to evade detection (feature hiding, edge injection). | Rigorous robustness benchmarking against Feature Masking and Edge Injection. |
| **Scalability & Cold-Start** | Graph expansion causes memory bottlenecks; newly registered accounts lack deep graph context. | Inductive learning via GraphSAGE with neighbor sampling ($k$-hop sampling). |

---

## 3. Mathematical Formulations & Formal Notation

### 3.1. Graph Representation & Node Feature Matrix
Let the online social network be modeled as an attributed graph:
$$G = (V, E, X)$$
- $V$: Set of users (nodes), $|V| = N$.
- $E$: Set of social relationships/interactions (edges), $|E| = M_E$.
- $X \in \mathbb{R}^{N \times M}$: The Node Feature Matrix, where $N$ is the number of accounts and $M$ is the dimensionality of engineered node attributes.
- $A \in \mathbb{R}^{N \times N}$: The graph adjacency matrix representing topological connectivity.

### 3.2. GNN Message Passing & Neighborhood Aggregation
At each layer $l \in \{1, \dots, L\}$, user $v$'s representation is updated by aggregating information from its immediate neighborhood $\mathcal{N}(v)$:
$$h_v^{(l+1)} = \phi\left(h_v^{(l)}, \text{AGG}\left\{h_u^{(l)} \mid u \in \mathcal{N}(v)\right\}\right)$$
Where:
- $h_v^{(l)}$: Feature representation (hidden state) of user node $v$ at layer $l$ ($h_v^{(0)} = x_v$).
- $\mathcal{N}(v)$: Topological neighborhood of node $v$.
- $\text{AGG}$: Permutation-invariant aggregation function (e.g., mean, pooling, or multi-head attention).
- $\phi$: Non-linear combination/update function (trainable neural network layer).
- Multi-hop context: Stacking $L$ layers expands the receptive field to an $L$-hop neighborhood.

### 3.3. Final Node Embedding
The final node embedding $z_v$ captures both individual profile attributes and structural neighborhood context:
$$z_v = f_\theta(X, A)_v$$
Where $f_\theta$ is the parameterized Graph Neural Network.

### 3.4. Classification & Fake-Profile Risk Prediction
The node embedding $z_v$ passes into a classification layer with a sigmoid activation function for binary classification:
$$\hat{y}_v = \sigma(W z_v + b) = \frac{1}{1 + e^{-(W z_v + b)}}$$
- $\hat{y}_v \in [0, 1]$: Predicted probability that account $v$ is fake (or risk score for operational triage).
- $W \in \mathbb{R}^{1 \times d}$, $b \in \mathbb{R}$: Trainable weight matrix and bias vector.

### 3.5. Optimization Objective (Binary Cross-Entropy Loss)
Trained over labeled training nodes $V_L$ ($|V_L| = N_L$):
$$\mathcal{L} = -\frac{1}{N_L} \sum_{v \in V_L} \left[ y_v \log(\hat{y}_v) + (1 - y_v) \log(1 - \hat{y}_v) \right]$$

---

## 4. End-to-End Proposed Methodology (9 Stages)

```
[1. Data Collection] ──► [2. Data Preprocessing] ──► [3. Feature Engineering]
                                                               │
                                                               ▼
[6. Message Passing & Embeddings] ◄── [5. Training & Validation] ◄── [4. Model Development]
         │
         ▼
[7. Fake Profile Prediction] ──► [8. Adversarial Robustness] ──► [9. Suspicious Network Analysis]
```

1. **Stage 1: Data Collection**
   - Ingestion of user identifiers, metadata, activity logs (posts, replies, retweets/shares, likes), and interaction edges (follower–following, mentions, friendships).
   - Timestamp logging for temporal analysis.
2. **Stage 2: Data Preprocessing**
   - Schema validation, normalization of handles/IDs, deduplication of records.
   - Missing attribute imputation using *training-partition-only* parameters.
   - Extreme value auditing (preserving genuine influencers vs. high-volume bot activity).
   - Strict separation of train, validation, and test splits prior to graph construction to eliminate data leakage.
3. **Stage 3: Feature Engineering**
   - **Account/Behavioral Features ($M$):** Account age, follower count, following count, follower-to-following ratio, post frequency (posts/day), profile completeness %, reciprocity rate, temporal burstiness.
   - **Structural Graph Features:** Degree centrality, clustering coefficient, mutual connection ratio, neighborhood density, community membership.
4. **Stage 4: Model Development**
   - Progressive evaluation hierarchy:
     - Non-graph baselines: Logistic Regression, Support Vector Machine (SVM), Random Forest, Artificial Neural Network (MLP).
     - Graph Neural Networks: Graph Convolutional Networks (GCN), GraphSAGE, Graph Attention Networks (GAT).
5. **Stage 5: Model Training & Validation**
   - Chronological or inductive splits to mirror real-world deployment.
   - Validation-set hyperparameter tuning (learning rate, hidden dimensions, layer count, dropout rate, neighborhood sampling budget).
   - Early stopping to prevent overfitting.
6. **Stage 6: Message Passing & Node Representation Learning**
   - Iterative neighborhood aggregation over $L \ge 2$ layers to capture multi-hop relational patterns.
7. **Stage 7: Fake Profile Prediction & Triage**
   - Computation of profile risk score $\hat{y}_v \in [0, 1]$.
   - Decision threshold tuning based on operational cost (balancing False Positives vs. False Negatives).
8. **Stage 8: Adversarial Robustness Analysis**
   - Controlled perturbations to stress-test resilience:
     - **Feature Masking:** Hiding or perturbing key profile features to simulate profile spoofing.
     - **Edge Injection:** Synthesizing artificial edges between fake nodes and genuine/verified nodes to simulate relation camouflage.
9. **Stage 9: Suspicious Network Analysis**
   - Clustering and sub-graph inspection: Connected components, Louvain/Leiden community detection, high-density subgraph mining to identify coordinated Sybil rings and bot armies.

---

## 5. System Architecture & Modular Infrastructure

The system employs a 5-layer modular architectural paradigm:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 5. DECISION SUPPORT LAYER (Dashboard, Network Visualizer, Audit Log)   │
├────────────────────────────────────────────────────────────────────────┤
│ 4. PREDICTION LAYER (Risk Probability Scoring, Thresholding, Triage)   │
├────────────────────────────────────────────────────────────────────────┤
│ 3. GRAPH MODELING LAYER (GNN Architectures: GCN, GraphSAGE, GAT)       │
├────────────────────────────────────────────────────────────────────────┤
│ 2. DATA ENGINEERING LAYER (Cleaning, Feature Prep, Graph Construction) │
├────────────────────────────────────────────────────────────────────────┤
│ 1. DATA COLLECTION LAYER (APIs, Webhooks, Platform Ingestion Logs)     │
└────────────────────────────────────────────────────────────────────────┘
```

### Functional Component Inventory

| Module Name | Core Responsibility |
|---|---|
| **User Data Module** | Stores, normalizes, and validates profile records and behavioral event logs. |
| **Graph Construction Module** | Compiles edge indices and builds the adjacency matrix from follower/interaction links. |
| **Feature Engineering Module** | Generates normalized individual, behavioral, and structural feature matrices ($X$). |
| **GNN Model Module** | Executes neighborhood sampling, message-passing layers, and generates embeddings ($Z$). |
| **Prediction Module** | Generates binary classifications, continuous risk scores, and confidence intervals. |
| **Network Analysis Module** | Identifies anomalous subgraphs, dense cliques, and suspicious clusters. |
| **Dashboard Module** | Presents visual insights, network topologies, and reviewer triage workflows. |

---

## 6. Experimental Protocols & Model Evaluation Benchmarks

### Table I: Recommended Experimental Protocol

| Stage | Purpose | Key Control / Constraint |
|---|---|---|
| **Training** | Learn model parameters from labeled user data and graph structure. | Training partition only; zero access to test labels/features. |
| **Validation** | Select hyperparameters and optimal classification decision threshold. | Isolated validation partition for early stopping and thresholding. |
| **Testing** | Estimate out-of-sample generalization on unseen profiles. | Final evaluation only; test set held completely untouched. |
| **Ablation Study** | Isolate and measure contribution of features vs. graph topology. | Systematically drop feature groups and graph layers. |
| **Robustness Test** | Evaluate degradation under adversarial evasion attempts. | Inject synthetic camouflage edges and mask profile attributes. |
| **Inductive Evaluation** | Test performance on newly joined nodes with no prior training context. | Completely unseen nodes excluded from graph fitting (GraphSAGE). |

### Table II: Qualitative Model Comparison Matrix

| Model Architecture | User Features | Structural Learning | Multi-Hop Context | Inductive Learning | Interpretability |
|---|---|---|---|---|---|
| **Logistic Regression** | Explicit features | No | No | Yes (feature-based) | High |
| **SVM** | Explicit features | No | No | Yes (feature-based) | Moderate |
| **Random Forest** | Explicit features | No | No | Yes (feature-based) | Moderate |
| **ANN / MLP** | Explicit features | No | No | Yes (feature-based) | Lower |
| **GCN** | Node features | Explicit (Graph) | Yes ($L$-hop) | Transductive / setup-dependent | Lower |
| **GraphSAGE** | Node features | Explicit (Graph) | Yes ($L$-hop) | **Yes (Learned Aggregator)** | Lower |
| **GAT** | Node features | Explicit (Graph) | Yes ($L$-hop) | Transductive / setup-dependent | Lower |

### Evaluation Metrics Standard
- **Accuracy:** $\frac{TP + TN}{TP + TN + FP + FN}$ (monitored with caution due to class imbalance).
- **Precision:** $\frac{TP}{TP + FP}$ (critical to prevent false flagging of legitimate users).
- **Recall:** $\frac{TP}{TP + FN}$ (vital to catch dangerous botnets).
- **F1-Score:** $2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$.
- **ROC-AUC & PR-AUC:** Precision-Recall AUC is especially emphasized due to severe genuine-to-fake class imbalance in real-world OSNs.
- **System Metrics:** Inference latency (ms), memory footprint (MB/GB), and robustness drop under perturbation ($\Delta \text{F1}$).

---

## 7. Web Application Prototype & Analyst UI Workflow

The paper specifies five functional interfaces for the Innovexa Trust & Safety platform:

1. **Landing & Authentication Screen (Fig. 4):**
   - Professional security-oriented login portal (*"Smarter Detection. Safer Social Networks"*).
   - Role-Based Access Control (RBAC) linking audit logs to analyst credentials.
2. **Profile Detection View (Fig. 5):**
   - Input methods: Single manual handle input, platform selection (Twitter/X, etc.), User ID lookup, or batch file upload.
   - Detection output: Radial/badge Risk Score (e.g., `0.87 High Risk – Likely Fake Profile`), join date, account age, post counts.
   - Contextual indicators: Low profile completeness, abnormal follower/following ratio (e.g., 36.3), content similarity, and an interactive ego-network graph snippet highlighting suspicious vs. legitimate neighbors.
3. **Executive Dashboard (Fig. 6):**
   - Top KPI cards: *Total Profiles Analyzed* (e.g., 12,487), *Predicted Fake Accounts* (2,843 / 22.8%), *Predicted Genuine* (9,644 / 77.2%), *High-Risk Cases* (612), *Suspicious Clusters* (48).
   - Visualizations: Detection trend timeline over days, donut class distribution, regional geographic risk distribution map (Delhi, Noida, Gurgaon, etc.).
   - Model health telemetry: GNN Model online status, validation accuracy (92.4%), feature pipeline latency (320ms), graph freshness.
4. **Suspicious Network Analysis View (Fig. 7):**
   - Deep-dive relational canvas: Interactive force-directed graph centering on a suspect node (e.g., `@janedoe123`), connecting to high-risk neighbors (red), medium risk (orange), and genuine accounts (blue/green).
   - Coordinated cluster extraction: Groups flagged with common creation dates, high internal connection density, and identical posting schedules.
   - Node detail table: Risk score, followers, account age, and cluster role (Core Member vs. Connected Link).
5. **Detection History & Audit Trail (Fig. 8):**
   - Comprehensive log of past analyses: User ID, handle, prediction class, risk score, model version (`GNN v1.2.3`), timestamp, and reviewer disposition status (`Pending`, `Reviewed`, `Flagged`, `Escalated`).
   - Export capabilities for regulatory compliance and downstream account actioning.

---

## 8. Limitations & Future Roadmap

- **Graph Drift & Temporal Shifts:** Static GNNs degrade as network patterns evolve. Future iterations should incorporate Temporal Graph Networks (TGNs) or dynamic edge time-decay functions.
- **Severe Class Imbalance:** Real-world fake account ratios are low (~2–10%). Requires cost-sensitive focal loss, SMOTE-like graph oversampling, or self-supervised contrastive pre-training.
- **Explainability (XAI):** GNN predictions need post-hoc explainers (such as GNNExplainer or SubgraphX) to provide human-interpretable rationales for content moderation teams.
- **Adversarial Hardening:** Ongoing defense research against active evasion tactics (adaptive edge dropouts and adversarial training loops).
