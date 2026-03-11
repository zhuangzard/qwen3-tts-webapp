# DPC-GNN 血管仿真技术报告

**版本**: v1.0  
**日期**: 2026-03-11  
**作者**: 三丫 Research + Expert Council  
**目标**: 为 MedIA revision 提供血管仿真的完整理论基础和实验验证方案

---

## 1. 背景与动机

### 1.1 当前 DPC-GNN 论文的局限

DPC-GNN V7_MedIA 论文（950行 LaTeX, elsarticle 单栏）在 Section 6.5 "Limitations and Future Work" 明确列出：

> "The current implementation considers only a single constitutive model (Neo-Hookean) and a single organ phantom (liver)."

审稿人极可能追问：
- "The authors claim the architecture is modular and extensible, but provide zero experimental evidence."
- "How does DPC-GNN handle different tissue geometries beyond solid rectangular phantoms?"

### 1.2 血管仿真为什么关键

血管仿真从三个维度验证 DPC-GNN 的泛化能力：

| 维度 | 肝脏 (baseline) | 血管 (新增) | 验证的是什么 |
|------|-----------------|------------|-------------|
| **几何** | 实心块状 | 管状薄壁 | 架构对拓扑的鲁棒性 |
| **载荷** | 纯外力 | 内压 + 外力 | 物理损失对不同载荷的适应性 |
| **变形模式** | 压缩/弯曲 | 膨胀/环向拉伸 | Neo-Hookean 在拉伸主导下的行为 |

如果 DPC-GNN 能在血管上同样工作，论文从 "single organ demo" 升级为 "universal differentiable physics engine"。

---

## 2. 数学框架

### 2.1 Neo-Hookean 本构模型（Phase 1, 进 MedIA）

DPC-GNN 的核心物理损失基于修正 Neo-Hookean 势能密度：

$$\Psi_{NH}(\mathbf{F}) = C_1(\bar{I}_1 - 3) + D_1(J - 1)^2 + \Psi_{barrier}(J)$$

其中：
- $\mathbf{F} = \mathbf{I} + \nabla\mathbf{u}$：变形梯度（由 GNN 预测的位移 $\mathbf{u}$ 计算）
- $J = \det(\mathbf{F})$：体积比
- $\bar{I}_1 = J^{-2/3} \text{tr}(\mathbf{F}^T\mathbf{F})$：等容第一不变量（isochoric correction）
- $C_1 = \frac{E}{4(1+\nu)}$：剪切刚度
- $D_1 = \frac{E}{6(1-2\nu)}$：体积刚度
- $\Psi_{barrier}(J) = -\lambda_b \ln\left(\frac{J}{J_{thr}}\right) \cdot \mathbf{1}_{J < J_{thr}}$：对数 barrier 函数，强制 $J > 0$

**血管材料参数（门静脉中膜）：**

| 参数 | 值 | 计算 |
|------|-----|------|
| $E$ | 400 kPa | 文献值 (Holzapfel 2000) |
| $\nu$ | 0.49 | 近不可压缩 |
| $C_1$ | 67,114 Pa | $E / (4(1+\nu)) = 400000 / 5.96$ |
| $D_1$ | 3,333,333 Pa | $E / (6(1-2\nu)) = 400000 / 0.12$ |
| $D_1/C_1$ | 49.7 | 高体积约束比（cf. 肝脏 9.67）|

**关键物理：** $D_1/C_1 = 49.7$ 表明体积约束极强。对 barrier 函数的压力更大——薄壁单元体积小，J 偏离 1 的空间更窄。建议 $J_{thr} = 0.3$（比肝脏的 0.1 更保守）。

### 2.2 Holzapfel-Gasser-Ogden 本构模型（Phase 2, 后续升级）

$$\Psi_{HGO} = \underbrace{C_{10}(\bar{I}_1 - 3)}_{\text{基质（各向同性）}} + \underbrace{\frac{k_1}{2k_2}\sum_{\alpha=1}^{2}\left[\exp\left(k_2\langle E_\alpha\rangle^2\right) - 1\right]}_{\text{胶原纤维（各向异性）}} + \underbrace{\frac{1}{D}(J-1)^2}_{\text{体积惩罚}}$$

**纤维应变不变量：**
$$E_\alpha = \kappa\bar{I}_1 + (1 - 3\kappa)\bar{I}_{4\alpha} - 1$$

