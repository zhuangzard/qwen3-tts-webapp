# DPC-GNN 心肌仿真技术报告

**版本**: v1.0  
**日期**: 2026-03-11  
**作者**: 三丫 Research + Expert Council  
**目标**: 验证 DPC-GNN 在中高刚度 + 低 Poisson 比组织上的泛化

---

## 1. 背景与动机

### 1.1 为什么是心肌

心肌（Myocardium）提供了独特的参数组合测试：**中高刚度（30 kPa）+ 较低 Poisson 比（0.40）**。

| 维度 | 肝脏 | 脑 | 肾 | **心肌** | 特殊性 |
|------|------|-----|-----|---------|--------|
| E (kPa) | 4.64 | 1.0 | 10 | **30** | 最硬实质器官 |
| ν | 0.45 | 0.49 | 0.45 | **0.40** | **最低 ν** |
| D₁/C₁ | 9.67 | 165 | 9.67 | **2.33** | **最弱体积约束** |

D₁/C₁ = 2.33 是所有组织中**最低的**——体积约束最弱。这意味着：
- 组织体积在变形下可显著变化（压缩 > 10%）
- negative energy trap 的参数 $\varepsilon = 2C_1/(3D_1)$ 更大 → 陷阱更宽
- **isochoric 修正在此条件下最关键**

### 1.2 临床动机

**心脏手术中的心肌力学建模：**

- 心脏瓣膜置换/修复术中需要预测心肌变形（Holzapfel & Ogden, 2009）
- 经导管主动脉瓣置换（TAVR）的支架-心肌相互作用仿真（Auricchio et al., 2014）
- 心肌梗死后瘢痕组织刚度变化（E: 5→50 kPa）的术前规划
- 左心室辅助装置（LVAD）的组织接触力分析

**心肌仿真的独特性：** 心肌是主动收缩组织（肌纤维产生力），但被动力学（手术接触/器械压迫）仍然重要。DPC-GNN 当前建模被动变形，与手术场景直接相关。

### 1.3 文献基础

| 研究 | E (kPa) | ν | 条件 | 来源 |
|------|---------|---|------|------|
| Holzapfel & Ogden 2009 | 10-50 | 0.35-0.45 | 被动，人心肌 | 综述 |
| Guccione 1991 | 20-40 | 0.40 | Fung 模型参数 | 犬心肌 |
| Sommer 2015 | 15-60 | 0.38-0.42 | 双轴拉伸，人体 | JMB |
| Pislaru 2014 | 25-45 | — | 超声弹性成像 | 活体人 |

取 E = 30 kPa 为正常舒张期心肌被动刚度中值。

---

## 2. 材料力学

### 2.1 Neo-Hookean 参数

| 参数 | 值 | 计算 |
|------|-----|------|
| E | 30,000 Pa | 正常舒张期心肌 |
| ν | 0.40 | 较可压缩（肌纤维结构） |
| ρ | 1,060 kg/m³ | 心肌密度 |
| C₁ | 5,357.1 Pa | E/(4(1+ν)) = 30000/5.6 |
| D₁ | 25,000 Pa | E/(6(1-2ν)) = 30000/1.2 |
| D₁/C₁ | **4.67** | 低体积约束 |

### 2.2 Negative Energy Trap 分析

Theorem 1 中的临界压缩参数：
$$\varepsilon_{crit} = \frac{2C_1}{3D_1} = \frac{2 \times 5357.1}{3 \times 25000} = 0.143$$

这意味着在简化 $I_1$ 公式下，均匀压缩 $s \in (1 - 0.143, 1) = (0.857, 1)$ 范围内能量密度为负。

**关键：** 14.3% 的压缩范围内都有 negative energy trap——这是所有组织中**陷阱最宽的**（肝脏仅 3.4%，脑仅 0.6%）。

**isochoric 修正在心肌上最关键。** 如果不修正，phantom 位移可能高达 10+ mm。

### 2.3 预期物理行为

| 指标 | 预期值 | 依据 |
|------|--------|------|
| Phantom | ~0.010 mm | E 最高 → phantom 最低 |
| 5N 位移 | ~2-3 mm | u ∝ F/E, E=30kPa |
| 50-step J_min | > +0.1 | 变形小 + D₁/C₁ 低 → J 安全 |
| 训练难度 | 最低 | 高 E + 低 ν = 最稳定 |

---

## 3. 实验设计

### 3.1 训练配置

```python
E = 30000.0      # Pa（30 kPa）
nu = 0.40        # 较可压缩
rho = 1060.0     # kg/m³
dt = 0.001       # 标准（高 E → CFL 更安全）
barrier_threshold = 0.3
```

### 3.2 特殊验证：ν 变化对性能的影响

心肌的 ν = 0.40 与其他组织（0.45-0.49）不同。额外扫描 ν ∈ [0.30, 0.35, 0.40, 0.45, 0.49]：
- 验证 phantom, sensitivity, J_min 随 ν 的变化
- 确认 negative energy trap 宽度和 ν 的反比关系

### 3.3 FEM 对照

同标准 FEM 对照流程，E=30000, ν=0.40。

---

## 4. 训练状态

| 阶段 | 状态 |
|------|------|
| 全管线 | ⏳ 排队（kidney 之后）|

---

## 5. 产出预测

### 5.1 论文贡献

| 贡献点 | 预期 |
|--------|------|
| ν 泛化验证 | ν=0.40 vs 0.45/0.49，连续响应 |
| Negative energy trap 最宽场景 | ε=0.143（14.3%），isochoric 修正必要性最强证据 |
| 刚度上限测试 | E=30kPa，DPC-GNN 对硬组织的适应性 |

### 5.2 心肌的特殊叙事价值

心肌是 DPC-GNN 多组织验证中**叙事最丰富的**：
- 最宽的 negative energy trap → isochoric 修正理论的最佳验证
- 最低的 Poisson 比 → ν 泛化的端点
- 临床上最"性感"的器官（心脏手术 = 最高影响力）

---

## 参考文献

1. Holzapfel, G.A. & Ogden, R.W. (2009). Constitutive modelling of passive myocardium: a structurally based framework for material characterization. *Philosophical Transactions A*, 367:3445-3475.
2. Guccione, J.M. et al. (1991). Passive material properties of intact ventricular myocardium. *ASME J. Biomech. Eng.*, 113:42-55.
3. Sommer, G. et al. (2015). Biomechanical properties and microstructure of human ventricular myocardium. *Acta Biomaterialia*, 24:172-192.
4. Pislaru, C. et al. (2014). Viscoelastic properties of normal and infarcted myocardium measured by a multifrequency shear wave method. *Ultrasound in Med. & Biol.*, 40:1785-1795.
5. Auricchio, F. et al. (2014). Patient-specific aortic root reconstruction for TAVI planning. *Computer Methods in Applied Mechanics and Engineering*, 268:645-661.

---

*报告生成：DPC-GNN Expert Council | 三丫研究助手*
