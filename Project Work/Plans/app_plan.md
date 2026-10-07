Two separate plans, as asked — backend first, frontend second, each phased with its own verification gate, plus the memory.md protocol at the end. Sidebar/dashboard sections are remapped from the reference image to what Innovexa actually does, not copy-pasted (orders/customers/revenue → predictions/clusters/model performance).

---

## What changes from the reference UI → Innovexa

The reference is an e-commerce dashboard. Structurally useful (card layout, sidebar, dark theme, chart placement) but the *content* has to map to what your system actually produces:

| Reference concept | Innovexa equivalent |
|---|---|
| Total revenue / orders / visitors / net profit | Total profiles analyzed / Fake detected / Genuine detected / High-risk pending review |
| Revenue bar chart (this month vs last) | Detections over time (fake vs genuine per day, from your test-set run log) |
| Sales by Category donut | Fake detections by archetype (A/B/C/D) — this is a chart you can actually produce from your archetype metadata |
| Order list table | Detection History table (node ID, prediction, risk score, archetype if known, timestamp, model version) |
| "Add order" button | "Simulate New Profile" button (your inductive GraphSAGE demo) |

Sidebar sections: **Dashboard (overview) → Browse Profiles (Option A) → Simulate Profile (Option B) → Network Analysis (clusters) → Detection History → Model Info** (no login/auth needed for a portfolio demo — skip that scope entirely unless you want it).

---

## BACKEND IMPLEMENTATION PLAN (FastAPI)

### Phase B0 — Project Setup & Model Artifact Export

**Objective:** Get everything your notebook produced out of the notebook and into loadable, versioned artifacts the API can serve without retraining anything.

**Steps:**
- FastAPI project structure: `/app/main.py`, `/app/routers/`, `/app/models/`, `/app/schemas/`, `/app/services/`, `/artifacts/`
- From the notebook, export: trained GNN model weights (`.pt`), fitted scaler, unified feature schema mapping (Phase 2 of the earlier plan), the full test-set node data (features + edges + labels + archetype metadata), community detection results
- Pin `requirements.txt` (fastapi, uvicorn, torch, torch_geometric, pydantic, networkx)

**Verification:**
- Load every exported artifact in a throwaway script outside the notebook — confirm no pickling/version mismatch errors
- Confirm artifact file sizes are non-trivial (catch silent empty-export bugs)

---

### Phase B1 — Core Data Access Layer

**Objective:** A service layer that answers "give me node X's data" without re-deriving anything — pure lookup against exported artifacts.

**Steps:**
- `GraphStore` service: loads node feature matrix, edge index, labels, archetype metadata into memory at startup (small enough graph — no DB needed for this layer)
- Methods: `get_node(node_id)`, `get_neighbors(node_id)`, `list_test_nodes(filter_params)`

**Verification:**
- Query a known node ID, manually cross-check returned features/neighbors against the notebook's raw data for that same ID — exact match required

---

### Phase B2 — Prediction Endpoints

**Objective:** The actual inference layer, split by the two modes from our earlier discussion.

**Steps:**
- `POST /predict/browse/{node_id}` — Option A: look up an existing test-set node, run it through the trained model, return prediction + confidence + archetype (if fake)
- `POST /predict/simulate` — Option B: accept user-submitted feature toggles + list of connection node IDs, construct a temporary inductive node, run GraphSAGE forward pass, return prediction (only expose this endpoint if your best/final model is GraphSAGE — confirm this before building it)
- Both endpoints log every call to the detection history store (Phase B5)

**Verification:**
- Re-run the same node ID from Phase B1 through `/predict/browse` — confirm the prediction matches what the notebook's final evaluation produced for that exact node (this is your single most important check — a mismatch here means something broke in the artifact export)
- For `/predict/simulate`: submit a feature set that mimics the egofeat of a known genuine node, connected only to genuine neighbors — sanity-check the model leans genuine; submit sparse features + random connections — sanity-check it leans fake. Not a hard pass/fail, but should not be inverted

