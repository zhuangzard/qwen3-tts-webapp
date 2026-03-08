# NMI Revision War Plan (Strictest-Version)

**Date:** 2026-03-08  
**Owner:** 三丫  
**Target paper:** PhysDrive Med Gym / DiffPPO / MPWM manuscript  
**Principle:** Follow the *strictest* reviewer interpretation, not the easiest one.

---

## 0. Mission

We assume the harsh R4/R5 reviewer sets are the real bar.
That means this is **not a cosmetic minor revision**. It is a **evidence rebuild + claim recalibration** campaign.

Primary objective:
1. Remove all claims that can be attacked as overstated.
2. Rebuild the evidence chain with fair baselines, multi-seed statistics, and matched metrics.
3. Make the paper reproducible enough that a hostile reviewer has fewer attack surfaces.
4. Force all sub-agents to work under a strict QC pipeline.

---

## 1. New Global Sub-agent Workflow (effective immediately)

### 1.1 Fixed role split
Every non-trivial experiment must use **5 GPT-5.4 sub-agents**, with one responsibility each:

1. **Spec Agent**
   - writes exact experiment spec before any run
   - defines hypothesis, metrics, seeds, stopping rule, fairness constraints

2. **Execution Agent**
   - runs experiments only according to approved spec
   - cannot change config silently

3. **Verification Agent**
   - checks logs, seeds, checkpoints, metric scripts, table values
   - verifies that reported numbers equal recomputed numbers

4. **Statistics Agent**
   - produces mean/std/median/success@threshold/CI
   - checks cherry-picking risk and metric mismatch

5. **Paper Integration Agent**
   - updates manuscript/table/figure/appendix/rebuttal text
   - cannot invent results; only consume verified outputs

### 1.2 Hard gates
No experiment counts as "done" unless all gates pass:

- **Gate A: Spec freeze**
  - question, config, seeds, baselines, metrics are frozen before run
- **Gate B: Run integrity**
  - logs complete, seed IDs recorded, checkpoints saved
- **Gate C: Metric integrity**
  - all paper numbers reproduced from raw outputs
- **Gate D: Fair comparison**
  - same thresholds / same eval horizon / same budget across compared methods
- **Gate E: Writing integrity**
  - abstract/body/tables/figures all use the same statistical object

### 1.3 Forbidden behavior
- No single-agent "I ran it and it looks good"
- No reporting best-case only
- No mixing best-stage, final-stage, and mean values in one headline claim
- No estimated numbers in final tables
- No silent baseline weakening
- No claim stronger than evidence
- No manuscript edits before number verification

### 1.4 Mandatory artifact bundle per experiment
Each experiment folder must contain:
- `SPEC.md`
- `RUNS/` with per-seed logs
- `CHECKPOINTS/`
- `METRICS.json`
- `QC_REPORT.md`
- `FIGURES/`
- `TABLE_ROW.json`
- `INTEGRATION_NOTES.md`

---

## 2. Priority stack from strictest reviewers

### P0 — Must fix or paper remains rejectable
1. Remove / rewrite invalid claims:
   - `without data`
   - over-strong `without reward engineering`
   - `analytically accurate gradients`
   - `beyond human capability`
   - direct clinical applicability language
2. Unify statistics:
   - separate best precision / stage mean / end-of-training mean / success rate
3. Add fair success metric for DiffPPO
4. Finish real ablations (no estimated numbers)
5. Fix method-definition ambiguity (DiffPPO identity, PGAS wording)
6. Fix Figure 1 contradiction with physics loss
7. Align E-range claim with actual table support

### P1 — Strongly recommended for top-venue survivability
8. Add stronger baselines (prefer SAC + TD3; MPC/CEM optional if feasible)
9. Add 4-scenario quantitative table with multi-seed where possible
10. Add full reproducibility appendix (mesh/GNN/PPO/contact/FEM details)
11. Add FD-gradient distribution analysis, not median only
12. Lower Curriculum Collapse from formal claim to preliminary characterization unless generalized evidence is completed

### P2 — Strengthening layer
13. Replace or weaken human-tremor comparison
14. Merge/rework repetitive figures
15. Clean references completely
16. Expand limitations and contribution boundary

---

## 3. Seven-day execution plan

## Day 1 — Claim reset + experiment freeze
**Goal:** Stop all narrative drift. Freeze what must be rerun.

### Deliverables
- Final P0/P1 experiment matrix
- Claim rewrite sheet
- Unified metric schema
- Experiment owner assignment

