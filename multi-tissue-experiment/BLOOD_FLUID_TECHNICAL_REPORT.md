# DPC-GNN 血液流体仿真技术报告

**版本**: v1.0  
**日期**: 2026-03-11  
**作者**: 三丫 Research + 6-Expert Council  
**目标**: 为 DPC-GNN 扩展到血液流体仿真提供完整理论基础、技术方案和验证计划

---

## 1. 背景与动机

### 1.1 为什么要做血液仿真

DPC-GNN 当前覆盖：
- **实心组织**: 肝脏、脑、肾、心肌、软骨（Neo-Hookean 弹性体）
- **薄壁结构**: 血管（管状四面体 + 内压）

缺失的关键物态：**流体**。血液是手术仿真中不可或缺的组成部分：
- 肝切除术中的出血预测
- 门静脉血流动力学（决定肝脏灌注质量）
- 心脑血管疾病预测（中风、脑卒中、动脉瘤破裂风险）

如果 DPC-GNN 能同时仿真固体（组织）+ 薄壁（血管壁）+ 流体（血液），论文叙事从 "soft tissue simulator" 升级为 **"multi-physics medical world model"**。

### 1.2 临床应用前景（下一篇论文核心方向）

| 应用 | 关键指标 | 临床价值 |
|------|---------|---------|
| 脑卒中风险预测 | WSS（壁面剪切应力）分布 | WSS < 0.4 Pa 区域为血栓高危区 |
| 动脉瘤破裂风险 | OSI（振荡剪切指数）| OSI > 0.3 为高风险 |
| FFR 虚拟评估 | 血流储备分数 | 替代有创冠脉造影 |
| 门静脉高压 | 压力梯度 | 肝硬化分期、术前评估 |
| 中风后康复预测 | 脑灌注分布 | 缺血区域定位 |

---

## 2. 物理框架：SPH-GNN

### 2.1 为什么选 SPH（Smoothed Particle Hydrodynamics）

**6位专家一致推荐 SPH**，评分 4.20/5（可行性矩阵最优选）。

SPH 和 DPC-GNN 的对应关系：

| SPH 概念 | DPC-GNN 对应 | 兼容性 |
|----------|-------------|--------|
| 粒子 | GNN 节点 | **天然对应** |
| 粒子间相互作用 | 图的边 | **天然对应** |
| $F_{ij} = -F_{ji}$（核函数对称性）| AntisymmetricMP | **完美匹配** |
| 无网格 | 图结构动态重建 | 兼容 |
| Lagrangian 框架 | DPC-GNN 已有 | 一致 |

**替代方案排除理由：**
- **Euler 网格法**：网格固定，流体穿过——与 GNN 的节点追踪模式不兼容
- **LBM（Lattice Boltzmann）**：规则网格，不适合复杂血管几何
- **PINN**：直接拟合 PDE 残差，无法利用 AntisymmetricMP 的架构优势
- **ALE**：混合方法可行但实现复杂度远超 SPH

### 2.2 SPH 基本方程

#### 核函数（Wendland C2）

$$W(r, h) = \alpha_d \left(1 - \frac{r}{2h}\right)^4 \left(1 + \frac{2r}{h}\right), \quad r < 2h$$

其中 $\alpha_d = \frac{21}{16\pi h^3}$（3D 归一化常数，经数值积分验证 $\int W \, dV = 0.999998$）。

**关键性质：**
- 对称性：$W_{ij} = W_{ji}$（保证质量守恒）
- 梯度反对称：$\nabla W_{ij} = -\nabla W_{ji}$（保证动量守恒 = AntisymmetricMP）
- 紧支撑：$r > 2h$ 时 $W = 0$（稀疏图，计算高效）

#### Navier-Stokes 方程（SPH 离散化）

**连续性方程（质量守恒）：**
$$\frac{d\rho_i}{dt} = \sum_j m_j (\mathbf{v}_i - \mathbf{v}_j) \cdot \nabla W_{ij}$$