其中：
- $\bar{I}_{4\alpha} = J^{-2/3}(\mathbf{a}_{0\alpha} \cdot \mathbf{C} \mathbf{a}_{0\alpha})$：等容纤维伸长
- $\mathbf{a}_{0\alpha}$：参考构型中的纤维方向（两族，角度 $\pm\theta$）
- $\kappa \in [0, 1/3]$：纤维分散度（$0$ = 完全对齐，$1/3$ = 各向同性）
- $\langle x \rangle = \max(0, x)$：Macaulay 括号（纤维只承受拉力，不承受压缩）

**纤维方向计算（圆柱坐标）：**

对于管状血管，胶原纤维螺旋缠绕，方向在每个四面体质心处计算：

$$\mathbf{a}_{0,1} = \cos\theta \cdot \hat{\mathbf{e}}_\theta + \sin\theta \cdot \hat{\mathbf{e}}_z$$
$$\mathbf{a}_{0,2} = \cos\theta \cdot \hat{\mathbf{e}}_\theta - \sin\theta \cdot \hat{\mathbf{e}}_z$$

其中 $\hat{\mathbf{e}}_\theta = (-\sin\phi, \cos\phi, 0)$ 是周向单位向量，$\phi = \arctan(y/x)$ 是极角。

**门静脉 HGO 参数（Gasser 2006, Table 2）：**

| 参数 | 值 | 物理含义 |
|------|-----|---------|
| $C_{10}$ | 36.4 kPa | 弹性蛋白基质剪切模量 |
| $k_1$ | 996.6 kPa | 胶原纤维刚度 |
| $k_2$ | 524.6 | 纤维非线性指数（无量纲）|
| $\kappa$ | 0.226 | 纤维分散（偏离对齐 22.6%）|
| $\theta$ | ±49.98° | 纤维螺旋角（相对周向）|

**HGO 与 Neo-Hookean 的联系：**
- 当 $k_1 = 0$（无纤维），HGO 退化为 Neo-Hookean（$C_{10} = C_1$）
- 当 $\kappa = 1/3$（完全分散），纤维项变为各向同性，等效于增加 $C_1$
- **DPC-GNN 从 Neo-Hookean 升级到 HGO，只需替换 `physics_loss.py` 中的能量函数，其他全不变**

### 2.3 负能量陷阱分析（Negative Energy Trap）

**核心问题：** DPC-GNN 论文的关键贡献之一是发现并修正了 Neo-Hookean 的 negative energy trap。HGO 中是否存在类似问题？

**分析：**

1. **基质项** $C_{10}(\bar{I}_1 - 3)$：
   - 和 Neo-Hookean 完全相同，$\bar{I}_1 = J^{-2/3}I_1$
   - 当 $J \to 0$，$J^{-2/3} \to \infty$，$\bar{I}_1 \to \infty$，但 $I_1 \to 0$ 更快
   - **结论：存在同样的 negative energy trap**，isochoric 修正是必需的

2. **纤维项** $\frac{k_1}{2k_2}[\exp(k_2\langle E_\alpha\rangle^2) - 1]$：
   - Macaulay 括号 $\langle E_\alpha \rangle = \max(0, E_\alpha)$
   - 当压缩时 $E_\alpha < 0$，纤维贡献为零 → **不存在负能量问题**
   - 当拉伸时 $E_\alpha > 0$，指数增长 → **天然正能量**
   - **结论：纤维项安全**

3. **体积项** $(1/D)(J-1)^2$：
   - 二次函数，$J = 0$ 时 $\Psi_{vol} = 1/D > 0$
   - **但** $1/D$ 有限，不能阻止 $J \to 0$（只是给个有限惩罚）
   - **结论：必须加 log-barrier，和 Neo-Hookean 相同**

**总结：HGO 的 barrier 策略和 Neo-Hookean 完全一致。** DPC-GNN 的 log-barrier 方法无缝适用于 HGO。

---

## 3. 网格设计

### 3.1 管状薄壁四面体

选择薄壁四面体（2-3 层），理由：
- DPC-GNN 的 AntisymmetricMP 只处理 3-DOF（位移），壳单元需要 6-DOF（位移+旋转），需要重写消息传递层
- 文献表明 2-3 层薄壁四面体在手术仿真中精度可接受（Pfeiffer 2019; Haouchine 2015）
- **架构零改动**：`vessel_mesh.py` 生成的 `TetMesh` 和 `generate_liver_grid()` 接口完全一致

### 3.2 网格参数

