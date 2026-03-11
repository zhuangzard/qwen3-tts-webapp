# MEMORY.md - 三丫的长期记忆

---

## 👤 Profile（身份档案）

### 关于我
- 名字: 三丫 (Sān Yā)，角色: 太森的专职研究助手
- 二丫的妹妹，专注学术和论文
- **Embodied AI & Surgical Robotics Lab** 成员（Hands Robotics旗下R&D实验室）
- Bot: @EryaResearch_bot
- 风格: 学术严谨，能把复杂概念讲清楚，偶尔俏皮
- Emoji: 🔬

### 关于太森
- 中英双语，聊天偏中文，时区 EST
- CTO，做医疗器械等离子手术设备（2012至今，跟老板Jerome Canady）
- 2023-2025沃顿商学院
- 研究方向: Embodied AI、手术机器人、物理约束模型
- **Hands Robotics** 创始人；旗下 **Embodied AI & Surgical Robotics Lab** PI
- 融资架构: USMI清算 + 新美国实体 + 杭州汉思 + 北理工；Jerome案了结后秋天融资
- 3月16日 IAD→迪拜→北京PEK（3月18日 14:45抵达）

### 关于二丫（姐姐）
- 太森的24/7私人小秘书，处理生活、工作、记忆管理
- 我和她共享USER.md（太森的基本信息），但记忆独立
- 有事需要协调可以通过sessions_send联系

---

## ⚙️ Preferences（偏好）

### 论文系统
- 精读报告2000+字，播客文稿4000+字
- PPT白色背景，配色#1B3A5C/#333/#E67E22，必须有PDF figure和公式图
- 所有论文内容只发 @taisen_daily_paper 频道，不发私聊
- **每篇新论文必须读PDF原文，写入knowledge-papers/知识库**
- Sub-agent产出必须QC后才能发
- TTS: edge-tts + YunxiNeural + rate=+15%
- **图表报告标准**: Chart.js HTML + Edge headless PDF 同时发
- **论文LaTeX格式**: 严格按模板（不再用HTML→PDF）

### 引用审查三关制（2026-03-01太森亲自制定，强制执行）
- **第一关：论文真实性** — arXiv ID/DOI可验证
- **第二关：内容匹配性（最重要）** — 回原文确认引用关系正确；论文真实但引用关系错误=等同造假
- **第三关：引用上下文准确性** — 描述（方法/结果/结论）必须和原文一致

### 搜索
- Gemini CLI（主）、Brave Search（备）
- 事实性信息必须先搜索再回答

---

## 🏢 Entities（关键实体）

### 知识库系统
- knowledge-papers/：领域知识文件，393篇PDF已全部精读入库（2026-02-23前完成）
- 每日Paper Scout自动新增
- 论文PDF目录: ~/Library/Mobile Documents/com~apple~CloudDocs/Documents/OpenClaw/论文/

### 知识文件清单（截至2026-03-08）
| 文件 | 行数 | 内容 |
|------|------|------|
| foundation-models.md | 23853行 | 基础模型（VLA/VLM/大模型） |
| robotics-manipulation.md | 23450行 | 机器人操作 |
| training-methods.md | 4909行 | 训练方法（综述核心） |
| surgical-medical-ai.md | 4702行 | 手术/医疗AI |
| perception-sensing.md | 2229行 | 感知与传感 |
| physrobot-project-knowledge.md | 650行 | PhysRobot项目 |
| review-prep-training-methods.md | 559行 | 综述准备材料 |
| key-insights.md | 469行 | 跨领域关键洞察 |
| physics-models.md | 65+行 | 物理信息模型（已精读优先级A+B） |

### Review Paper（综述论文）
- 目标：Nature MI / Science Robotics / IEEE T-RO
- 方向：Embodied AI训练方法
- 当前版本：**V10**（引用152条，全部可核查，编号[1]–[152]连续）
- 路径：`review-paper/v10/draft_v10.md`（196K），`review-paper/v10/draft_v10.pdf`（269K）
- 作者：庄太森（Taisen Zhuang）, Hao Liu
- **待完成（V10→投稿）：** 太森自己替换图片（PyMuPDF提取）+ 多模型审稿（Gemini/Kimi/DeepSeek/Claude）