**动量方程：**
$$\frac{d\mathbf{v}_i}{dt} = -\sum_j m_j \left(\frac{p_i}{\rho_i^2} + \frac{p_j}{\rho_j^2}\right) \nabla W_{ij} + \nu_{eff} \nabla^2 \mathbf{v}_i + \mathbf{g}$$

**核心观察：** 压力项 $-m_j\left(\frac{p_i}{\rho_i^2} + \frac{p_j}{\rho_j^2}\right)\nabla W_{ij}$ 天然满足 $F_{ij} = -F_{ji}$——因为 $\nabla W_{ij} = -\nabla W_{ji}$，且系数关于 $i, j$ 对称。这和 AntisymmetricMP 的架构约束**数学上完全一致**。

#### 状态方程（弱可压缩）

$$p = c^2(\rho - \rho_0)$$

其中 $c = 15$ m/s（人工声速，约 10× 最大流速），$\rho_0 = 1060$ kg/m³。

弱可压缩 SPH 避免了求解 Poisson 方程（计算瓶颈），代价是允许密度波动 ~1%（临床可接受）。

### 2.3 血液流变学：Carreau-Yasuda 非牛顿模型

血液不是简单的牛顿流体——它在低剪切率下粘度高（红细胞聚集），高剪切率下粘度低（红细胞变形排列）。

$$\mu_{eff}(\dot{\gamma}) = \mu_\infty + (\mu_0 - \mu_\infty)\left[1 + (\lambda\dot{\gamma})^a\right]^{(n-1)/a}$$

| 参数 | 值 | 物理含义 |
|------|-----|---------|
| $\mu_\infty$ | 0.0035 Pa·s | 高剪切极限粘度（大动脉主流区） |
| $\mu_0$ | 0.16 Pa·s | 低剪切极限粘度（滞流区/回流区） |
| $\lambda$ | 8.2 s | 松弛时间常数 |
| $n$ | 0.2128 | 幂律指数（<1 = 剪切变稀） |
| $a$ | 0.64 | 牛顿-幂律过渡参数 |

**为什么选 Carreau-Yasuda 而非 Casson/Power-Law：**
- Carreau-Yasuda 在全剪切率范围 ($\dot{\gamma} = 0 \to \infty$) 连续可微
- 梯度连续性对 GNN 反向传播至关重要（Casson 模型在 $\dot{\gamma} = 0$ 不可微）
- 文献验证最充分（Cho & Kensey 1991, 5000+ citations）

### 2.4 与 Neo-Hookean 的物理损失对比

| | Neo-Hookean（固体） | SPH（流体） |
|--|---------------------|------------|
| **物理量** | 位移 $\mathbf{u}$ | 速度 $\mathbf{v}$、密度 $\rho$、压力 $p$ |
| **方程类型** | 平衡方程（时间无关） | 演化方程（时间步进） |
| **损失函数** | $\Pi = \sum \Psi(F)V_0 - \sum f \cdot u$ | $L = L_{mass} + L_{mom} + L_{div}$ |
| **守恒律** | 牛顿三定律（反对称MP） | 质量+动量守恒（反对称MP + 核对称） |
| **训练模式** | 每步独立最小化 | BPTT 时间窗口 |

**损失函数具体形式：**

$$L_{mass} = \sum_i \left|\frac{d\rho_i}{dt} + \rho_i \nabla \cdot \mathbf{v}_i\right|^2$$

$$L_{mom} = \sum_i \left|\rho_i \frac{d\mathbf{v}_i}{dt} - \mathbf{F}_{pressure,i} - \mathbf{F}_{viscous,i}\right|^2$$

$$L_{div} = \sum_i |\nabla \cdot \mathbf{v}_i|^2 \quad \text{（增强不可压缩性约束）}$$

$$L_{total} = w_{mass} L_{mass} + w_{mom} L_{mom} + w_{div} L_{div}$$