### Tasks
- Rewrite title candidates (remove `without data`)
- Rewrite Abstract into conservative version
- Create one canonical metric dictionary:
  - `best_precision_mm`
  - `stage3_mean_mm`
  - `final_window_mean_mm`
  - `success@1mm`
  - `success@3mm`
  - `success@5mm`
  - `mean±std across seeds`
- Freeze baseline fairness rules
- Freeze exact seeds and compute budget

### Exit criteria
- No ambiguous headline metric remains
- Every experiment has an owner and spec

---

## Day 2 — Core ablations rerun
**Goal:** Replace all estimated / weak ablation evidence.

### Experiments
- w/o Near-Field
- w/o PGAS
- w/o curriculum or simplified curriculum
- full DiffPPO reference run

### Requirements
- minimum 3 seeds, preferably 5 if budget allows
- identical evaluation window
- identical success thresholds

### Deliverables
- clean ablation table draft with mean±std
- per-seed run sheet
- QC note on failure modes

### Exit criteria
- No final ablation row comes from estimate or intermediate run

---

## Day 3 — Strong baselines
**Goal:** Remove the "weak baseline" attack.

### Experiments
- SAC baseline
- TD3 baseline
- optional MPC/CEM if implementation cost is acceptable
- re-check StdPPO with tuned reward and documented tuning method

### Fairness requirements
- same observation/action space
- same curriculum exposure or explicitly justified mismatch
- same training budget or clearly normalized comparison

### Deliverables
- baseline fairness memo
- new main table draft
- failure analysis for each baseline

### Exit criteria
- At least two strong baselines added or a documented reason why one cannot be fairly run

---

## Day 4 — Multi-scenario evidence
**Goal:** Support framework-level claims.

### Experiments
- palpation
- push
- grasp
- multi-instrument

### Minimum standard
- quantitative table for all 4 scenarios
- if multi-seed impossible on all four, then:
  - full multi-seed on primary task
  - preliminary but clearly labeled results on secondary tasks

### Deliverables
- 4-scenario summary table
- scenario-specific appendix notes
- claim downgrade if secondary tasks remain preliminary

### Exit criteria
- No paragraph says "four scenarios" without a corresponding quantitative table

---

## Day 5 — Mechanism evidence + reproducibility
**Goal:** Defend the method scientifically, not rhetorically.

### Tasks
- DiffPPO algorithm definition cleanup
- PGAS wording unification
- Newton's third law vs energy conservation wording fix
- FD gradient distribution analysis:
  - median
  - 95th percentile
  - contact / non-contact split
  - sample count
- reproducibility appendix:
  - mesh size
  - node count
  - GNN layers/dims/activation/aggregation
  - PPO hyperparameters
  - FEM/contact details
  - curriculum transition rule

### Deliverables
- methods patch set
- appendix config table
- FD validation figure/table

### Exit criteria
- A skeptical reader can implement the method without guessing hidden settings

---

## Day 6 — Figures, tables, manuscript integration
**Goal:** Eliminate presentational attack surfaces.

### Tasks
- Regenerate Figures 1–4
- add error bars where needed
- fix all units / axis labels / captions / typos
- remove repeated figure content
- align all table captions to identical statistical definitions
- rewrite Discussion/Limitations/Conclusion conservatively

### Deliverables
- figure pack v2
- table pack v2
- manuscript draft R-strict

### Exit criteria
- No figure contradicts text
- No caption hides the evaluation object

---

## Day 7 — Red-team review + submission pack
**Goal:** Try to kill the paper internally before reviewers do.

### Tasks
- red-team read by hostile reviewer sub-agents
- table-to-log number audit
- citation / DOI / placeholder audit
- response-to-reviewers draft aligned with real completed changes only
- final checklist signoff

### Deliverables
- RED_TEAM_REPORT.md
- FINAL_QC.md
- response_to_reviewers_strict.md
- submission-ready PDF bundle

### Exit criteria
- Every claim traces to a verified artifact
- No uncompleted experiment appears in manuscript or response letter

---

## 4. Sub-agent daily operating rhythm

### Morning
- Spec Agent posts run plan
- 三丫 approves / rejects
- Execution Agent starts runs

### Midday
- Verification Agent checks early logs
- aborts broken runs quickly

### Evening
- Statistics Agent recomputes numbers
- Paper Agent updates only verified content
- 三丫 posts daily summary:
  - what finished
  - what failed
  - what must rerun tomorrow