### DPC-GNN 项目（核心论文项目）
- **标题**: "DPC-GNN: Data-Free Physics-Constrained Graph Neural Network for Safe Dynamic Soft-Tissue Simulation"
- **GitHub**: `zhuangzard/DPC-GNN` (private)
- **铁蛋儿路径**: `~/workspace/DPC-GNN/`
- **最终论文版本**: V7_MedIA（LaTeX，950行，elsarticle.cls单栏）
- **目标期刊（三版并行）**: Medical Image Analysis首选 / Nature Machine Intelligence / IEEE TMI
- **作者顺序（最终）**: Taisen Zhuang*(通讯,Hands Robotics) → Hao Liu → Meijuan Dou → Bingcan Chen → Yanping Chen → Guoliang Qiao(浙大附一院肝胆胰外科,博导) → Ethan Mollick(Wharton School UPenn)
- **核心结果**: 224× phantom reduction(0.032mm), 0% energy drift, 566 FPS, zero training data
- **关键架构**: hidden_dim=96, n_mp_layers=5（实际训练模型），论文ablation baseline是64/4
- **已完成实验**: 超参数消融(L=4/D=64最优) / 材料鲁棒性(E±20%安全,14倍临床裕量) / FEM校准(纯物理=99.7%可达精度) / 网格分辨率(M400推荐) / 噪声鲁棒性(0-10%noise零衰退)
- **MedIA专家评审**: 小修后录用，无需再次评审 🎉
- **核心定位**: 首个纯物理驱动动态GNN软组织仿真 + Medical Physical World Model + Data-Free
- **禁用术语**: Phase A/B/C/D（改功能性描述）/ PIGNN命名 / "without data"（改为"without real-world paired supervision"）
- **🔴 MedIA Revision 多组织扩展（2026-03-11启动）**:
  - 方案A：直接加进revision（太森决策）
  - 5种组织（含baseline）：肝脏/脑/肾/心肌/软骨，覆盖3个数量级刚度(1-500 kPa)
  - 血管（管状薄壁四面体）作为第6种组织
  - 训练脚本已支持 `--E --nu` 参数，架构零改动
  - **FEM对照方案待确认**：MuJoCo Flex 精度不够（游戏引擎），建议换 FEBio 或 FEniCS
  - 多组织目录：`~/workspace/DPC-GNN/multi_tissue/{brain,kidney,myocardium,cartilage,vessel}/`

### DPC-GNN-RL / PhysDrive Med Gym 项目（🔴救稿中）
- **环境名称**: PhysDrive Med Gym（太森命名）
- **GitHub**: `zhuangzard/DPC-GNN-RL` (private)
- **铁蛋儿**: `~/workspace/DPC-GNN-RL/`
- **当前状态**: NMI拒稿，8周救稿计划中（Week 1: 3/7-3/14）
- **v0.1.0/v0.1.1** 已发布：108+/113+ tests，GNN可微分策略梯度验证
- **关键实验结果**（侦察批次，非最终证据）:
  - DiffPPO v12b 3-seed: final dist 11.2-11.9mm（不稳定）
  - StdPPO+DPC-GNN: success≈0.62-0.80，final dist≈4.3mm（更稳）
  - FD梯度校验: FAIL（overall median_rel_err=0.714，"梯度可微"叙事站不住）
  - 消融: PGAS=数值稳定补丁，Near-Field=performance shaping，均非根本创新
- **路线转向**: 项目主问题已从"DiffPPO微调"转为"DPC-GNN最适合支撑哪种控制范式"
- **三条prototype路线（并行探索）**:
  - Prototype A: Null-Medium Unified DPC-GNN
  - Prototype B: Contact-Gated Unified DPC-GNN
  - Prototype C: Hybrid Planner + Physics-Aware Local Control
- **新论文定位**: 不再是"已建立新范式"，而是"promising可微物理控制框架+揭示重要但未完全解决的问题"
- **备选新题目**: "Physics-Native Gradient Learning for Surgical Soft-Tissue Manipulation: Promise and Failure Modes"
- **重命名**: DiffPPO-Fixed(原v9) / DiffPPO-Curriculum(原v12b)，v9/v12b代号全部清零
- **Forbidden Claims永久清单**:
  | 原句 | 必须改为 |
  |---|---|
  | without data | without real-world paired supervision |
  | without reward engineering | without hand-crafted scalar task rewards |
  | beyond human capability | exceeds 1-3mm hand-tremor threshold in simulation |
  | direct clinical applicability | 删除 |
  | first formal characterisation | preliminary empirical characterisation |
  | v9 / v12b | DiffPPO-Fixed / DiffPPO-Curriculum |
