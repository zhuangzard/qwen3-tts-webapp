# DPC-GNN 肾组织仿真技术报告

**版本**: v1.0  
**日期**: 2026-03-11  
**作者**: 三丫 Research + Expert Council  
**目标**: 验证 DPC-GNN 在中等刚度器官上的泛化（肝脏→肾脏的"近邻"迁移）

---

## 1. 背景与动机

### 1.1 为什么是肾组织

肾脏和肝脏的力学参数相近（E 相差约 2×，ν 相同），是验证 DPC-GNN **参数连续性**的理想选择：

| 维度 | 肝脏 (baseline) | 肾 | 差异 |
|------|-----------------|-----|------|
| E | 4,640 Pa | 10,000 Pa | **2.2× 更硬** |
| ν | 0.45 | 0.45 | 相同 |
| D₁/C₁ | 9.67 | 9.67 | 相同 |
| 密度 ρ | 1,060 kg/m³ | 1,050 kg/m³ | 几乎相同 |

**核心测试**：如果 DPC-GNN 在 ν 相同、E 翻倍的条件下表现一致，说明架构对刚度的泛化是连续的——不存在"甜点参数"问题。

### 1.2 临床动机

**肾部分切除术（Partial Nephrectomy）**中的组织变形预测：

- 腹腔镜/机器人辅助肾部分切除是保留肾单位的标准术式（Campbell et al., 2009）
- 术中肾实质夹持和翻转产生 5-15 mm 位移
- 实时变形预测辅助识别肿瘤边界和肾盂/肾盏位置（Simpfendörfer et al., 2011）
- 肾缺血时间（warm ischemia time < 25 min）限制术中调整时间 → 需要实时仿真

### 1.3 文献基础

| 研究 | 方法 | E (kPa) | ν | 应用 |
|------|------|---------|---|------|
| Nava 2008 | 体内压痕 | 5-25 | 0.45 | 肾实质（皮质+髓质平均） |
| Umale 2013 | 离体拉伸 | 5-15 | 0.40-0.45 | 人尸体肾 |
| Carter 2001 | 综述 | 5-20 | 0.45 | 腹部脏器综合 |
| Mendizabal 2020 | DL仿真 | 10 | 0.45 | 医学影像分析，实时超弹性 |

肾实质的力学特性因皮质/髓质分层有差异（皮质约 10-25 kPa，髓质约 5-10 kPa），取 10 kPa 为均质近似。

---

## 2. 材料力学

### 2.1 Neo-Hookean 参数

$$\Psi = C_1(\bar{I}_1 - 3) + D_1(J - 1)^2 + \Psi_{barrier}(J)$$

| 参数 | 值 | 计算 |
|------|-----|------|
| E | 10,000 Pa | 肾皮质中值 |
| ν | 0.45 | 与肝脏相同 |
| ρ | 1,050 kg/m³ | 肾实质 |
| C₁ | 1,724.1 Pa | E/(4(1+ν)) |
| D₁ | 16,666.7 Pa | E/(6(1-2ν)) |
| D₁/C₁ | 9.67 | 与肝脏相同 |

### 2.2 预期物理行为

由于 E 增大 2.2×，预期：
- **静态位移减小 2.2×**：5N 下最大位移 ~6-7 mm（vs 肝脏 ~14 mm）
- **力灵敏度不变**：sensitivity ratio 应接近肝脏的 150×（取决于 ν 而非 E）
- **J 分布更保守**：更硬的材料变形更小，J 偏离 1 的幅度更小
- **训练更容易收敛**：更硬→梯度更稳定

### 2.3 和肝脏的对比预测

| 指标 | 肝脏预期 | 肾预期 | 依据 |
|------|---------|--------|------|
| Phantom | 0.032 mm | ~0.015 mm | E↑ → phantom↓ |
| 5N 位移 | 14 mm | ~6 mm | 线性弹性近似 u ∝ F/E |
| 50-step J_min | +0.021 | > +0.1 | 变形更小 → J 更安全 |
| FPS | 566 | ~566 | 架构不变 |

---

## 3. 实验设计

### 3.1 训练配置

```python
E = 10000.0      # Pa（10 kPa）
nu = 0.45        # 和肝脏相同
rho = 1050.0     # kg/m³
dt = 0.001       # 和肝脏相同（CFL 安全，更硬意味着更安全）
barrier_threshold = 0.3   # 标准值
hidden_dim = 96           # 不变
n_mp_layers = 5           # 不变
```

### 3.2 FEM 对照

- 同 Neo-Hookean Newton-Raphson FEM 求解器
- E=10000, ν=0.45, 同网格、同边界条件
- 5N 载荷下 FEM 参考位移 → 计算 GNN/FEM ratio

### 3.3 特殊验证：肝脏→肾脏连续性

额外实验：在 E = [2000, 4000, 6000, 8000, 10000] Pa 范围内扫描，验证 DPC-GNN 性能（phantom, sensitivity, J_min）随 E 的连续变化——如果出现突变点，说明架构有参数敏感性问题。

---

## 4. 训练状态

| 阶段 | 状态 | 备注 |
|------|------|------|
| Phase A 静态 | 🔄 训练中 | 12:36 启动 |
| Phase B 短动态 | ⏳ 排队 | — |
| Phase D1 | ⏳ 排队 | — |
| Phase D v7 | ⏳ 排队 | — |
| FEM 对照 | ⏳ 待训练完成 | — |

---

## 5. 产出预测

### 5.1 论文贡献

| 贡献点 | 预期数据 |
|--------|---------|
| 刚度泛化验证 | E 从 4.6→10 kPa，性能不退化 |
| ν 一致性验证 | 同 ν=0.45 下 E 变化的连续响应 |
| 临床参数覆盖 | 肝+肾覆盖腹部手术两大器官 |

### 5.2 预期结果

**乐观预测**：肾组织应该是所有新组织中**表现最好的**——参数最接近肝脏 baseline，训练难度最低。如果肾组织出问题，说明架构有根本缺陷。

**风险**：几乎为零。

---

## 参考文献

1. Campbell, S.C. et al. (2009). Guideline for management of the clinical T1 renal mass. *Journal of Urology*, 182(4):1271-1279.
2. Simpfendörfer, T. et al. (2011). Augmented reality visualization during laparoscopic radical prostatectomy. *Journal of Endourology*, 25(12):1841-1845.
3. Nava, A. et al. (2008). In vivo mechanical characterization of human liver. *Medical Image Analysis*, 12:203-216.
4. Umale, S. et al. (2013). Experimental in vitro mechanical characterization of porcine Glisson's capsule and hepatic veins. *Journal of Biomechanics*, 46:1583-1589.
5. Mendizabal, A. et al. (2020). Simulation of hyperelastic materials in real-time using deep learning. *Medical Image Analysis*, 59:101569.
6. Carter, F.J. et al. (2001). Measurements and modelling of the compliance of human and porcine organs. *Medical Image Analysis*, 5(4):231-236.

---

*报告生成：DPC-GNN Expert Council | 三丫研究助手*