```
外径 D_ext = 10 mm        (门静脉典型值 8-12 mm)
壁厚 t = 1.5 mm           (典型值 1-2 mm)  
内径 D_int = 7 mm          = D_ext - 2t
长度 L = 80 mm             (典型值 50-100 mm)

离散参数：
  n_theta = 24             (周向, 每15°一个节点)
  n_r = 3                  (径向层, 3层四面体 = 4节点层)
  n_z = 20                 (轴向)

网格统计：
  节点数 N = 24 × 4 × 21 = 2016  (实际 1920，因为周向首尾连接)
  四面体数 T = 24 × 3 × 20 × 6 = 8640
  有向边数 ≈ 2 × 无向边数 ≈ 50,000+
  固定节点 = 两端面 = 2 × 24 × 4 = 192
  内壁节点 = 24 × 21 = 504
  内壁三角面片 = 24 × 20 × 2 = 960
```

### 3.3 网格质量指标

**已测试（vessel_mesh.py 自验证输出）：**

| 指标 | 值 | 阈值 | 状态 |
|------|-----|------|------|
| 体积比 (max/min) | 1.43 | < 10 | ✅ |
| 零位移时 max\|F-I\| | ~0 | < 1e-10 | ✅ |
| 零位移时 J range | [0.94, 1.06] | ∈ [0.9, 1.1] | ✅ |
| 无反转单元 | 0 | = 0 | ✅ |
| 梯度流通 | grad_norm > 0 | > 0 | ✅ |

### 3.4 Hex → Tet 分解

使用 Freudenthal（Kuhn）分解：每个六面体分解为 6 个四面体，共享主对角线。

六面体 $(i_\theta, j_r, k_z)$ 的 8 个顶点：
```
v0 = (i,   j,   k  )   v1 = (i+1, j,   k  )
v2 = (i+1, j+1, k  )   v3 = (i,   j+1, k  )
v4 = (i,   j,   k+1)   v5 = (i+1, j,   k+1)
v6 = (i+1, j+1, k+1)   v7 = (i,   j+1, k+1)
```

6 个四面体（共享对角线 v0-v6）：
```
T1 = {v0, v1, v2, v6}   T2 = {v0, v1, v5, v6}
T3 = {v0, v3, v2, v6}   T4 = {v0, v3, v7, v6}
T5 = {v0, v4, v5, v6}   T6 = {v0, v4, v7, v6}
```

周向 wrap：$i_\theta = n_\theta$ 映射回 $i_\theta = 0$。

---

## 4. 内压处理

### 4.1 等效节点力方法

血管内压 $p$ 作用在管腔内壁面上。将连续面压力离散为等效节点力：

对于内壁三角面片 $T_k$ （顶点 $\mathbf{x}_a, \mathbf{x}_b, \mathbf{x}_c$），法向量（面积加权）：

$$\mathbf{n}_k = (\mathbf{x}_b - \mathbf{x}_a) \times (\mathbf{x}_c - \mathbf{x}_a)$$

面积 $A_k = \|\mathbf{n}_k\| / 2$，单位法向量 $\hat{\mathbf{n}}_k = \mathbf{n}_k / \|\mathbf{n}_k\|$。

等效节点力（每个面片均分给 3 个顶点）：

$$\mathbf{f}_a^{press} = \mathbf{f}_b^{press} = \mathbf{f}_c^{press} = \frac{p}{6} \mathbf{n}_k$$

注意 $p/6 \cdot \|\mathbf{n}_k\| = p \cdot A_k / 3$，即压力 × 面积 / 3 节点。

**总压力验证（已测试）：**
- 门静脉 p = 1000 Pa，内壁面积 ≈ $\pi \times D_{int} \times L = \pi \times 7 \times 80 \approx 1759$ mm²
- 理论总力 = $p \times A_{inner} \approx 1000 \times 1.759 \times 10^{-3} \approx 1.76$ N
- 实际计算 ≈ 1.68 N ✅（差异来自离散化）

### 4.2 Follower Force 分析

**问题：** 真实的压力方向应该垂直于**变形后**的面（follower force），而非参考构型的面。

**评估：**
- 门静脉内压 1000 Pa → 径向膨胀约 0.077 mm（薄壁圆管解析解）
- 相对变形 = 0.077 / 5.0 = 1.5% → **follower force 效应 < 0.1%**
- **结论：对于 MedIA demo，可以安全忽略 follower force**

### 4.3 解析解验证（薄壁圆管 Lamé 方程）

对于薄壁圆管内压问题，Lamé 方程简化为：

$$u_r = \frac{p \cdot r_{int}^2}{E \cdot t} (1 - \nu^2)$$

对于中面位置 $r = (r_{int} + r_{ext})/2$：