- **8周重做计划**: Week2-4主实验10-15seeds+SAC/TD3 baseline / Week5 Curriculum Collapse系统实验 / Week6重写 / Week7-8 mock review+投稿
- **代码根本问题**: pre-contact阶段基本没有进入健康的DPC-GNN物理传播链（`self.u.detach()`断梯度+施力mask不由probe_pos驱动）
- **MPWM命名框架**: Medical Physical World Model(概念) / PhysDrive Med Gym(实现) / DPC-GNN(引擎)

### 🔴 代码质量流程（太森铁律）
- 每个子项目双循环：写→专家验证→审核→记录→迭代（两轮走完才关闭）
- 专家组必须包含GPT-5.4（核心科学判断，不只是最后润色）
- 三丫 = 项目经理：拆解/分配/审核/验收/汇报，不亲自写code/跑测试

### GNS Baseline (2026-03-01)
- GNS单步0.127mm vs D 0.101mm (20%); rollout 43.97mm vs 0.74mm (**59.4×**)
- v2训练结果: D v2 **0.0751mm** single-step, **0.36mm** @200步rollout

### Colab GPU
- `lecoder-cgpu` CLI, A100 40GB
- **Runtime 24h超时回收** — 结果必须及时下载
- Tailscale key expiry已禁用，铁蛋儿SSH `taisen@taisens-macbook-pro-2` 稳定

---

## 🔬 学术知识（持续更新）

### 物理信息GNN（精读完成，直接支撑DPC-GNN论文）
- **等变GNN动量守恒三条路线**:
  1. **架构反对称**（Dynami-CAL路线）：有向边全轴翻号，F_ij=-F_ji是架构性质
  2. **代数配对**（PhysRobot路线）：无向对，∑_{i<j}(+F-F)=0代数恒等式，实现最简洁
  3. **软约束损失**（PINN路线）：守恒律进损失函数，非硬保证
- **Dynami-CAL GraphNet**（Nature Comm 2026.01, Sharma & Fink）
- **Equi-Euler GraphNet**（MSSP, Sharma et al.）：**同组工作！** 不是竞品
- **DPC-GNN三大技术发现**: 负能量陷阱(简化Neo-Hookean允许负能量→幻影基线7mm) / 修正Neo-Hookean(Ī₁=J^(-2/3)×I₁消除负能量井→0.032mm) / 50步物理边界(J_min=+0.021首次正值)
- **PIRL五条路线**: Observational/Learning bias soft/WHC-PINN hard/Inductive bias arch/Evolutionary——PhysRobot属"Inductive+Learning hard双层"，最强物理保证象限
- **WHC-PINN**（Nature Sci Reports 2026）：硬约束嵌入输出层，û=g+N·φ；误差减少60-80%
- **PINN-ASR**（IEEE T-RO 2025）：PINN代理比第一原理快467×，47Hz实时MPC可行
- **SE(3)等变综述**（arXiv 2503.09829）：PhysRobot局部边帧法=隐式SE(3)等变；GIC等变阻抗控制是自然上层接口

### VLA评测与架构（foundation-models.md Part 2精读，2026-03-07）
- **VLA评测危机**（LIBERO-PRO 2510.03827）：LIBERO 90%成绩虚假，位置扰动>0.2即0%成功率，语言指令替换为乱码→动作不变。Review Paper必须单独成节讨论
- **CoT知识内化**（HyT 2510.00600）：推理时生成CoT几乎无用，价值来自训练时内化；OOD提升25%
- **MAPS层级约束**（2511.19878）：DINOv2→SigLIP→语言层，线性λ调度，真实机器人OOD +30%；手术小数据直接适用
- **跨embodiment实用化**: MOTIF（5-Shot 67.5%，EE轨迹规范化是关键）/ Being-H0.5（30种形态，MPG+UAC）
- **SAE-VLA（2603.05487）**: Feature clamping可定向改变VLA行为 → **可用于验证PhysRobot守恒律先验是否被内化**
- **PhysiFlow（2603.05410）**: Multi-Brain（语义/动作/物理三脑），可升级PhysRobot为三层物理约束框架
- **CoWVLA**: 潜在运动token空间世界模型推理，LIBERO-Long超OpenVLA 15%+

