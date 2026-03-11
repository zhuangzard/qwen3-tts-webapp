# 🎯 Master TODO List

> 最后更新: 2026-03-11 14:25 EDT

---

## 🔴 紧急 (Urgent) — 等铁蛋儿恢复后立即执行

- [ ] **铁蛋儿恢复检查**：SSH连接 → 检查训练进度 → 确认数据完整性
- [ ] **重启训练管线**（串行，不再并行5个）：
  - [ ] Kidney Phase A-D v7
  - [ ] Myocardium Phase A-D v7
  - [ ] Cartilage Phase A-D v7
  - [ ] Poiseuille 500ep（SPH-GNN）
  - [ ] Womersley 200ep（SPH-GNN）
- [ ] **部署新代码到铁蛋儿**：
  - [ ] Level 1 TI 代码 → `~/workspace/DPC-GNN/multi_tissue/bone/`
  - [ ] Level 2 正交各向异性代码（完成后）
  - [ ] 同步所有报告到铁蛋儿对应目录
- [ ] **铁蛋儿 DPC-GNN repo commit+push**

---

## 🟡 Paper 1: DPC-GNN MedIA Revision（当前重点）

### 实验
- [ ] 多组织训练完成并收集结果表
  - [x] Brain（phantom=0.026mm, 10步J_min=+0.407）
  - [ ] Kidney
  - [ ] Myocardium
  - [ ] Cartilage
  - [ ] Vessel（Neo-Hookean Phase 1）
  - [ ] Blood（SPH-GNN Poiseuille + Womersley demo）
  - [ ] Bone（Level 1 TI，时间允许加 Level 2）
- [ ] FEM 对比实验重跑（用真实 Neo-Hookean FEM 替代 MuJoCo）
  - [ ] Fig 3 force-displacement 图
  - [ ] Fig 8 GNN vs FEM mesh 对比图
  - [ ] Table 6 FEM calibration RMSE（验证GT来源）
- [ ] 速度对比更新（566 FPS vs FEM 58s → 33,000×）

### 论文修改
- [ ] 按 AUDIT_REPORT.md 修改论文文本（Line 436/508/512/517/546/737/760-768/774）
- [ ] GNN/FEM ratio 更新：0.13 → 0.20
- [ ] 新增小节：游戏引擎 vs 高精度 FEM 精度讨论
- [ ] 多组织泛化结果表（6+种组织，3个数量级）
- [ ] SPH-GNN 血液 demo 段落（写入但不重点展开）
- [ ] Level 1 TI 骨组织结果段落

### 图表
- [ ] 多组织 phantom 对比图
- [ ] 多组织 J_min 对比图
- [ ] 刚度 vs 精度 曲线（1kPa→500kPa）

---

## 🟢 Paper 2: SPH-GNN 心脑血管（下一篇）

### 验证实验
- [ ] Poiseuille 稳态验证（< 10% 误差 vs 解析解）
- [ ] Womersley 脉动验证（< 15% 振幅误差）
- [ ] WSS 计算验证
- [ ] OSI 计算验证

### 扩展
- [ ] 门静脉分叉几何（Y形管）
- [ ] FSI 双向耦合（血管壁+血液）
- [ ] 临床数据获取（4D Flow MRI）

### 论文
- [ ] 初稿撰写
- [ ] 目标期刊：Nature Biomedical Engineering

---

## 🔵 Paper 3: 多组织耦合仿真

### 架构
- [ ] 方案B实现：分组织图 + 耦合层
- [ ] 界面力学：接触检测 + penalty method
- [ ] 课程学习策略：单组织→双组织→完整场景

### 临床场景
- [ ] 肝切除术（肝+门静脉+血液+器械）
- [ ] 膝关节镜（骨+软骨+半月板+滑液）
- [ ] 心脏手术（心肌+冠脉+血液+心包）

