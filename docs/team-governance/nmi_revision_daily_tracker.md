# NMI Revision Daily Tracker

## Rules
- Update this file every day.
- End each day with: status, artifacts, risks, next queue, commit hash.
- No day closes without a git push unless the repo is broken.

---

## 2026-03-08 (Day 1)
### Completed
- Built strict war plan: `docs/team-governance/nmi_revision_warplan_2026-03-08.md`
- Built checklist: `docs/team-governance/nmi_revision_checklist_2026-03-08.md`
- Confirmed 铁蛋儿 SSH target: `ssh taisen@taisens-macbook-pro-2`
- Confirmed 铁蛋儿 main repo: `~/workspace/DPC-GNN-RL`
- Verified 铁蛋儿 hardware: Apple M3 Max, 36 GB RAM
- Launched DiffPPO v12b 3-seed batch on 铁蛋儿
- Launched 铁蛋儿 monitor log
- Started Expert Council review line (algorithm / baselines / failure / positioning / week plan)

### In progress
- Batch A: `run_diffppo_v12b.sh` (3 seeds in parallel) — completed; treated as reconnaissance, not final evidence
- Batch B: parallel ablation launch on 铁蛋儿
  - `ablation_no_pgas_seed1.py`
  - `ablation_no_pgas_seed2.py`
  - `ablation_no_pgas_seed3.py`
  - `ablation_no_nearfield_seed1.py`
  - `ablation_no_nearfield_seed2.py`
  - `ablation_no_nearfield_seed3.py`
- Expert Council first-round outputs delivered; GPT-5.4 synthesis pending

### Artifacts / Logs
- Local plan: `docs/team-governance/tiedan_run_plan_2026-03-08.md`
- Remote logs:
  - `~/workspace/DPC-GNN-RL/logs/launch_diffppo_v12b_20260308.log`
  - `~/workspace/DPC-GNN-RL/logs/exp_monitor_20260308.log`
- Remote result logs:
  - `~/workspace/DPC-GNN-RL/results/diffppo_v12b_seed0_run.log`
  - `~/workspace/DPC-GNN-RL/results/diffppo_v12b_seed1_run.log`
  - `~/workspace/DPC-GNN-RL/results/diffppo_v12b_seed2_run.log`

### Risks
- GPT-5.4 subagent route unstable for orchestration; Sonnet supervisor route preferred
- Current approach may not be globally optimal; requires Expert Council judgment
- Baseline coverage still incomplete (SAC / TD3 / stronger fairness matrix not yet run)
- Current RL code/result pipeline is not yet paper-grade; current runs are reconnaissance until they pass the new robustness gate
- Early signal from Batch B: removing PGAS causes very large gradient norms (already >4k by ep90 on seed1), suggesting severe stabilization dependence

### Next queue
1. Fix the ablation final-print KeyError so outputs become pipeline-clean
2. Turn tonight's ablation logs into a structured summary table
3. Launch next route comparison batch (StdPPO + DPC-GNN, then stronger baselines as feasible)
4. Produce GPT-5.4 synthesis memo from expert council reports
5. Continue route comparison toward a hard conclusion on the best control paradigm for DPC-GNN

### End-of-day commit
- Commit hash: `c5a5fda`
- Push status: pushed to `main`