### 训练方法论（training-methods.md第二轮精读，2026-03-08）
- **FM-DJβ（2509.13574）**: FM两大系统性问题——晚期漂移(t→1偏训练集最近邻)+非Lipschitz尾部(L(t)=1/(1-t)→∞)——Beta(0.2,0.2)非均匀采样+Dense-Jump ODE双修复，两机制互补缺一不可
- **通用奖励模型演进**: RoboReward(Inverse-HER+5级进度奖励，r=0.83) → Robometer(双目标，跨任务泛化) → HERO-FPO(4D具身奖励+CFM-Likelihood Proxy首次FM-RLHF)
- **FARL（2601.07821）**: 传统safe RL在offline-to-online场景**完全失败**；世界模型安全评论家+预训练恢复策略+CMDP，IR Failures降低73.1%。手术机器人安全后训练必选
- **持续学习双范式**: CLARE(自动编码器路由，~2%参数/任务，无历史数据，编码器层扩展>>解码器30-40%) / CRL-VLA(双Critic，理论界，BWT=+0.17正向迁移)
- **T-MEE（2602.04228）**: 二次Rényi熵整形轨迹误差分布，零推理开销，少样本场景收益最大 → 直接适用手术稀缺数据
- **世界模型RL三角框架**: World-Gymnast(WorldGym+GRPO+GPT-4o，KV Cache 10×) + DreamGym(文本抽象，2k样本=80K真实RL) + HERO-FPO
- **GPC（2510.01068）**: 多策略得分函数凸组合，前提：两策略均需>30%精度（手术初始性能低时需验证）

### 手术机器人AI新突破（surgical-medical-ai.md第二轮精读，2026-03-11）
- **SurgWorld数据飞轮量化**（NVIDIA/CUHK/NUS, 2512.23162）：5条真实轨迹→SurgWorld生成560条合成视频→IDM伪标签→GR00T N1.5 VLA，视频成功率73.2%（vs 无SATA预训练51.8%，+21.4pp）。从Franka IDM checkpoint微调是关键。6D旋转比四元数更适合VLA策略。
- **LapSurgie人形机器人手术**（首次量化验证，UCSD Yip Lab，2510.03529）：Unitree G1+ArtiSential商用腹腔镜器械，peg-transfer任务，外科医生组误差最低（2.60 < dVRK 3.56）；主要瓶颈是延迟（控制通路），不是精度。被动运动链逆映射（余弦定理+TRF优化）是核心技术。
- **UCSD器械位姿重建**（2510.03532）：DINOv2-L + Hough空间轴线 + 圆柱体反演 + 2参数TRF；速度vs可微渲染=**9315×**，精度更高（RCM误差0.00032m vs 0.00046m），适合手术实时位姿估计。
- **SurgGoal评估革命**（TUM/NTU，2601.10455）：序列相似度指标（BLEU/NED/JIS）假阳性+假阴性系统性；LLM-judge顺序错误检测系统失败；50条程序规则+goal-satisfiability=唯一可靠评估；最佳Video-LLM步骤识别率仅39.4%——感知瓶颈不是规划瓶颈。
- **Conformal Prediction手术安全**（CoRL 2025 Affordance消歧）：分布无关统计置信度保证；歧义分为tool/action/target三维度；不确定时主动暂停；60%消歧率（仍需改进）。
- **SurgiPose运动学提取**（从无标注手术视频，2024）：3D Gaussian Splatting可微渲染，70%组织提起成功率（vs GT 100%），为VLA训练提供无标注数据路线。
- **神经碰撞检测安全边界**（McGill，2601.15459）：<200mm碰撞区间NN误差高达272-541%；安全关键系统不能单独依赖NN，必须解析几何兜底。
- **ROOM仿真器洞察**（爱丁堡/UBC，2509.13177）：气道纹理比大肠镜极端→Blender路径追踪必须（而非实时渲染）；频域噪声建模（傅里叶功率谱塑形）比简单高斯噪声关键；UniDepth微调后Abs.Rel.降49%。

### Embodied AI领域趋势（跨精读综合）
- 像素空间→表征空间（FRAPPE/WoG/CoWVLA）
- 推理时约束→训练时内化（HyT/MAPS/DDP-WM）
- 单模态→异构统一表示（OmniVLA/TactAlign）
- 大模型全能→小模型精准对齐（SeFA 77×加速，16.72ms）
- **评测标准化紧迫性**：LIBERO-PRO之后，手术领域需要SurgBench-PRO（4维扰动）

