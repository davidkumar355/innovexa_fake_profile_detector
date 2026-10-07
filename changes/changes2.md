You are editing an existing PowerPoint presentation project for my mini-project:

**Project:** Innovexa — Fake Profile / Account Detection Using Graph Neural Networks (GNN)

I already have an existing implementation that generated the current 22-slide presentation. DO NOT rebuild the presentation from scratch unless technically necessary. Inspect the existing source/code/assets first and modify the current implementation so that the final presentation contains exactly **12 slides**.

## PRIMARY OBJECTIVE

Compress the existing 22-slide Innovexa presentation into **exactly 12 slides** while:

1. Preserving all essential research information.
2. Preserving the current visual identity, theme, typography, spacing philosophy, icons, shapes, and overall design language.
3. Following the academic storytelling structure of the provided reference presentation `main ppt 4.pptx`.
4. Removing redundancy rather than blindly shrinking text.
5. Combining related topics intelligently.
6. Keeping the presentation readable and visually balanced.
7. Maintaining technical correctness.
8. Never inventing experimental results, datasets, accuracy values, or claims that are not supported by the existing project.
9. Keeping the deck suitable for a CSE/Data Science mini-project evaluation and viva.

## IMPORTANT SOURCE MATERIALS

Use these as the source of truth:

- Current presentation: `ppt1_updated.pptx`
- Reference presentation/design structure: `main ppt 4.pptx`
- Existing Innovexa research material and content already present in the project

The reference PPT is useful primarily for **presentation structure and information density**, not for copying its subject matter or wording.

## RECOMMENDED ACADEMIC STORY

The final presentation should communicate this story in sequence:

**Problem → Existing Approaches → Research Gap → Why GNN → Proposed Representation → Methodology → GNN Learning → Detection & Explainability → Evaluation/Robustness → Future/Deployment → References → Thank You**

The audience should be able to understand:
- what the problem is,
- why existing methods are insufficient,
- why a graph-based solution is appropriate,
- what Innovexa does,
- how GNN works,
- what the output means,
- how the system would be evaluated,
- and what its practical/future scope is.

---

# EXACT 12-SLIDE STRUCTURE

Do not produce 11 or 13 slides. The final deck must contain exactly these 12 slides.

## SLIDE 01 — TITLE / COVER

Title:

**Innovexa: Fake Profile / Account Detection Using Graph Neural Networks (GNN)**

Keep:
- Department of CSE – Data Science
- Mini Project Presentation
- Guide details
- Team member names and IDs
- Existing college/project cover format

IMPORTANT:
The current deck contains the phrase **“Graphical Neural Network.”**
Replace this with the technically correct term:

**Graph Neural Network (GNN)**

Do not add technical content to the cover.

---

## SLIDE 02 — CONTENTS

Create a concise contents/agenda slide modeled after the structure of `main ppt 4`.

Use grouped sections rather than listing every slide:

1. Problem Statement
2. Existing Approaches & Research Gap
3. Why Graph Neural Networks?
4. Proposed Solution & Methodology
5. GNN Learning & Detection
6. Evaluation & Expected Outcomes
7. Future Scope
8. References

Keep this slide visually simple.

---

## SLIDE 03 — PROBLEM STATEMENT: WHY FAKE ACCOUNTS ARE HARD TO DETECT

MERGE CURRENT SLIDES 02 AND 03.

Do not preserve them as separate slides.

Use a two-part layout.

### Section A — How fake profiles deceive

Retain the four deception categories:

- Fake Identity
- Fake Connections
- Misleading Behavior
- Coordinated Manipulation

Use short descriptions only.

### Section B — What detection must consider

Retain the five core detection dimensions:

- Profile
- Behavioral
- Social Relationships
- Network Topology
- Multi-hop Neighborhood

Also summarize the most important challenges:
- Feature mimicking
- Relation camouflage
- Changing behavior
- Adversarial manipulation

Do NOT list every challenge from the original slide.

### Central takeaway

Use a strong statement such as:

**“Profile-level signals alone are insufficient; suspicious behavior can emerge from the surrounding social network.”**

Make this a visually prominent callout.

---

## SLIDE 04 — EXISTING APPROACHES & RESEARCH GAP

MERGE CURRENT SLIDE 04 WITH THE MOST IMPORTANT RESEARCH-GAP/LIMITATION CONTENT.