---

### Phase B3 — Dashboard Aggregate Endpoint

**Objective:** One endpoint powering the overview cards/charts — compute once at startup or cache, don't recompute from scratch on every dashboard load.

**Steps:**
- `GET /dashboard/summary` — total profiles, fake/genuine counts, high-risk count (above threshold), detections-over-time series, fake-by-archetype breakdown (your donut chart source)
- Precompute at startup from the test-set evaluation results exported in Phase B0, not recalculated live

**Verification:**
- Sum of fake-by-archetype counts == total fake count from Phase 11 of the modeling plan (cross-check against the notebook's own reported numbers, not just internal consistency)

---

### Phase B4 — Network Analysis Endpoint

**Objective:** Serve suspicious cluster data for the graph visualization page.

**Steps:**
- `GET /network/clusters` — return detected high-risk communities (from Phase 13 of the modeling plan) with member node IDs and cluster-level risk score
- `GET /network/node/{node_id}/subgraph` — return a node's local neighborhood (for visualizing "why" a specific prediction was made — who it's connected to)

**Verification:**
- Confirm at least one returned cluster overlaps with your known planted Sybil-ring archetype (if you included one) — same check as Phase 13's own verification, now exposed through the API layer

---

### Phase B5 — Detection History Store

**Objective:** Persist every prediction made through the dashboard (not the offline test-set evaluation — the live demo interactions).

**Steps:**
- SQLite (simplest, zero infra) table: `id, node_id, mode (browse/simulate), prediction, risk_score, archetype, model_version, timestamp`
- `GET /history?page=&filter=` — paginated, filterable, mirrors the Order List table structure from the reference image

**Verification:**
- Make 5 test predictions through B2, confirm all 5 appear in `/history` in correct order with correct fields, no data loss on restart (confirm SQLite file persists, not in-memory)

---

### Phase B6 — API Hardening & Docs

**Objective:** Make it actually usable by a frontend, not just functional in isolation.

**Steps:**
- CORS config for your frontend origin
- Pydantic request/response schemas for every endpoint (not raw dicts)
- Input validation: reject out-of-range node IDs, malformed simulate payloads, with proper 4xx errors
- Confirm `/docs` (Swagger) renders cleanly — this doubles as your API documentation