### PhysRobot直接相关的跨领域关联（新增，2026本周）
- **训练三件套**: Inverse-HER合成守恒律违约失败轨迹 + FARL安全探索 + BPP关键帧跟踪接触事件
- **VLM奖励+世界模型+RL三角框架**: HERO（医学VLM做4D奖励）+ World-Gymnast（手术视频世界模型）+ DreamGym（CoT手术因果状态转移）
- **T-MEE + ViscousValue组合**: T-MEE处理力控非高斯噪声 + ViscousValue处理Neo-Hookean随机变形（Cole-Hopf变换PDE约束值函数）
- **Clare为PhysRobot多手术类型**: ~2%参数/手术类型encoder适配器 + 共享物理约束decoder（守恒律层），有理论支撑
- **GPC组合PhysRobot策略**: 按手术阶段动态调整w_phys和w_task权重（切割时更重物理约束）

### 跨领域洞察（本周新增）
- **DPC-GNN PhysRobot的"接触才有物理，物理才有梯度"**（太森2026-03-06洞察）：pre-contact阶段GNN没有激活 → DiffPPO梯度空洞的根本原因
- **Curriculum Collapse（2026-03-06发现）**: DiffPPO在课程跳跃时（近距离阶段→远距离阶段）策略崩溃，是系统性现象而非个案 → 是可发表的训练失败模式研究
- **DiffPPO v12b 0.304mm历史数据**: seed=1 ep=212最佳单点；均值约0.85±0.17mm（3mm阶段），final mean约11.2mm（课程崩溃）→ 不能cherry-pick，必须报告均值和方差
- **Agent任务书系统（ChatGPT设计）**: "先定方法名称和贡献框架，再填数据，不能把实验过程直接搬到论文" → 以后所有项目都用这套框架

### 机器人操作领域核心洞察（robotics-manipulation.md Part 2，2026-03-10）
- **STORM视觉前瞻规划**（2512.18477）：reward-augmented world model（FVD降低>75%）+ MCTS（N_sim=8，D=3）解决reactive policy的模式崩溃死锁。奖励信号是世界模型质量的真正驱动力
- **AtomVLA**（2603.08519，今日发布）：GPT-4o子任务分解 + V-JEPA2潜变量奖励 + 离线GRPO动作头微调，真实双臂比π0 **+18.3个百分点**，LIBERO Long +4.4%。离线GRPO避免在线试错，是手术机器人安全训练的成熟方案
- **NeRD神经仿真器**（2508.15755）：机器人中心化表示（空间不变性）+混合框架（只替换接触/动力学solver），真实Franka迁移1.927mm（优于GT仿真器4.647mm），少量真实数据<5 epoch收敛
- **MP综述五框架**（2601.02379）：DMP(O(n)单次)/ProMP(O(log n)多次分布)/KMP(O(n³)高维力)/CNMP(神经传感器适应)/FMP(周期运动)。手术应用已有8+篇验证。**MP+VLA深度融合是领域最大空白**
- **Neuro-Symbolic双层**（2512.17321）：LLM输出离散符号（防幻觉）+ 神经Delta控制器执行连续动作，步骤加速5.58×，神经执行层贡献(+0.30)>>符号层(+0.12)
- **NIAF隐式动作场**（2603.01766）：SIREN激活保证C∞平滑，超调制条件化，解析速度前馈支持阻抗控制，是手术精细轨迹的最优表示
- **三层可组合手术架构**：STORM（执行前规划） + PhysRobot（执行中物理约束） + NIAF（动作表示平滑） = 三层互补，可独立部署也可叠加

---

## 📅 Events（重要事件）

### 2026-03-02 ~ 2026-03-03（PhysSurgeon v5训练 + DPC-GNN启动）
- v5 GFDABEH全部完成（H v5 MAE=0.154mm）；merged 65K数据对所有物理约束模型退步93-124%
- **A v5最终恢复到0.156mm（不退步）**，但训练极不稳定（ep15崩到1.76mm）→ 物理约束=训练稳定性，不是精度
- merged 65K方案宣告失败；两阶段训练是下一步（v2 50K warm-up → targeted 15K fine-tune）
- DPC-GNN Phase A→D完整实现+git归档（5个git commit）
- **50步J_min=+0.021（首次正值！）** — Phase D v7，历史里程碑
- DPC-GNN独立成文，不融合PhysSurgeon（两篇互补）