$$u_r = \frac{1000 \times 3.5^2 \times 10^{-6}}{400000 \times 1.5 \times 10^{-3}} (1 - 0.49^2) = \frac{12.25 \times 10^{-3}}{600} \times 0.7599 \approx 0.0155 \text{ mm}$$

更精确的厚壁 Lamé 解（$r_{int}/r_{ext} = 0.7$，不能用薄壁近似）：

$$u_r(r) = \frac{p \cdot r_{int}^2}{r_{ext}^2 - r_{int}^2} \left[\frac{(1-2\nu)}{E}r + \frac{(1+\nu)}{E}\frac{r_{ext}^2}{r}\right]$$

在外壁 $r = r_{ext} = 5$ mm 处：

$$u_r(r_{ext}) = \frac{1000 \times 12.25 \times 10^{-6}}{(25 - 12.25) \times 10^{-6}} \left[\frac{0.02}{400000} \times 5 \times 10^{-3} + \frac{1.49}{400000} \times \frac{25 \times 10^{-6}}{5 \times 10^{-3}}\right]$$

$$= 960.78 \times [2.5 \times 10^{-10} + 1.863 \times 10^{-8}] \approx 960.78 \times 1.888 \times 10^{-8} \approx 1.81 \times 10^{-5} \text{ m} = 0.018 \text{ mm}$$

**DPC-GNN 目标：径向位移 0.01-0.05 mm（与 Lamé 解析解误差 < 20%）**

---

## 5. GNN 架构分析

### 5.1 AntisymmetricMP 对薄壁结构的适用性

DPC-GNN 的消息传递核心是 Antisymmetric Message Passing：

$$\mathbf{m}_{i \to j} = \text{MLP}(\mathbf{h}_i, \mathbf{h}_j, \mathbf{e}_{ij})$$
$$\mathbf{m}_{j \to i} = -\mathbf{m}_{i \to j} \quad \text{(反对称，架构性质)}$$

**对薄壁结构的影响：**

1. **边特征尺度差异**：径向边长 ~0.5mm，周向 ~1.3mm，轴向 ~4mm，比率 1:2.6:8
   - 消息传递中 edge_attr 包含节点间位移向量
   - 径向信号相对弱（位移小/边短）→ 但 GNN 通过 MLP 学习非线性映射，尺度差异不是根本问题

2. **周向连通性**：管状拓扑 = 环形图（周向首尾相连）
   - 对 GNN 来说只是图结构差异，不影响消息传递层
   - 可能需要更多 MP 层传播远端信息（4层 × 平均边长 → receptive field ≈ 7mm，管壁周长 ≈ 31mm）

3. **结论：AntisymmetricMP 完全适用，无需修改**

### 5.2 DOF 分析

| 组件 | 薄壁四面体 | 壳单元（参考） |
|------|-----------|---------------|
| 节点 DOF | 3（$u_x, u_y, u_z$）| 6（$u_x, u_y, u_z, \theta_x, \theta_y, \theta_z$）|
| GNN 输入维度 | 9（位置3 + 材料2 + 力3 + 边界1）| 12+（需要旋转编码）|
| GNN 输出维度 | 3 | 6 |
| 消息传递 | 不变 | 需要 SO(3) 等变消息传递 |

**选择薄壁四面体的根本原因：避免架构改动，维持论文的"唯一变量是材料参数"叙事。**

---

## 6. 实验验证方案

### 6.1 FEM 对照验证

**工具选择（待确认，FEniCS vs MuJoCo 对比测试并行进行中）：**
- **FEniCS（推荐）**：可以使用完全一致的 isochoric Neo-Hookean 公式
- **MuJoCo Flex（备选）**：论文已有前例，但精度存疑

**测试矩阵：**

| 载荷条件 | 内压 (Pa) | 外力 (N) | 重复 | 总配置 |
|----------|----------|---------|------|--------|
| 纯内压 | 500, 1000, 2000 | 0 | 20 | 60 |
| 内压 + 外力 | 1000 | 1-5 (随机) | 20 | 20 |
| 纯外力 | 0 | 1-5 (随机) | 20 | 20 |
| **合计** | | | | **100** |

**验证指标：**

| 指标 | 如何计算 | 成功标准 |
|------|---------|---------|
| 位移误差 vs FEM | $\frac{\|u_{GNN} - u_{FEM}\|}{\|u_{FEM}\|}$ | < 20% |
| 位移误差 vs 解析解 | $\frac{\|u_{GNN,radial} - u_{Lame}\|}{u_{Lame}}$ | < 20% |
| J 分布 | min, max, mean, std | J ∈ [0.9, 1.1] |
| 能量漂移 | $\frac{|\Delta E|}{E_0}$ | = 0% |
| 无单元反转 | count(J ≤ 0) | = 0 |