**Verification:**
- Hit every endpoint through `/docs` manually, confirm correct status codes on both valid and deliberately malformed input (empty feature list, node ID that doesn't exist, negative IDs)

---

## FRONTEND IMPLEMENTATION PLAN (HTML/CSS + vanilla JS)

### Phase F0 — Design Tokens & Shell

**Objective:** Lock the visual system before building pages — dark theme, spacing, typography, pulled from the reference but as reusable CSS variables, not hardcoded per-page.

**Steps:**
- `:root` CSS variables: background layers (base/card/elevated), accent colors (genuine=green, fake=red, high-risk=amber, matching the reference's status-pill color logic), typography scale
- Sidebar shell: logo placeholder, 6 icon nav items (Dashboard, Browse Profiles, Simulate, Network Analysis, History, Model Info), collapse toggle like the reference

**Verification:**
- Sidebar renders identically across all planned pages once reused as a shared partial/include — no visual drift page to page

---

### Phase F1 — Dashboard Overview Page

**Objective:** The landing page — stat cards + two charts, sourced from `/dashboard/summary`.

**Steps:**
- 4 stat cards (Total Profiles / Fake Detected / Genuine Detected / High-Risk Pending) with the up/down delta pill style from the reference
- Bar chart: detections over time (Chart.js, since it's already an approved library in your build environment)
- Donut chart: fake-by-archetype breakdown

**Verification:**
- Numbers on cards match `/dashboard/summary` response exactly, re-verified against the backend's own Phase B3 verification numbers — three-way consistency (notebook → API → UI)

---

### Phase F2 — Browse Profiles Page

**Objective:** Option A — search/select a real test-set node, see its data and prediction.

**Steps:**
- Searchable list/table of test-set nodes (paginated, calling a `GET /nodes` style endpoint — add this to B1 if not already covered)
- Detail panel on selection: node's profile feature summary (human-readable, not raw 1411-dim vector — show category groupings from `.featnames`), its connections count, prediction result with confidence

**Verification:**
- Select 3 known nodes (one from each easy archetype, one Archetype C) — confirm displayed prediction matches backend Phase B2 verification for those same IDs

---

### Phase F3 — Simulate Profile Page

**Objective:** Option B — inductive demo, feature toggles + connection picker.

**Steps:**
- Feature category toggles (grouped by `.featnames` categories — education, work, hometown, etc. — not 1411 raw checkboxes, that's unusable)
- Multi-select for "connect to" existing nodes (searchable, limited to 2-5 per your earlier design)
- Submit → call `/predict/simulate` → display result

**Verification:**
- Confirm the UI sends well-formed payloads matching B2's Pydantic schema (check network tab, not just visual success) — malformed payloads caught by backend validation should surface as a visible UI error, not a silent failure

---

### Phase F4 — Network Analysis Page

**Objective:** Visualize suspicious clusters — this is the one genuinely custom visualization, not a reference-image equivalent.

**Steps:**
- Cluster list (sidebar within the page) + graph visualization panel (vis.js or D3 force-directed — nodes colored by risk score, edges shown)
- Click a node in the viz → shows subgraph detail via `/network/node/{id}/subgraph`

**Verification:**
- Confirm the visualized cluster membership matches the raw `/network/clusters` response exactly — easy to introduce silent rendering bugs here (wrong node dropped, duplicate edges)

---

### Phase F5 — Detection History Page

**Objective:** Direct structural equivalent of the reference's Order List — table, filters, pagination.

**Steps:**
- Table: Node ID, Mode, Prediction, Risk Score, Archetype, Timestamp — status pill styling matching reference (delivered/on-way/await → genuine/fake/high-risk colors)
- Filter by prediction type, date range; pagination matching `/history` endpoint's page params

**Verification:**
- Make a new prediction via F2 or F3, confirm it appears at the top of this table without a manual page refresh breaking state

---

### Phase F6 — Integration Pass & Polish

**Objective:** Everything wired together, responsive, no dead ends.

**Steps:**
- Full click-through: Dashboard → Browse → Simulate → Network → History, confirm no broken links/empty states
- Loading states for every API call (reference design already implies async data, handle it visibly, not with a frozen UI)
- Error states: backend down, node not found, malformed simulate input

**Verification:**
- Kill the backend mid-session, confirm frontend shows a clear error state rather than a silent blank page or console-only failure

---

## memory.md Update Protocol

Every phase, backend or frontend, gets one entry appended on completion — same structured format you already used when reporting Phase 6 baseline results back to me. That format works well, keep it exactly:

```
[YYYY-MM-DD HH:MM:SS] Phase <ID> — <Phase Name>
Status: ✅ PASS / ❌ FAIL / ⚠️ PARTIAL

Component: Backend / Frontend
Files: <relevant files touched this phase>

Key Results:
<whatever numeric/functional output this phase produced>

Verification Details:
Check | Expected | Actual | Status
<one row per verification item from the phase's checklist above>

Notes / Observations:
<anything worth flagging — unexpected results, deviations, follow-ups>
```

Rules for using it:
- One entry per phase, appended, never overwritten — this becomes your build log and your eventual project write-up source material
- A phase isn't marked complete and you don't move to the next one until its verification table is fully ✅ — a ⚠️ PARTIAL entry should name exactly what's outstanding, not get silently abandoned
- Backend and frontend phases interleave by dependency, not by list order above — e.g., F1 needs B3 done first, F2 needs B1+B2 done first, so the actual build order is: B0→B1→B2→B3→F0→F1→B5→F2→B4→F4→... — I'd build backend endpoints just ahead of the frontend page that consumes them, phase pair by phase pair, rather than finishing the entire backend before touching HTML