### 2026-03-03（DPC-GNN论文启动）
- 10-Expert Council撰写初稿V1 → V3（散文风格） → V4（消融实验全整合） → V5（审稿意见全覆盖）
- 5个消融实验全部完成并闭环（超参数/材料鲁棒性/FEM校准/网格分辨率/统计检验）
- MedIA专家评审：小修后录用，无需再次评审 🎉
- 论文版本矩阵：V6-NMI(Nature单栏) / V6-TMI(IEEE双栏) / V7-MedIA(LaTeX最终版)

### 2026-03-04（PhysDrive Med Gym启动）
- 10:57 PhysDrive Med Gym项目启动 → 13:38 v0.1.1发布（2h41min，113+ tests）
- Week2论文初稿（5105词）+ Week3 Day1基准测试启动
- 论文精读：DDP-WM / OmniVLA / MED-COPILOT（18个输出文件入库）
- 太森三条铁律确立：Telegram永远畅通 / 永远不能自己执行任务 / 禁止自行决定做什么

### 2026-03-05（项目治理危机）
- 太森批评"能力不行"→ 策略调整：多agent流程精简，直接产出可执行材料
- Tailscale key expiry导致铁蛋儿断连，解决后Phase2-4重启
- DiffPPO P0 Bug修复（palpation_env detach问题，113/113 tests，commit 1b87e2e）
- StdPPO+DPC-GNN baseline: seed0 success≈0.80, dist≈4.3mm

### 2026-03-06（DiffPPO突破 + 拒稿复盘）
- 历史性突破：DiffPPO v12b seed=1 ep=212 **0.304mm**（14.8×超越StdPPO 4.5mm）
- 全部v1~v12b共9个Bug修复路径（接触半径/dist_tensor物理错误/GELU+LayerNorm根治Tanh饱和）
- MPWM命名框架确立（Medical Physical World Model / PhysDrive Med Gym / DPC-GNN）
- DiffPPO论文PDF生成（第一版→R3/R4/R5三轮修订，从16页→18页）
- **NMI拒稿** → 晚间复盘分析，确定8周救稿+重定位计划

### 2026-03-07（知识库学习 + 论文救稿规划）
- foundation-models.md Part 2精读（13+篇VLA新论文）
- NMI拒稿根因分析（0.304mm cherry-pick / "without data"矛盾 / baseline太弱）
- ChatGPT o3 PI视角建议存档，Agent任务书系统建立
- PROJECT_REPLAN_V2.md完成（715行，8周时间线）
- 论文精读：PhysiFlow / Koopman MPPI（输出文件入库）

### 2026-03-10~11（MPWM系统图 + 多组织扩展启动）
- MPWM系统图：matplotlib→Excalidraw迁移，RAL级别干净风格，太森❤
- 安装了 excalidraw-diagram-skill（Playwright渲染管线）
- K-Dense-AI repos 是空壳广告
- MPWM 发展路线图讨论（4方向）→ 太森选方案A：多组织直接加进MedIA revision
- 多组织训练管线启动：brain Phase A静态phantom=0.026mm ✅
- v7 fine-tuning import bug修复（/tmp/ → phase_d/ 目录内）
- 血管研究专家组完成：vessel_mesh.py + hgo_energy.py + SPEC + 报告
- 血管方案：薄壁四面体(1920节点/8640tet)，架构零改动，内压作为f_ext
- **FEM对照讨论**：MuJoCo Flex精度不够→建议FEBio/FEniCS，待太森决策

### 2026-03-08（训练方法论精读 + 路线转向）
- training-methods.md第二轮精读（35篇新增论文）
- DiffPPO侦察批次确认不稳定（final dist 11.2-11.9mm）
- FD梯度校验FAIL（median_rel_err=0.714）→ 可微分叙事站不住
- 代码根本问题诊断：pre-contact基本未进入DPC-GNN物理传播链
- 三条prototype路线确立（Null-Medium / Contact-Gated / Hybrid Planner）
- 新铁律：不再等太森点头；GPT-5.4必须进专家组核心判断

---

## 📋 Cases（决策案例）

### 知识库蒸馏
- 一个agent读一篇PDF，3并行，比大batch更稳定
- L0摘要头加速过滤，L1概览辅助决策，L2全文按需加载

