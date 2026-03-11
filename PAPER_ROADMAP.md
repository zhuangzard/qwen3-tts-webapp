# 论文路线图 (Paper Roadmap)

> 最后更新: 2026-03-11 14:15 EDT

---

## 📝 当前论文

### Paper 1: DPC-GNN MedIA Revision（进行中）
- **标题**: "DPC-GNN: Data-Free Physics-Constrained Graph Neural Network for Safe Dynamic Soft-Tissue Simulation"
- **期刊**: Medical Image Analysis（小修后录用，无需再次评审）
- **状态**: 🔄 Revision 中 — 多组织扩展实验
- **核心升级**:
  - [x] 原始肝脏实验（phantom 0.032mm, 566 FPS）
  - [x] MuJoCo→FEM ground truth 切换（+52%误差发现）
  - [x] 审查报告完成（AUDIT_REPORT.md）
  - [ ] 多组织验证（6种：脑/肾/心肌/软骨/血管/血液demo）
  - [ ] Level 1 横观各向同性骨组织（如时间允许则加 Level 2）
  - [ ] FEM 对比图重跑（Fig 3 + Fig 8）
  - [ ] 新小节：游戏引擎 vs 高精度FEM 精度讨论
  - [ ] SPH-GNN 血液 demo（写入但不重点展开）

---

## 🔜 后续论文

### Paper 2: SPH-GNN 心脑血管预测
- **建议标题**: "SPH-GNN: Data-Free Physics-Constrained Graph Neural Network for Cardiovascular Hemodynamics Prediction"
- **目标期刊**: Nature Biomedical Engineering / MICCAI
- **核心贡献**:
  - 首个纯物理驱动 SPH-GNN 血流仿真引擎
  - Carreau-Yasuda 非牛顿血液模型的无数据学习
  - 流固耦合（FSI）：统一 GNN 框架同时仿真血管壁+血流
  - 临床验证：WSS/OSI/FFR 预测 vs 4D Flow MRI
- **临床方向**: 中风/脑卒中风险预测、冠心病FFR虚拟评估、动脉瘤破裂预测、门静脉高压
- **技术基础**: SPH-GNN 代码框架已完成（7文件），Poiseuille+Womersley 验证中
- **TODO**:
  - [ ] Poiseuille 稳态验证完成
  - [ ] Womersley 脉动验证完成
  - [ ] 门静脉分叉几何
  - [ ] FSI 双向耦合实现
  - [ ] 临床数据获取（4D Flow MRI）
  - [ ] 论文初稿

### Paper 3: 多组织耦合仿真
- **建议标题**: "Unified Multi-Tissue Surgical Simulation via Physics-Constrained Graph Neural Networks"
- **目标期刊**: Nature Machine Intelligence / Science Robotics
- **核心贡献**:
  - 首个纯物理驱动的多组织联调 GNN 手术仿真框架
  - 共享权重 + 材料参数条件化：一个 GNN 同时仿真多种组织
  - 界面力学：组织间接触/连续/固定界面的统一处理
  - 零样本组合：训练时见过的单组织可自由组合成未见过的多组织场景
- **临床场景**:
  - 肝切除术：肝实质 + 门静脉 + 肝静脉 + 血液 + 器械
  - 膝关节镜：股骨(骨) + 关节软骨 + 半月板 + 滑液
  - 心脏手术：心肌 + 冠状动脉 + 血液 + 心包
- **技术基础**: Paper 1 提供单组织验证，Paper 2 提供 FSI 能力
- **TODO**:
  - [ ] 多组织耦合架构设计（统一图 / 分组织图+耦合层 / 条件化）
  - [ ] 界面力学实现（接触检测 + 力传递 + 损失分配）
  - [ ] 训练策略（预训练→微调 / 课程学习）
  - [ ] 肝切除术完整场景验证
  - [ ] 膝关节镜完整场景验证
  - [ ] 心脏手术完整场景验证
  - [ ] 与 SOFA Framework / FEBio 对比
  - [ ] 论文初稿

### Paper 4: 骨物理力学仿真
- **建议标题**: "AntiSym-SE3-GNN: SE(3)-Equivariant Physics-Constrained Graph Neural Network for Anisotropic Bone Mechanics"
- **目标期刊**: Nature Machine Intelligence / JMPS
- **核心贡献**:
  - SE(3) 等变消息传递 + 牛顿第三定律反对称约束的统一理论
  - 正交各向异性本构（9独立常数）的纯物理驱动学习
  - 从皮质骨(17 GPa)到松质骨(0.1-5 GPa)的跨尺度验证
  - Fabric tensor 驱动的微观→宏观各向异性预测
- **临床方向**: 骨折固定应力分析、脊柱融合术、关节置换应力屏蔽
- **技术基础**: Level 1-2 代码在 MedIA 中完成，Level 3 = SE(3)等变MP全新实现
- **TODO**:
  - [ ] Level 1 横观各向同性验证（MedIA中完成）
  - [ ] Level 2 正交各向异性验证（MedIA中完成）
  - [ ] Level 3 SE(3)等变MP架构设计与实现
  - [ ] 球谐函数(SH)消息分解 + 奇偶约束证明
  - [ ] 皮质骨/松质骨/椎体三种骨组织验证
  - [ ] FEBio/Abaqus ground truth 对比
  - [ ] 论文初稿

