# DPC-GNN-RL Delivery Checklist

Last updated: 2026-03-04

## 1) Required files

- [x] `docs/paper_assets/DELIVERY_CHECKLIST.md`
- [x] `scripts/reproduce_figs.sh`
- [x] `physdrive_paper.md`
- [x] `physdrive_paper.pdf`

## 2) Figure asset inventory (canonical names)

Expected source figures at repo root:

1. `multi_instrument_perf.png`
2. `reward_curve.png`
3. `gradient_norm.png`

Validation criteria:

- [x] Files exist
- [x] Naming is consistent with canonical list above
- [x] PNG output is 300 DPI (print-ready)

## 3) One-command reproduction

```bash
bash scripts/reproduce_figs.sh
```

What it does:

1. Reads canonical source figures from repo root.
2. Re-saves figures to `docs/paper_assets/figures/` with explicit `300x300` DPI metadata.
3. Checks:
   - Source file existence
   - Output naming consistency (no missing/extra PNGs)
   - DPI threshold (`>=299` on both axes)

## 4) Notes

- Current source PNG metadata is already approximately 300 DPI (`299.9994`).
- Reproduction script normalizes output to explicit `300 DPI` and performs automated validation.
