# 论文路线图 (Paper Roadmap)

> 最后更新: 2026-03-11 14:12 EDT

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

## 🔜 下一篇论文

### Paper 2: SPH-GNN 心脑血管预测（规划中）
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

### Paper 3: 骨物理力学仿真（规划中）
- **建议标题**: "AntiSym-SE3-GNN: SE(3)-Equivariant Physics-Constrained Graph Neural Network for Anisotropic Bone Mechanics"
- **目标期刊**: Nature Machine Intelligence / JMPS (Journal of the Mechanics and Physics of Solids)
- **核心贡献**:
  - SE(3) 等变消息传递 + 牛顿第三定律反对称约束的统一理论
  - 正交各向异性本构（9独立常数）的纯物理驱动学习
  - 从皮质骨(17 GPa)到松质骨(0.1-5 GPa)的跨尺度验证
  - Fabric tensor 驱动的微观→宏观各向异性预测
- **临床方向**: 骨折固定应力分析、脊柱融合术、关节置换应力屏蔽
- **技术基础**: Level 1-2 代码在 MedIA revision 中完成，Level 3 = SE(3)等变MP全新实现
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

| # | 论文 | 刚度范围 | 物态 | 本构模型 | 期刊 | 状态 |
|---|------|---------|------|---------|------|------|
| 1 | DPC-GNN MedIA | 1 kPa → 500 kPa | 固/管/流 | Neo-Hookean + TI | MedIA | 🔄 Revision |
| 2 | SPH-GNN 心脑血管 | 流体 | 血液 | SPH N-S + Carreau-Yasuda | Nature BME | 📋 规划 |
| 3 | AntiSym-SE3 骨力学 | 0.1 → 17 GPa | 骨 | 正交各向异性 + SE(3) | NMI/JMPS | 📋 规划 |

**三篇论文合计覆盖：1 kPa → 17 GPa = 7个数量级，固/管/流/骨全物态**

---

*路线图由三丫维护，太森审批*