### Every day mandatory summary fields
- completed experiments
- failed / invalid experiments
- exact artifacts saved
- new risks discovered
- next-day dependencies

---

## 5. Master checklist

## A. Claim cleanup
- [ ] Remove `without data`
- [ ] Rewrite reward-engineering claim precisely
- [ ] Remove `analytically accurate`
- [ ] Remove `beyond human capability`
- [ ] Remove direct clinical-applicability language
- [ ] Downgrade Curriculum Collapse claim if evidence remains narrow

## B. Statistics integrity
- [ ] Best vs mean separated everywhere
- [ ] Stage metric vs final metric separated everywhere
- [ ] Mean±std reported for key tables
- [ ] Success@1/3/5mm added
- [ ] DiffPPO and baselines use matched metrics
- [ ] No estimated values remain in final tables

## C. Baselines
- [ ] StdPPO fairness documented
- [ ] SAC added
- [ ] TD3 added
- [ ] optional MPC/CEM considered
- [ ] baseline budget parity documented

## D. Multi-scenario evidence
- [ ] palpation quantitative results
- [ ] push quantitative results
- [ ] grasp quantitative results
- [ ] multi-instrument quantitative results
- [ ] preliminary labels used if needed

## E. Methods / reproducibility
- [ ] DiffPPO objective defined cleanly
- [ ] PGAS wording unified
- [ ] Newton 3rd law vs energy conservation corrected
- [ ] λ1 / λ2 values stated
- [ ] d_boost rationale stated
- [ ] Δt units fixed
- [ ] mesh/node/GNN/FEM/PPO config table added

## F. Mechanism evidence
- [ ] FD validation distribution added
- [ ] contact vs non-contact analysis added
- [ ] sample count added
- [ ] collapse evidence validated or claim downgraded

## G. Figures / tables / refs
- [ ] Figure 1 contradiction fixed
- [ ] Figure 2/3 redundancy fixed
- [ ] error bars added
- [ ] all axes/units/captions corrected
- [ ] refs cleaned, DOI/page ranges checked
- [ ] no placeholder citations remain

## H. Final QC
- [ ] every paper number linked to raw artifact
- [ ] response letter mentions only completed work
- [ ] hostile red-team pass
- [ ] final PDF compiled

---

## 6. Decision rule for submission

### Submit to NMI only if all are true:
- all P0 done
- at least 2 strong baselines completed
- ablations are real multi-seed results
- multi-scenario evidence is quantitatively reported
- claims are fully recalibrated

### Otherwise:
- downgrade venue strategy temporarily
- or continue revision until evidence matches claim level

---

## 7. Command principle

The paper no longer wins by sounding stronger.  
It wins by becoming **harder to attack than to praise**.

---

## 8. Continuous execution rule (new, mandatory)

This project does **not pause between batches** unless blocked by:
- machine failure,
- missing user decision,
- corrupted results,
- or a failed quality gate.

Otherwise, the default is:
1. finish today's batch,
2. verify and archive outputs,
3. update docs/checklists,
4. commit + push,
5. immediately queue tomorrow's batch.

### 8.1 Daily completion package
Every day must end with all of the following:
- experiment status updated
- results/log paths recorded
- checklist updated
- risk log updated
- next-day queue frozen
- git commit created
- git push completed

### 8.2 Daily cadence
#### End of Day N
- stop only after the current batch reaches a valid checkpoint
- verify which runs are valid / invalid
- save exact artifact paths
- update war plan + tracker + checklist
- commit + push all non-transient docs/code/results metadata

#### Start of Day N+1
- read prior day's tracker
- resume unfinished valid runs if needed
- launch the next highest-priority batch immediately
- do not wait for a new instruction if the queue is already defined

### 8.3 Push discipline
- **Every day must have a git push** unless the repo is in a broken/conflicted state
- Commit message must reflect the real state, e.g.:
  - `docs: day1 experiment matrix + tiedan run plan`
  - `exp: diffppo v12b 3-seed batch launched on tiedan`
  - `qc: baseline fairness matrix and daily tracker update`
- Never claim an experiment is complete in git history unless QC has passed

### 8.4 Completion definition for the whole project
The project is only considered complete when:
- required experiments are run,
- required QC is done,
- figures/tables/manuscript are synchronized,
- response letter matches actual completed work,
- and the submission package is ready.

Until then, this remains an active rolling operation.