### LEFT SIDE — Existing approaches

Include:

**Rule-Based Methods**
- New account
- High follower/following ratio
- Unusual activity
- Limitation: attackers can adapt their behavior

**Traditional Machine Learning**
- Logistic Regression
- SVM
- Random Forest
- MLP / ANN
- Primarily account-level feature vectors

### RIGHT SIDE — Research gap

Use four concise gaps:

**01 — Relational Gap**
Traditional models do not naturally represent user-to-user relationships.

**02 — Structural Gap**
Network topology and suspicious communities are difficult to capture.

**03 — Multi-hop Gap**
Useful signals may exist beyond immediate neighbors.

**04 — Adversarial Gap**
Attackers can manipulate features and social relationships.

### Bottom callout

**“Research Gap → Need for graph-based, multi-hop, and robust detection.”**

Do not create a separate limitations slide from this material.

---

## SLIDE 05 — WHY GRAPH NEURAL NETWORKS?

KEEP THE CORE IDEA OF CURRENT SLIDE 05.

Show a clear social graph visual:

Users as **nodes**
Relationships/interactions as **edges**

Example interaction types:
- Follow
- Friendship
- Like
- Reply
- Mention
- Message
- Share

Show that each node may contain:
- Profile information
- Behavioral information
- Activity information

Add one prominent explanatory sentence:

**“GNN combines a user’s own features with information from connected users.”**

Do not overload this slide with equations or deep model details.

---

## SLIDE 06 — OUR SOLUTION: MULTIMODAL GRAPH REPRESENTATION

MERGE CURRENT SLIDES 06 AND 07.

This should be one of the strongest technical slides.

### Main visual

Display prominently:

**G = (V, E, X)**

Explain:

**V = Users / Nodes**  
**E = Relationships / Edges**  
**X = Node Feature Matrix**

### Feature groups

Retain the four multimodal groups:

**Profile**
- Username
- Bio
- Account age
- Profile picture

**Network**
- Followers/friends
- Communities
- Centrality

**Behavior**
- Posts
- Timestamps
- Engagement patterns

**Content**
- Text
- Images
- Metadata

End with:

**“Each account becomes a feature-rich node connected through the social graph.”**

Do not repeat the entire graph-construction explanation from the original slide.

---

## SLIDE 07 — PROPOSED METHODOLOGY: FROM DATA TO DECISION

MERGE CURRENT SLIDE 08 AND CURRENT SLIDE 14.

DO NOT retain the system architecture as a separate slide.

Create one integrated five-stage pipeline:

### 01 — Data Collection
Profiles, behavior, relationships

### 02 — Data Engineering
Cleaning, validation, feature construction

### 03 — Graph + GNN Modeling
Graph construction, message passing, node representations

### 04 — Prediction
Fake probability and risk score

### 05 — Decision Support
Explanations, suspicious accounts, suspicious communities, human review

Use arrows between stages.

At the bottom add:

**Data → Graph → Learning → Prediction → Investigation**

The pipeline should visually communicate the whole system at a glance.

---

## SLIDE 08 — GNN MESSAGE PASSING & MODEL ARCHITECTURE

MERGE CURRENT SLIDES 09 AND 10.

### Upper half — Message passing

Show the sequence:

**Initial Node Features**
→
**Inspect Neighbors**
→
**Aggregate Information**
→
**Update Representation**

Then explain multi-hop learning:

**1-Hop:** Direct neighbors  
**2-Hop:** Friends of friends  
**3-Hop:** Broader structural context

### Lower half — Model comparison

Use three compact cards:

**GCN**
- Aggregates neighboring node information

**GraphSAGE**
- Samples and aggregates neighborhood information
- Supports inductive learning / unseen nodes

**GAT**
- Uses attention to assign different importance to neighbors

Do not explain the mathematical internals of each architecture.

The slide should answer:

**“How does GNN learn from the graph, and what model families are being considered?”**

---

## SLIDE 09 — RISK DETECTION, EXPLAINABILITY & COMMUNITY ANALYSIS

MERGE CURRENT SLIDES 11, 12 AND 18.

Use a three-column layout.

### COLUMN 1 — Risk Score

Display:

**0.87 — HIGH RISK**

Keep the current disclaimer:

**“Illustrative score for the prototype UI.”**

This must remain clearly labeled as illustrative and NOT as measured experimental performance.