---

## 3. GNN 架构设计

### 3.1 SPH-GNN 模型架构

```
输入层 (9D):
  position(3) + velocity(3) + density(1) + pressure(1) + particle_type(1)
     ↓
Encoder MLP: 9D → 96D
     ↓
AntisymmetricMP × 5 层 (复用 DPC-GNN 架构)
  边特征 (11D): r_ij(3) + |r_ij|(1) + v_ij(3) + W_ij(1) + ∇W_ij(3)
  消息: m_ij = MLP(h_i, h_j, e_ij),  m_ji = -m_ij
     ↓
Decoder MLP: 96D → 3D (加速度预测 a_i)
     ↓
时间积分 (Symplectic Euler):
  v^(n+1) = v^n + dt × a
  x^(n+1) = x^n + dt × v^(n+1)
  ρ^(n+1) = ρ^n + dt × (dρ/dt)
```

**参数量：304,707**（hidden_dim=96, n_mp_layers=5），和 DPC-GNN 实心组织模型完全一致。

### 3.2 边界条件处理

| 粒子类型 | 处理方式 |
|----------|---------|
| 流体粒子 | GNN 预测加速度 $a_i$ |
| 壁粒子 | $a = 0$（固定），参与近邻图但不更新 |
| 入口粒子 | 设定速度 profile（Poiseuille/Womersley） |
| 出口粒子 | 零梯度 BC：$\partial \mathbf{v}/\partial n = 0$ |

### 3.3 近邻图动态重建

和固体不同，流体粒子位置时刻变化，近邻图需要动态更新：

- **重建频率**：每 $N_{rebuild}$ 步（典型值 5-10）
- **cutoff 半径**：$r_{cut} = 2h$（SPH 核紧支撑半径）
- **实现**：基于 cell-list 的 O(N) 近邻搜索

---

## 4. 管状圆柱域设计

### 4.1 粒子域参数（门静脉）

```
内径 D_int = 7 mm
长度 L = 80 mm
粒子间距 dp = 1.0 mm（测试） / 0.5 mm（生产）
核光滑长度 h = 1.3 × dp

测试分辨率 (dp=1.0mm):
  流体粒子 ≈ 2,400
  壁粒子 ≈ 1,500
  入口/出口粒子 ≈ 200
  总粒子 ≈ 4,100

生产分辨率 (dp=0.5mm):
  流体粒子 ≈ 19,200
  壁粒子 ≈ 6,000
  总粒子 ≈ 28,000
```

### 4.2 血液物理参数

| 参数 | 值 | 来源 |
|------|-----|------|
| 密度 $\rho_0$ | 1060 kg/m³ | 全血 |
| 动力粘度（高剪切）$\mu_\infty$ | 0.0035 Pa·s | Cho & Kensey 1991 |
| 动力粘度（低剪切）$\mu_0$ | 0.16 Pa·s | Cho & Kensey 1991 |
| 人工声速 $c$ | 15 m/s | ≈10× 门静脉峰值流速 |
| 门静脉平均流速 | 15-20 cm/s | Moriyasu 1986 |
| 门静脉 Reynolds 数 | Re ≈ 530 | 层流（Re < 2300） |
| Womersley 数 | Wo ≈ 3-5 | 弱脉动 |

**门静脉是层流**（Re ≈ 530 << 2300），这大大简化了仿真——不需要湍流模型。

---

## 5. 验证方案

### 5.1 Poiseuille 稳态管流（Demo 1）

**设置：** 直管，入口压差 $\Delta p$，两端壁固定

**解析解：**
$$v(r) = \frac{\Delta p}{4\mu L}(R^2 - r^2)$$

其中 $R$ = 管内径/2, $L$ = 管长, $\mu$ = 动力粘度。

**最大速度（管中心）：**
$$v_{max} = \frac{\Delta p R^2}{4\mu L}$$

