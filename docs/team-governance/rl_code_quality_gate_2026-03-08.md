# RL Code Quality Gate — 2026-03-08

## Position
The current manuscript cannot be treated as publication-ready evidence.
From this point onward, all RL code and all experiment outputs are treated as **research-stage artifacts** until they pass the gates below.

## Core rule
**A paper cannot be built on one-off experiment scripts alone.**
It must be built on a robust, reproducible, reviewable RL codebase.

---

## 1. Required quality upgrades

### 1.1 Code structure
- No important result should depend on a single ad-hoc script with hidden constants.
- Training/eval/ablation logic must be factored into reusable modules where possible.
- Configs should be explicit and discoverable.
- Script names like `v9/v12b/fixed/final2` cannot be the scientific story.

### 1.2 Reproducibility
Every run must record:
- seed
- exact config
- code version / commit
- machine name
- start time / end time
- result paths
- evaluation thresholds

### 1.3 Robustness
Required before final evidence is accepted:
- smoke test passes
- resume/restart behavior known
- failure mode logged clearly
- no silent config drift
- no mixed metrics across scripts

### 1.4 Evaluation discipline
- training metric != final paper metric unless explicitly stated
- best-case numbers cannot headline the paper without stable statistics
- all baselines must use matched thresholds / windows / budgets
- result JSON/CSV generation must be standardized

### 1.5 Review discipline
Every major RL change must go through:
1. implementation review
2. experiment design review
3. result audit
4. paper-integration review

---

## 2. Minimal acceptance gates for RL code
A code path is only considered paper-grade if all pass:

- [ ] deterministic seed handling checked
- [ ] config source is explicit
- [ ] training log emitted regularly
- [ ] result summary file emitted automatically
- [ ] evaluation script/path is explicit
- [ ] no hidden manual post-processing required
- [ ] artifact paths documented
- [ ] another agent can rerun it without guessing

---

## 3. Practical implication for current project

### Current DiffPPO runs
- Current runs are useful as **reconnaissance / status checks**.
- They do **not automatically qualify as final paper evidence**.
- Any result that enters the paper must be rerun or revalidated through the new quality gate.

### Current manuscript
- The paper must transition from an "experiment log story" to a real scientific paper:
  - stable method naming
  - contribution framing first
  - verified evidence second
  - reproducible pipeline underneath

---

## 4. Required outputs before final submission
- cleaned method naming
- baseline matrix
- ablation matrix
- unified eval pipeline
- QC report for core tables
- result-to-figure traceability
- commit-linked evidence map

---

## 5. Command principle
If a result is impressive but fragile, it is not publication-grade yet.