### COLUMN 2 — Why was the account flagged?

Show:

- Connected to many suspicious accounts
- Sudden burst of interactions
- Low neighborhood diversity
- Belongs to a high-risk community

### COLUMN 3 — Human-in-the-loop

Show:

**Analyst Review**
→
**Investigate**
→
**Take Action**

Also retain the idea that humans provide context, fairness, accountability, and final judgment.

### Community detection

Do NOT create another large section for all five community methods.

Instead add a compact line/card:

**Community analysis:** connected components, community detection, local density, repeated interactions, subgraph inspection.

Main message:

**“The system detects not only suspicious users, but also suspicious network structures and coordinated groups.”**

---

## SLIDE 10 — EVALUATION, ROBUSTNESS & EXPECTED OUTCOMES

MERGE CURRENT SLIDES 13, 15 AND 16.

Do NOT create separate slides for these topics.

Use three compact zones.

### TOP — Evaluation setup

Include only:

- Training / Validation / Testing
- Hyperparameter tuning
- Ablation study
- Robustness testing
- Inductive evaluation

### MIDDLE — Metrics

Use five small metric cards:

- Accuracy
- Precision
- Recall
- F1-Score
- ROC-AUC

PR-AUC can be mentioned as a secondary metric if space permits.

### RIGHT OR LOWER SECTION — Robustness

Two attack vectors:

**Feature Masking**
Hide/change profile or activity information.

**Edge Injection**
Add misleading connections to camouflage network position.

Testing flow:

**Normal Graph → Modified Graph → Compare Prediction Change**

### BOTTOM — Expected outcomes

Use three concise outcomes:

**Better Detection**
Combines account-level and network-level evidence.

**Robust & Explainable Predictions**
Provides supporting clues and tests adversarial resilience.

**Actionable Decision Support**
Helps analysts identify suspicious accounts and communities.

### Results table

Include a small model-comparison table only if it fits cleanly:

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Logistic Regression | TBD | TBD | TBD | TBD |
| SVM | TBD | TBD | TBD | TBD |
| Random Forest | TBD | TBD | TBD | TBD |
| GCN | TBD | TBD | TBD | TBD |
| GraphSAGE | TBD | TBD | TBD | TBD |
| GAT | TBD | TBD | TBD | TBD |

IMPORTANT:
NEVER invent or estimate results.

All numerical values must remain **TBD** unless actual experimental values already exist in the project.

Add a small note:

**“Experimental values will be populated after model training and evaluation.”**

---

## SLIDE 11 — FUTURE SCOPE & DEPLOYMENT

MERGE CURRENT SLIDES 17 AND 20.

### Future Scope

Prioritize these six:

1. Dynamic / Temporal GNNs
2. Real-time detection
3. Stronger adversarial robustness
4. Text + image + graph multimodal learning
5. Cross-platform detection
6. Community-level coordinated attack detection

### Deployment considerations

Use four compact cards:

**Scalable**
Large social graphs

**Real-Time**
Fast risk scoring

**Explainable**
Graph evidence

**Privacy-Aware**
Minimize unnecessary data exposure

Do not repeat the human-in-the-loop concept extensively here because it is already on Slide 09.

Do not retain all ten future-scope items as separate large components.

---

## SLIDE 12 — REFERENCES + THANK YOU

MERGE CURRENT SLIDES 21 AND 22.

### Top section — References

Retain the seven current academic references, properly formatted and readable.

Ensure consistency in:
- Author names
- Paper titles
- Conference/journal
- Year
- Punctuation
- Citation numbering

Current references include GNN foundation papers and social-bot/fake-account research.

### Bottom section

Large:

**THANK YOU**

Smaller:

**Questions?**

Do not make a separate 13th thank-you slide.

---

# CONTENT PRIORITY RULES

When space becomes limited, use this priority order:

### MUST KEEP
- Problem definition
- Existing approaches
- Research gap
- Why graph representation
- G = (V,E,X)
- Multimodal features
- Overall methodology
- GNN message passing
- GCN / GraphSAGE / GAT
- Risk score + explanation
- Evaluation metrics
- Robustness concept
- Expected outcomes
- References

### CAN BE COMPRESSED
- Detailed challenge lists
- Detailed community-detection techniques
- Deployment details
- Limitations
- Future-scope details
- Repeated architecture descriptions
- Long explanations of individual features

