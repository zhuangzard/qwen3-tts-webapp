# 2026-03-08 Handoff Summary — PhysDrive / DiffPPO Rescue

## Purpose
This file is the fast re-entry summary for the next session.
If resumed later, read this file first, then `nmi_revision_daily_tracker.md`.

---

## 1. Current status (truthful)
- The paper is **not publication-ready**.
- Current DiffPPO line is **not stable enough** to support the main paper claim.
- Current project state is a **rescue / pivot evaluation** phase, not a minor-revision phase.
- Heavy experiments are now run on **铁蛋儿** via SSH: `ssh taisen@taisens-macbook-pro-2`
- Main executor repo on 铁蛋儿: `~/workspace/DPC-GNN-RL`

---

## 2. Main experiment results collected tonight

### 2.1 DiffPPO v12b reconnaissance batch (3 seeds, completed)
Final distances from run logs:
- seed0: **11.88 mm**
- seed1: **11.19 mm**
- seed2: **11.38 mm**

Interpretation:
- Current DiffPPO v12b is **not reliable**.
- It may produce transient good numbers, but final behavior is poor.
- These runs are **reconnaissance only**, not final paper evidence.

### 2.2 Parallel ablation batch (completed on 铁蛋儿)
#### No-PGAS
- seed1: **11.04 mm**
- seed2: **8.67 mm**
- seed3: **11.00 mm**

#### No-NearField
- seed1: **8.90 mm**
- seed2: **6.66 mm**
- seed3: **9.10 mm**

Important note:
- All 6 ablation scripts hit a **final print KeyError** after training completed.
- The training data is still usable from logs.
- Need to fix summary bug before treating the pipeline as robust.

### 2.3 Early qualitative conclusion from ablations
- **PGAS behaves like a stabilization patch**: removing it leads to very large gradient norms early in training.
- **Near-Field behaves more like performance shaping**: removing it hurts results, but does not create the same degree of numeric explosion.
- Therefore, current method appears **trick-dependent**, especially on the stabilization side.

---

## 3. Main discussion conclusions from tonight

### 3.1 Core strategic conclusion
Do **not** assume DiffPPO is the answer.
Treat it as a candidate that may be rejected.

### 3.2 Real project advantage
The real competitive core is likely:
- **physics-native soft-tissue modeling / DPC-GNN**
- not the current unstable DiffPPO recipe by itself

### 3.3 Key scientific question
What control paradigm best leverages DPC-GNN?
Possible answers to test:
1. standard RL + DPC-GNN simulator/material
2. differentiable / local physics-aware controller
3. model-based planning (MPC / MPPI / CEM)
4. hybrid split: pre-contact vs post-contact

### 3.4 Important conceptual split
A major council consensus is that **pre-contact** and **post-contact** should likely be treated as different regimes:
- pre-contact = free-space / reach / planner regime
- post-contact = contact-rich / compliance / local physics-control regime

### 3.5 Philosophy shift
- Tricks that “make it work” are temporary.
- We are searching for the **healthy, principled, physics-grounded solution**.
- Any future method must be able to explain *why it works physically*, not just that it occasionally gets a good number.

---

## 4. Expert Council progress
The following first-round expert reports were completed:
- `expert_A_algorithm_alternatives.md`
- `expert_B_baselines_fairness.md`
- `expert_C_failure_modes.md`
- `expert_D_positioning.md`
- `expert_E_week_plan.md`
- `expert_F_contact_propagation.md`
- `expert_G_innovative_methods.md`
- `expert_H_stability_objective.md`
- `expert_I_breakthrough_chair.md`

High-level council consensus:
- Current DiffPPO paper story cannot be accepted as-is.
- Current method is not yet a principled solution.
- Need to evaluate stronger alternative routes, especially regime-aware / hybrid control.

---

## 5. Immediate next actions
1. Fix the final-print KeyError in ablation scripts.
2. Convert tonight's log-based ablation results into a structured summary table.
3. Launch the next comparison route(s):
   - StdPPO + DPC-GNN
   - stronger baselines (SAC / TD3 as feasible)
   - planning / hybrid route if implementation path is available
4. Produce GPT-5.4 synthesis of council reports into a hard decision memo.

---

## 6. Re-entry instruction for next session
Read in this order:
1. `docs/team-governance/2026-03-08_handoff_summary.md`
2. `docs/team-governance/nmi_revision_daily_tracker.md`
3. `docs/team-governance/tiedan_run_plan_2026-03-08.md`
4. relevant expert reports (A–I)

Then continue execution without re-deriving the same conclusions.