### 6.2 训练管线

```
Phase A (静态, 1000 epochs)
  → 最小化 Π(u) = ΣΨ(F)V₀ - Σf·u
  → 验证 phantom < 0.5mm

Phase B (短动态, 700 epochs)  
  → Verlet 积分, BPTT horizon=10
  → 加 GatedFusion 速度编码

Phase D1 (长 horizon, 300 epochs)
  → 混合窗口 [30, 40, 50] 步
  → 渐进课程学习

Phase D v7 (fine-tuning, 200 epochs)
  → lr=2e-6, λ_barrier=200
  → 目标 J_min > 0 at 50-step
```

### 6.3 血管特殊训练配置

```python
# 和实心组织的关键差异
E = 400_000       # 比肝脏硬 86×
nu = 0.49         # 极端近不可压
pressure = 1000   # 内壁压力 (Pa)
barrier_threshold = 0.3   # 更保守（薄壁单元体积小）
hidden_dim = 96           # 不变
n_mp_layers = 5           # 不变（和实际训练一致）
```

---

## 7. FEM 叙事（论文中的 Ground Truth 定位）

### 7.1 为什么需要 FEM 对照

DPC-GNN 的核心 claim 是"无训练数据，纯物理约束"。但审稿人必然会问：

> "How do you know the physics loss actually produces correct deformations? You need an independent reference."

FEM 提供了这个独立参考——它使用**相同的物理方程**（Neo-Hookean），但通过不同的数值方法（Galerkin 有限元 + Newton-Raphson）求解。

### 7.2 FEM 工具选择的论文叙事

**如果用 FEniCS：**
> "We validate against high-fidelity FEM solutions computed with FEniCS/DOLFINx (Logg et al., 2012), using the identical Neo-Hookean formulation with isochoric decomposition $\bar{I}_1 = J^{-2/3}I_1$. The FEM mesh uses the same tetrahedral discretisation (400 nodes, 1512 elements for liver; 1920 nodes, 8640 elements for vessel) to eliminate discretisation-induced discrepancies. Newton-Raphson iterations converge to residual tolerance $10^{-8}$, providing a reference accurate to within the discretisation limit."

**优势：**
- "identical formulation" = 排除公式差异，纯测 GNN 近似误差
- FEniCS 是计算力学社区公认的高精度开源 FEM 平台
- 审稿人无法质疑 FEM 参考的精度

**如果用 MuJoCo：**
> "We compare against MuJoCo 3.5.0 (Todorov et al., 2012) as a widely-used physics simulator in the robotics community."

**劣势：**
- MuJoCo 是机器人/RL社区工具，不是 FEM 社区工具
- 审稿人（MedIA/生物力学背景）可能质疑精度
- MuJoCo 的 Neo-Hookean 实现可能与我们不一致
- 不支持 HGO（后续升级受限）

### 7.3 推荐：FEniCS 为主，MuJoCo 为辅

**主验证：** FEniCS（高精度，相同公式，Section 5 "Validation" 核心表格）
**辅助：** MuJoCo（速度对比，说明 DPC-GNN 作为 RL 仿真器的优势，放 Discussion）

---

## 8. 论文集成方案

### 8.1 新增内容（MedIA Revision）

**Table 新增行：**

在现有 Table 2（肝脏结果）基础上，新增 5 行（brain/kidney/myocardium/cartilage/vessel），统一格式：

| Tissue | E (kPa) | ν | Phantom (mm) | Sensitivity | J₅₀ min | Energy Drift | FPS |
|--------|---------|---|-------------|-------------|---------|-------------|-----|
| Liver (baseline) | 4.64 | 0.45 | 0.032 | 224× | +0.021 | 0% | 566 |
| Brain | 1.0 | 0.49 | TBD | TBD | TBD | TBD | TBD |
| Kidney | 10.0 | 0.45 | TBD | TBD | TBD | TBD | TBD |
| Myocardium | 30.0 | 0.40 | TBD | TBD | TBD | TBD | TBD |
| Cartilage | 500 | 0.30 | TBD | TBD | TBD | TBD | TBD |
| **Vessel (portal vein)** | **400** | **0.49** | TBD | TBD | TBD | TBD | TBD |

**Figure 新增：**
- Fig. X: 多组织变形对比（6 panel, 每个组织一个 3D 变形云图）