### DO NOT INCLUDE AS LARGE STANDALONE SECTIONS
- Seven separate limitations
- Ten separate future-scope cards
- Separate system architecture slide
- Separate human-in-the-loop slide
- Separate community-detection slide
- Separate deployment slide
- Separate GCN / GraphSAGE / GAT slides

---

# DESIGN REQUIREMENTS

Preserve the existing visual design rather than redesigning from scratch.

Maintain:
- Existing color palette
- Existing typography
- Existing visual hierarchy
- Existing card style
- Existing red accent treatment
- Existing navy/dark styling
- Existing rounded containers
- Consistent spacing
- Consistent slide numbering if already present
- Professional academic appearance

However, when merging slides:

1. Rebalance layouts instead of shrinking text excessively.
2. Never use tiny unreadable fonts just to fit content.
3. Prefer fewer words + stronger visual grouping.
4. Use whitespace intelligently.
5. Use visual hierarchy to distinguish primary vs secondary information.
6. Remove duplicate subtitles and repeated project titles where unnecessary.
7. Keep each slide focused on one central question.

Do NOT simply concatenate the text of two slides onto one slide.

---

# REFERENCE PPT STRUCTURE TO EMULATE

Use `main ppt 4.pptx` as the structural benchmark.

Its effective pattern is:

**Problem Statement**
→
**Proposed Topic**
→
**Why This Topic**
→
**Existing Work**
→
**Research Gap**
→
**Proposed Methodology**
→
**Expected Outcomes**
→
**References**
→
**Thank You**

Adapt that storytelling pattern to Innovexa.

Do NOT copy the subject matter of the reference deck.

---

# TECHNICAL ACCURACY RULES

1. Use **Graph Neural Network (GNN)**, NOT “Graphical Neural Network.”
2. Do not claim that GNN automatically proves an account is fake.
3. Treat risk scores as decision-support outputs.
4. Keep human review as part of the system.
5. Do not invent accuracy, precision, recall, F1, ROC-AUC or other experimental values.
6. Do not claim a dataset was used unless it is actually present in the project.
7. Do not claim deployment is complete if it is only a proposed architecture.
8. Clearly distinguish:
   - implemented functionality,
   - proposed methodology,
   - illustrative UI examples,
   - future work.

---

# IMPORTANT IMPLEMENTATION INSTRUCTION

Before modifying the presentation:

**Inspect the existing source code and presentation-generation files.**

Then use planning mode to create a concise implementation plan for the 22-to-12 slide compression.

After the plan is internally established, modify the existing implementation rather than creating an unrelated new deck.

Preserve reusable components and existing styling code wherever possible.

---

# VALIDATION REQUIREMENTS

After making the changes, verify ALL of the following:

### Structural validation
- Final deck contains exactly **12 slides**
- No accidental duplicate slides
- Slide numbering is correct
- No blank slides
- No hidden extra slides if the implementation supports them

### Content validation
- All required research concepts are represented
- Existing approaches are included
- Research gap is explicit
- GNN rationale is explicit
- Graph representation G=(V,E,X) is present
- Methodology is present
- Message passing is present
- GCN, GraphSAGE and GAT are represented
- Risk/explainability is present
- Community analysis is represented
- Evaluation metrics are present
- Robustness is represented
- Future scope is represented
- References are present
- Thank-you section is present

### Design validation
- No text overflow
- No clipped objects
- No overlapping shapes
- No unreadable text
- No broken arrows
- No malformed equations
- Consistent alignment
- Consistent spacing
- Consistent typography
- Tables fit within slide boundaries
- References remain readable

### Semantic validation
Check that the final 12-slide presentation tells a coherent story from:

**Problem → Gap → GNN → Solution → Methodology → Detection → Evaluation → Future → References**

If any slide feels overcrowded, reduce wording and restructure the visual hierarchy rather than shrinking the font excessively.

---

# FINAL OUTPUT

Modify the existing presentation project and generate the final **12-slide PPTX**.

Do not merely describe what should be changed.

Actually implement the changes in the existing presentation code/files, regenerate the presentation, and verify the final slide count and visual integrity.

At the end, report:
1. Final slide count
2. Which original slides were merged
3. Any content that was intentionally removed or heavily compressed
4. The location/name of the final generated PPTX
5. Any issues that could not be resolved automatically