---

## 📊 论文矩阵总览

| # | 论文 | 刚度范围 | 物态 | 关键创新 | 期刊 | 状态 |
|---|------|---------|------|---------|------|------|
| 1 | DPC-GNN MedIA | 1kPa→500kPa | 固/管/流 | 纯物理+多组织泛化 | MedIA | 🔄 Revision |
| 2 | SPH-GNN 心脑血管 | 流体 | 血液+FSI | SPH+GNN血流动力学 | Nature BME | 📋 下一篇 |
| 3 | 多组织耦合 | 全范围 | 固+管+流+骨 | 统一多组织手术仿真 | NMI/SciRob | 📋 规划 |
| 4 | SE(3)骨力学 | 0.1→17 GPa | 骨 | SE(3)等变+各向异性 | NMI/JMPS | 📋 规划 |

### Paper 5: MPWM — Medical Physical World Model（初稿已有）
- **标题**: "PhysDrive Med Gym: A Medical Physical World Model for Physics-Guided Surgical Robot Learning"
- **目标期刊**: Nature Machine Intelligence
- **当前状态**: 初稿已完成（DPC-GNN-RL项目），目前内容仅肝脏单组织
- **GitHub**: `zhuangzard/DPC-GNN-RL` (private)
- **核心贡献**:
  - DPC-GNN 作为可微分物理引擎驱动 RL 策略学习
  - 物理梯度直接传播到策略网络（DiffPPO）
  - Medical Physical World Model 概念框架
  - 安全约束：log-barrier 保证仿真物理合法性
- **升级计划（用 Paper 1-4 成果丰富）**:
  - [ ] 从肝脏单组织 → 多组织场景（Paper 1 + Paper 3 成果）
  - [ ] 加入血流动力学约束（Paper 2 SPH-GNN）
  - [ ] 骨-软组织接触场景（Paper 4 骨力学）
  - [ ] 多组织手术全场景 RL 训练
  - [ ] 与 NVIDIA Isaac Gym / MuJoCo 手术 RL 对比
- **已有基础**:
  - DiffPPO v12b: 0.304mm 最佳（但 curriculum collapse 问题未解）
  - StdPPO baseline: success≈0.62-0.80, dist≈4.3mm
  - 113+ tests, v0.1.1 已发布
  - 8周救稿计划（NMI拒稿后重做）
- **TODO**:
  - [ ] 代码根本问题修复（pre-contact 梯度空洞）
  - [ ] 3条 prototype 路线验证（Null-Medium / Contact-Gated / Hybrid Planner）
  - [ ] 多 seed 完整实验（10-15 seeds + SAC/TD3 baseline）
  - [ ] Curriculum Collapse 系统实验
  - [ ] 多组织场景扩展
  - [ ] 论文重写

---

## 📊 论文矩阵总览

| # | 论文 | 刚度范围 | 物态 | 关键创新 | 期刊 | 状态 |
|---|------|---------|------|---------|------|------|
| 1 | DPC-GNN MedIA | 1kPa→500kPa | 固/管/流 | 纯物理+多组织泛化 | MedIA | 🔄 Revision |
| 2 | SPH-GNN 心脑血管 | 流体 | 血液+FSI | SPH+GNN血流动力学 | Nature BME | 📋 下一篇 |
| 3 | 多组织耦合 | 全范围 | 固+管+流+骨 | 统一多组织手术仿真 | NMI/SciRob | 📋 规划 |
| 4 | SE(3)骨力学 | 0.1→17 GPa | 骨 | SE(3)等变+各向异性 | NMI/JMPS | 📋 规划 |
| 5 | MPWM PhysDrive | 全范围 | 全物态+RL | 可微物理世界模型+手术RL | NMI | 🔄 重做中 |

**五篇论文构成完整的 MPWM (Medical Physical World Model) 体系：**

```
Paper 1 (MedIA) ─── 基础引擎 ──→ 证明 DPC-GNN 概念
    ↓
Paper 2 (Nature BME) ── 流体扩展 ──→ 心脑血管
    ↓                                    ↓
Paper 3 (NMI/SciRob) ── 系统集成 ──→ 多组织手术数字孪生
    ↓                                    ↓
Paper 4 (NMI/JMPS) ── 理论深度 ──→ SE(3)等变骨力学
    ↓                                    ↓
Paper 5 (NMI) ═══ 终极整合 ═══→ MPWM：可微物理世界模型 + 手术RL
```

- Paper 1 = 基础引擎（证明概念）
- Paper 2 = 流体扩展（心脑血管）
- Paper 3 = 系统集成（多组织手术数字孪生）
- Paper 4 = 理论深度（SE(3)等变+各向异性）
- Paper 5 = 终极整合（MPWM = Paper 1-4 全部成果 + RL 手术学习）

**总覆盖：1 kPa → 17 GPa = 7个数量级 × 固/管/流/骨 4种物态 × 各向同性→SE(3)等变 × 仿真→RL控制**

---

*路线图由三丫维护，太森审批*