### 论文
- [ ] 初稿撰写
- [ ] 目标期刊：NMI / Science Robotics

---

## 🟣 Paper 4: SE(3)等变骨力学

### 代码
- [x] Level 1 横观各向同性（5常数）— 10/10 测试通过
- [ ] Level 2 正交各向异性（9常数）— Expert Council 进行中
- [ ] Level 3 SE(3)等变 MP — 下一篇独立实现

### 实验
- [ ] 皮质骨训练验证
- [ ] 松质骨训练验证（密度依赖）
- [ ] 椎体训练验证
- [ ] FEBio/Abaqus ground truth 对比

### 论文
- [ ] 初稿撰写
- [ ] 目标期刊：NMI / JMPS

---

## 🟤 Paper 5: MPWM PhysDrive Med Gym

### 代码修复
- [ ] Pre-contact 梯度空洞问题
- [ ] 3条 prototype 验证（Null-Medium / Contact-Gated / Hybrid）
- [ ] Curriculum Collapse 系统实验

### 扩展
- [ ] 从肝脏单组织 → 多组织场景（Paper 1+3 成果）
- [ ] 加入血流动力学约束（Paper 2）
- [ ] 多 seed 完整实验（10-15 seeds + SAC/TD3）

### 论文
- [ ] 重写（NMI拒稿后8周计划）
- [ ] 目标期刊：Nature Machine Intelligence

---

## 📁 文件索引

### 技术报告（`multi-tissue-experiment/`）
| 文件 | 内容 | 大小 |
|------|------|------|
| `BRAIN_TECHNICAL_REPORT.pdf` | 🧠 脑组织 | 215K |
| `KIDNEY_TECHNICAL_REPORT.pdf` | 🫘 肾组织 | 176K |
| `MYOCARDIUM_TECHNICAL_REPORT.pdf` | 🫀 心肌 | 179K |
| `CARTILAGE_TECHNICAL_REPORT.pdf` | 🦴 软骨 | 204K |
| `VESSEL_TECHNICAL_REPORT.pdf` | 🩸 血管 | 263K |
| `BLOOD_FLUID_TECHNICAL_REPORT.pdf` | 💉 血液SPH | 279K |
| `HARD_TISSUE_TECHNICAL_REPORT.pdf` | 🦴 硬组织各向异性 | 410K |
| `MULTI_TISSUE_COUPLING_REPORT.pdf` | 🔗 多组织耦合 | 1.4M |
| `SPEC.md` | 📋 实验规范 | — |

### 代码（`multi-tissue-experiment/code/`）
| 文件 | 行数 | Level | 测试 |
|------|------|-------|------|
| `ti_physics_loss.py` | 220 | L1 TI | ✅ |
| `anisotropic_edge_features.py` | 180 | L1 TI | ✅ |
| `bone_material_params.py` | 130 | L1 TI | ✅ |
| `test_ti_physics.py` | 250 | L1 测试 | 10/10 |
| `ortho_physics_loss.py` | — | L2 Ortho | 🔄 |

### 项目文档
| 文件 | 内容 |
|------|------|
| `PAPER_ROADMAP.md` | 5篇论文路线图 |
| `TODO.md` | 本文件 |

### 铁蛋儿文件（SSH恢复后同步）
| 位置 | 内容 |
|------|------|
| `~/workspace/DPC-GNN/paper/AUDIT_REPORT.md` | FEM审查报告 |
| `~/workspace/DPC-GNN/multi_tissue/fem_comparison/` | FEM对比数据 |
| `~/workspace/DPC-GNN/multi_tissue/blood-fluid/src/` | SPH-GNN 7个文件 |
| `~/workspace/DPC-GNN/multi_tissue/vessel/` | 血管代码+报告 |
| `~/workspace/DPC-GNN/multi_tissue/brain/` | 脑组织训练结果 |

---

*TODO 由三丫维护，太森审批 | 完成项打 [x] 标记*