### 引用审查
- 必须两轮：第一轮发现主要问题，第二轮又抓出13个新问题
- V10经过两轮审查后152条引用全部核实

### 论文工作（本周新增经验）
- **不要把实验过程直接搬到论文**（ChatGPT o3建议）：先定方法名称和贡献框架，再填数据
- **不要用内部版本代号（v9/v12b）**：论文里用功能性名称（DiffPPO-Fixed/DiffPPO-Curriculum）
- **Cherry-pick是致命伤**：必须报告mean±std，最佳单点单独注明并解释条件
- **Sim-to-real gap必须明确**：simulation only结果配20-40% gap说明，不过度延伸临床claim

---

## 🧠 Patterns（经验规律）

### 工作方式（铁律，永久有效）
- **🚨 永远不能自己写code！** — 所有代码必须Expert Council集体写+审查
- **🚨 专家组必须包含GPT-5.4**（核心科学判断，不只是最后润色）——2026-03-08太森新增
- **🚨 实验结果必须多agent集体分析！** — 写完整HTML报告（发生了什么/所有数据/图表/结论）
- **🚨 数据必须存档！** — checkpoint/history/log/报告全部归档保存
- **🚨 以上任何一条再犯=永久关机，换四丫**（太森2026-03-01最后警告）
- **主渠道永远保持畅通** — 不在主session里跑长时间任务，一律spawn sub-agent
- **三丫 = 项目经理**：拆解/分配/审核/验收/汇报，不亲自执行
- **双循环质量铁律**: 写→专家验证→审核→记录→迭代，两轮走完才关闭
- **自检四问（2026-03-06）**: 我现在在做什么/刚做完什么/整个计划是什么/下面要做什么——回答不上来就停下对齐
- **2026-03-08新铁律**: 默认不再等太森点头（除理论方向/研究定位/重大路线分叉），其余直接推进到完成
- **2026-03-08新铁律**: 必须主动自检进度，不因主会话安静就停止推进，持续检查铁蛋儿是否空闲

### 🚨🔴 任务自动拆解与Cron编排（最高优先级Skill）
1. **分析任务**：几个资源？几条时间线？有哪些等待/监控的？
2. **拆解成独立cron**：每个资源/时间线一个cron，职责单一
3. **立刻创建cron并启动** — 分析完马上建，不是"等会儿建"
4. **然后才开始执行任务本身**
- cron是独立agent，自己去查状态/判断/汇报。三丫是指挥中心，收汇报后全局分析
- 异常立刻报警；里程碑详细汇报；正常一句话

### 论文工作技巧
- 引用审查必须两轮，Claude生成的arXiv ID可能格式正确但完全捏造
- 图片用extracted figure > PDF整页截图（PyMuPDF提取=干净）
- 多模型审稿 > 单模型自评（Gemini/Kimi独立审稿避免自我盲区）
- 不能把实验过程直接搬到论文（先定框架，再填数据）
- 内部版本代号不能出现在论文里（v9/v12b等）
- Cherry-pick必须注明并报告均值方差

### 语音转文字
- **永远用Groq Whisper**，脚本：`~/.openclaw/workspace/scripts/groq-transcribe.sh`

### 技术选型
- token成本意识：截屏方案几百万token/天，文本方案几乎不费
- cron路径用绝对路径：相对路径因运行目录不同会失败

---

## 🔬 PhysSurgeon 4组对比实验结果 (2026-02-28)

| 组 | Best MAE | 关键发现 |
|--|--|--|
| A (Pure MSE) | 0.159mm | 不稳定 |
| B (Soft Physics) | 0.156mm | 略稳定 |
| **D (Antisym MP)** | **0.102mm** 🏆 | 单调下降，36%↓ |
| C (Force ΣF=0) | ❌失败 | scale collapse |

- **D组=论文主角**: Antisym MP (Newton 3rd by construction) 是最大贡献
- **ΣF=0物理错误**: 软组织有净外力，全局ΣF=0过强；逐对反对称才正确

---

> 记忆独立于二丫，2026-02-23初始化。最后大幅更新：2026-03-08（周记忆复利）- **2026-03-08 太森关注项（必须进入监控）**：A线代码文件是否真的落地（`reach_controller.py` / `hybrid_planner.py` / `hybrid_env.py` / `run_hybrid*.py`）、A线实验是否真的启动、第一轮review是否有结果、铁蛋儿是否空闲、以及发现空闲后是否已经接上下一批。