**体积流量：**
$$Q = \frac{\pi R^4 \Delta p}{8\mu L} \quad \text{(Hagen-Poiseuille)}$$

**验证指标：**
| 指标 | 成功标准 |
|------|---------|
| 速度 profile 误差 vs 解析解 | < 10% |
| 流量误差 | < 5% |
| 密度波动 $|\rho - \rho_0|/\rho_0$ | < 1% |

**当前状态：** 500 epochs 训练中（铁蛋儿后台运行）

### 5.2 Womersley 脉动流（Demo 2）

**设置：** 脉动压差 $\Delta p(t) = \Delta p_0 \sin(\omega t)$，周期 $T = 0.8$ s（心跳）

**Womersley 解析解（涉及 Bessel 函数）：**
$$v(r, t) = \text{Re}\left[\frac{\Delta p_0}{i\omega\rho}\left(1 - \frac{J_0(\alpha r/R \cdot i^{3/2})}{J_0(\alpha \cdot i^{3/2})}\right)e^{i\omega t}\right]$$

其中 $\alpha = R\sqrt{\omega\rho/\mu}$ 为 Womersley 数，$J_0$ 为零阶 Bessel 函数。

**验证指标：**
| 指标 | 成功标准 |
|------|---------|
| 相位差 vs Womersley 解 | < 5° |
| 振幅衰减比 | 误差 < 15% |
| WSS 时间平均值 | 误差 < 20% |

**当前状态：** 200 epochs 训练中（铁蛋儿后台运行）

### 5.3 临床指标计算

训练完成后，从 SPH-GNN 输出计算临床指标：

**壁面剪切应力 WSS：**
$$\text{WSS} = \mu_{eff} \frac{\partial v_{tangential}}{\partial n}\bigg|_{wall}$$

**振荡剪切指数 OSI：**
$$\text{OSI} = \frac{1}{2}\left(1 - \frac{|\int_0^T \boldsymbol{\tau}_w \, dt|}{\int_0^T |\boldsymbol{\tau}_w| \, dt}\right)$$

**相对滞留时间 RRT：**
$$\text{RRT} = \frac{1}{(1 - 2 \cdot \text{OSI}) \cdot \overline{\text{WSS}}}$$

---

## 6. 流固耦合（FSI）展望

### 6.1 统一 GNN 架构

DPC-GNN 血管壁（固体节点）+ SPH-GNN 血液（流体粒子）可以在**统一的图**中耦合：

```
固体节点（血管壁）──── 固体边（弹性力）
    |
界面边（压力/剪切力传递）
    |
流体粒子（血液）──── 流体边（SPH 力）
```

**AntisymmetricMP 同时编码：**
- 固体子图：弹性力（Neo-Hookean / HGO）
- 流体子图：SPH 压力力 + 粘性力
- 界面边：no-slip BC + 压力耦合

### 6.2 实现路线（下一篇论文）

| 阶段 | 内容 | 时间 |
|------|------|------|
| Phase 1 | 单向耦合：流体→壁（压力载荷） | 2周 |
| Phase 2 | 双向耦合：壁变形→流体域更新 | 4周 |
| Phase 3 | 完整 FSI：脉动流 + 弹性壁 | 2月 |
| Phase 4 | 临床验证：门静脉分叉 + CT 数据 | 3月 |

---

## 7. 论文定位

### 7.1 当前 MedIA 论文

**定位：** 展示能力，不重点展开。

在多组织泛化实验的最后，加一段：

> "Beyond solid tissues and thin-walled structures, we extend DPC-GNN to fluid simulation through an SPH-GNN formulation, where SPH particle interactions naturally satisfy the antisymmetric force constraint ($F_{ij} = -F_{ji}$) guaranteed by the kernel gradient symmetry $\nabla W_{ij} = -\nabla W_{ji}$, which is mathematically identical to the AntisymmetricMP architecture. Preliminary validation on Poiseuille steady-state flow and Womersley pulsatile flow demonstrates [X]% velocity profile accuracy against analytical solutions, confirming the generalizability of the physics-constrained paradigm to fluid dynamics."

