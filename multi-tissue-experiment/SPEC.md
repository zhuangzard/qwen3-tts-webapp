# Multi-Tissue Generalization Experiment SPEC
# DPC-GNN MedIA Revision — New Section 5.X

## Objective
Demonstrate that DPC-GNN generalizes across 4 tissue types spanning 3 orders of magnitude in stiffness (0.5→500 kPa) with ZERO architecture changes — only E and ν differ.

## Tissue Matrix

| ID | Tissue | E (Pa) | ν | C₁ (Pa) | D₁ (Pa) | D₁/C₁ | ε_trap window | Literature |
|----|--------|--------|---|---------|---------|--------|---------------|------------|
| T0 | Liver (baseline) | 4640 | 0.45 | 800.0 | 9833.3 | 12.3 | 0.054 | Nava 2008, Umale 2011 |
| T1 | Brain | 1000 | 0.49 | 168.0 | 27777.8 | 165.3 | 0.004 | Budday 2017, Miller 2000 |
| T2 | Kidney | 10000 | 0.45 | 1724.1 | 16666.7 | 9.7 | 0.069 | Nasseri 2002, Farshad 1999 |
| T3 | Myocardium | 30000 | 0.40 | 5357.1 | 25000.0 | 4.7 | 0.143 | Sommer 2015, Guccione 1991 |
| T4 | Cartilage | 500000 | 0.30 | 96153.8 | 416666.7 | 4.3 | 0.154 | Mansour 2003, Mow 1980 |

## Key Scientific Questions
1. Does the isochoric correction (Ī₁) eliminate the negative energy trap for ALL tissue types?
   - Cartilage has ε_trap=0.154 (5× larger than liver) — strongest test
2. Does DPC-GNN maintain sub-0.5mm phantom baseline across 3 orders of stiffness?
3. Do structural safety guarantees (Newton 3rd, energy conservation, J>0) hold universally?
4. Is there a stiffness regime where the architecture breaks down?

## Experimental Protocol

### For EACH tissue (T1-T4):

**Phase 1: Static Training (1000 epochs)**
- Identical to liver protocol
- Only change: E, NU values in training script
- Mesh: same 400-node, 1512-tet phantom
- Loss: corrected Neo-Hookean Ψ = C₁(Ī₁-3) + D₁(J-1)² + barrier

**Phase 2: Dynamic Training (full curriculum)**
- Short dynamic: 700 epochs (3→10 step windows)
- Long-horizon: 700 epochs (10→50 step windows)  
- Mixed-window fine-tuning: 200 epochs
- Total: ~2600 epochs per tissue

**Metrics (identical to liver experiments):**
1. Phantom Baseline Displacement (mm) — zero force
2. Force Sensitivity Ratio — u_max(5N) / u_max(0.1N)
3. J_min at 15-step and 50-step (worst case over 20 random forces)
4. Energy Drift (%)
5. Inference FPS
6. Training time

### Statistical Design
- n=20 random force configurations per metric per tissue
- Same statistical tests as main paper (Shapiro-Wilk → ANOVA/KW)
- Cross-tissue omnibus test on phantom baseline

## Code Changes Required

### File: phase_a/train_phase_a_v2_1.py (or equivalent)
```python
# ONLY these two lines change per tissue:
E = 1000.0   # Brain (was 4640.0)
NU = 0.49    # Brain (was 0.45)
```

### File: phase_d/finetune_d_v7.py
```python
# Same two lines:
E = 1000.0
NU = 0.49
```

### NO changes to:
- static_pignn_model.py (architecture)
- dynamic_pignn_model.py (architecture)
- mesh_utils.py (geometry)
- physics_loss.py (energy functional — automatically uses E, NU)
- verlet_integrator.py (time integration)

## Execution Plan

### Training Order (serial on 铁蛋儿 M3 Max):
1. T1 Brain (~90 min)
2. T2 Kidney (~90 min)
3. T3 Myocardium (~90 min)
4. T4 Cartilage (~90 min)
Total: ~6 hours

### Output Directory Structure:
```
~/workspace/DPC-GNN/multi_tissue/
  brain/
    checkpoints/
    results/
    eval_report.json
  kidney/
    ...
  myocardium/
    ...
  cartilage/
    ...
  summary_table.json
  fig_multi_tissue.png
```

## Paper Integration

### New Table (Table 7):
"Multi-tissue generalization: DPC-GNN performance across 4 tissue types
spanning 3 orders of magnitude in Young's modulus (1–500 kPa)"

| Tissue | E (kPa) | ν | Phantom (mm) | Sensitivity (×) | J_min (50-step) | Energy drift | FPS |
|--------|---------|---|-------------|-----------------|-----------------|-------------|-----|
| Liver  | 4.64    | 0.45 | 0.032 | 150.9× | +0.021 | 0% | 566 |
| Brain  | 1.0     | 0.49 | ? | ? | ? | ? | ? |
| Kidney | 10.0    | 0.45 | ? | ? | ? | ? | ? |
| Myocardium | 30.0 | 0.40 | ? | ? | ? | ? | ? |
| Cartilage | 500.0 | 0.30 | ? | ? | ? | ? | ? |

### New Figure:
Log-scale stiffness (x-axis) vs phantom baseline + force sensitivity (dual y-axis)
Showing flat performance across 3 orders of magnitude

### Discussion Addition (~2 paragraphs):
- Empirical validation of "modular energy functional" claim
- Negative energy trap window analysis across D₁/C₁ ratios
- Addresses "Single organ phantom" limitation

## FEM 对比验证（太森要求，必须执行）

### 每种组织都需要 MuJoCo Flex FEM 对照：
1. 同网格、同材料参数、同边界条件、同载荷
2. 输出 GNN/FEM 位移比（和肝脏的 ≈0.13 做对比）
3. Force-displacement 曲线对比
4. 3D 变形可视化（GNN vs FEM 并排）
5. 统计：n=20 random force configs, mean±SD

### 对照脚本：
- 复用 MuJoCo Flex 3.5.0（和论文 Section 5 一致）
- 每种组织需要单独的 MuJoCo XML 配置文件

## Success Criteria
- ALL tissues: phantom < 0.5mm
- ALL tissues: force sensitivity > 10×
- ALL tissues: energy drift = 0%
- At least 3/4 tissues: J_min > 0 at 50-step
- Cartilage: negative energy trap eliminated despite ε=0.154 window
- ALL tissues: FEM 对比数据完整（GNN/FEM ratio + force-displacement curve）

## Risk Assessment
- Brain (ν=0.49): D₁/C₁=165 → extreme volumetric stiffness, may need barrier tuning
- Cartilage (E=500kPa): 100× stiffer → CFL may need adjustment (check ω_max·Δt)
  - c = sqrt(500000/1060) ≈ 21.7 m/s → ω_max ≈ 1447 rad/s → ω·Δt ≈ 1.45
  - CFL = 1.45 < 2 ✅ but safety factor only 1.4× (vs liver's 14×)
  - May need Δt = 0.0005 for cartilage

---
Created: 2026-03-11
Author: 三丫 (experiment design) → Expert Council (code + execution)