### 7.2 下一篇论文（重点深挖）

**建议标题：**
> "SPH-GNN: Data-Free Physics-Constrained Graph Neural Network for Cardiovascular Hemodynamics Prediction"

**目标期刊：** Nature Biomedical Engineering / Nature Medicine / MICCAI

**核心贡献：**
1. 首个纯物理驱动的 SPH-GNN 血流仿真引擎
2. Carreau-Yasuda 非牛顿血液模型的无数据学习
3. 流固耦合：统一 GNN 框架同时仿真血管壁和血流
4. 临床验证：WSS/OSI/FFR 预测 vs 4D Flow MRI

**临床场景（按影响力排序）：**
1. **脑卒中风险预测**：颈动脉分叉 WSS 分布 → 斑块破裂风险
2. **冠心病 FFR 虚拟评估**：替代有创冠脉造影（年市场 $2B+）
3. **动脉瘤破裂预测**：脑动脉瘤 OSI/RRT → 手术决策
4. **门静脉高压评估**：肝硬化分期 + 术前模拟
5. **中风后脑灌注预测**：缺血区域定位 + 康复规划

---

## 8. 代码实现状态

### 8.1 已完成文件

| 文件 | 行数 | 位置 | 状态 |
|------|------|------|------|
| `sph_domain.py` | 320 | `blood-fluid/src/` | ✅ 自测通过 |
| `sph_kernels.py` | 295 | `blood-fluid/src/` | ✅ 核归一化 0.999998 |
| `sph_physics_loss.py` | 640 | `blood-fluid/src/` | ✅ 零速度→零残差 |
| `sph_gnn_model.py` | 525 | `blood-fluid/src/` | ✅ 304K参数，MPS可用 |
| `sph_integrator.py` | 490 | `blood-fluid/src/` | ✅ Symplectic Euler |
| `poiseuille_test.py` | 350 | `blood-fluid/src/` | 🔄 500ep训练中 |
| `womersley_test.py` | 430 | `blood-fluid/src/` | 🔄 200ep训练中 |

### 8.2 技术验证

| 验证项 | 结果 |
|--------|------|
| 核归一化 $\int W \, dV$ | 0.999998 ✅ |
| 梯度反对称 $\nabla W_{ij} + \nabla W_{ji}$ | < 1e-6 ✅ |
| 零速度场 → 零残差 | ✅ |
| GNN 前向传播 + 梯度流通 | ✅ |
| 端到端管线（domain→核→损失→GNN→积分） | ✅ |

---

## 参考文献

1. Monaghan, J.J. (2005). Smoothed particle hydrodynamics. *Reports on Progress in Physics*, 68:1703.
2. Sanchez-Gonzalez, A. et al. (2020). Learning to Simulate Complex Physics with Graph Networks. *ICML*.
3. Pfaff, T. et al. (2021). Learning Mesh-Based Simulation with Graph Networks. *ICLR*.
4. Cho, Y.I. & Kensey, K.R. (1991). Effects of the non-Newtonian viscosity of blood on flows in a diseased arterial vessel. *Biorheology*, 28:241-262.
5. Kissas, G. et al. (2020). Machine learning in cardiovascular flows modeling. *Computer Methods in Applied Mechanics and Engineering*.
6. Arzani, A. et al. (2021). Data-driven cardiovascular flow modelling: examples and opportunities. *J. Royal Society Interface*.
7. Holzapfel, G.A. (2000). *Nonlinear Solid Mechanics*. Wiley.
8. Gasser, T.C., Ogden, R.W., Holzapfel, G.A. (2006). J. Royal Society Interface, 3(6):15-35.

---

*报告生成：DPC-GNN 6-Expert Council | 三丫研究助手*
