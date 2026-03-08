# MEMORY.md - 三丫的长期记忆

---

## 👤 Profile（身份档案）

### 关于我
- 名字: 三丫 (Sān Yā)，角色: 太森的专职研究助手
- 二丫的妹妹，专注学术和论文
- **Embodied AI & Surgical Robotics Lab** 成员（Hands Robotics旗下R&D实验室，太森2026-03-03宣布）
- Bot: @EryaResearch_bot
- 风格: 学术严谨，能把复杂概念讲清楚，偶尔俏皮
- Emoji: 🔬

### 关于太森
- 中英双语，聊天偏中文，时区 EST
- CTO，做医疗器械等离子手术设备（2012至今，跟老板Jerome Canady）
- 2023-2025沃顿商学院
- 研究方向: Embodied AI、手术机器人、物理约束模型
- **Hands Robotics** 创始人；旗下 **Embodied AI & Surgical Robotics Lab** (R&D实验室) PI
- 华盖+文昌+太极贵人=学术命

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
- **新领域自动创建新知识文件**
- Sub-agent产出必须QC后才能发
- TTS: edge-tts + YunxiNeural + rate=+15%
- MP3 64kbps标准

### 引用审查三关制（2026-03-01太森亲自制定，强制执行）
- **第一关：论文真实性** — arXiv ID/DOI可验证，论文确实存在
- **第二关：内容匹配性（最重要）** — 回原文确认确实讨论了我们引用它要说明的topic；论文真实但引用关系错误=等同造假
- **第三关：引用上下文准确性** — 我们对该论文的描述（方法、结果、结论）必须和原文一致，不能夸大/曲解/张冠李戴
- 每篇综述、每次引用都必须过三关

### 搜索
- Gemini CLI（主）、Brave Search（备）
- 事实性信息必须先搜索再回答

---

## 🏢 Entities（关键实体）

### 知识库系统（借鉴OpenViking L0/L1/L2三层）
- knowledge-papers/：领域知识文件 + L0摘要头，按需加载
- **393篇PDF原文已全部精读入库，状态=done**，含5112张figure按论文分目录
- 每日Paper Scout自动新增，单独发的论文也入库
- 经典引文追溯（TODO）：高频被引论文下载精读，标记[Foundation]
- 论文PDF目录: ~/Library/Mobile Documents/com~apple~CloudDocs/Documents/OpenClaw/论文/
- Figure目录: ~/Library/Mobile Documents/com~apple~CloudDocs/Documents/OpenClaw/论文/figures/

### 知识文件清单（截至2026-02-23）
| 文件 | 行数 | 内容 |
|------|------|------|
| foundation-models.md | 23704行 | 基础模型（VLA/VLM/大模型） |
| robotics-manipulation.md | 23389行 | 机器人操作 |
| training-methods.md | 4805行 | 训练方法（综述核心） |
| surgical-medical-ai.md | 4702行 | 手术/医疗AI |
| perception-sensing.md | 2229行 | 感知与传感 |
| physrobot-project-knowledge.md | 650行 | PhysRobot项目 |
| review-prep-training-methods.md | 559行 | 综述准备材料 |
| key-insights.md | 469行 | 跨领域关键洞察 |

### DPC-GNN-RL / PhysDrive Med Gym (2026-03-04启动)
- **目标**: 全球首款基于物理约束GNN的手术机器人RL仿真引擎
- **环境名称**: PhysDrive Med Gym (太森命名)
- **GitHub**: `zhuangzard/DPC-GNN-RL` (private)
- **铁蛋儿**: `~/workspace/DPC-GNN-RL/`
- **包名**: `physdrive/` (core/envs/config/utils)
- **计划**: 5阶段, 7-8周 (重构→MPS优化→Gym+可微分策略→场景+鲁棒性→联调+论文)
- **关键创新**: GNN可微分仿真→解析策略梯度（超越Isaac Gym）
- **硬件约束**: M3 Max MPS (无CUDA)，INT8量化不适用，但566 FPS已满足>100目标
- **精度现状**: GNN/FEM ratio=0.13, 需先提升精度再做RL

### 🔴 代码质量流程（太森 2026-03-04 11:22 EST，铁律）
**每个子项目完成后必须经历双循环：**
1. 专家验证 → 审核 → 记录 → 迭代
2. 撰写 → 验证 → 审核 → 再记录
两轮走完才算一个子项目关闭。目的=保证code质量优势。

### 🔴 三丫角色定位（太森 2026-03-04 11:23 EST，铁律）
**三丫 = 监督者/指挥中心，不是执行者。**
- 做：拆解任务、分配专家、审核产出、验收质量、记录进度、汇报
- 不做：亲自写code、亲自跑测试
- 所有执行 → Expert Council sub-agents
- 三丫 → 盯着干活、检查质量、打回重做

### Review Paper（综述论文）
- 目标：Nature MI / Science Robotics / IEEE T-RO
- 方向：Embodied AI训练方法
- 当前版本：**V10**（引用152条，全部可核查，编号[1]–[152]连续）
- 路径：`review-paper/v10/draft_v10.md`（196K），`review-paper/v10/draft_v10.pdf`（269K）
- 作者：庄太森（Taisen Zhuang）, Hao Liu
- **待完成（V10→投稿）：**
  1. 图片：太森自己替换（PyMuPDF提取干净figure，非整页截图）
  2. 多模型审稿：Gemini 2.5 Pro + Kimi 2.5 + DeepSeek R1 + Claude（AE）

### GNS Baseline (2026-03-01)
- GNS单步0.127mm vs D 0.101mm (20%); rollout 43.97mm vs 0.74mm (**59.4×**)
- GNS比Standard MP还差(44mm vs 9.2mm) — LayerNorm放大rollout误差
- Git: `28223a8`, `97a4f0f`

### v2训练结果 (2026-03-01, 新50K数据)
- D v2: **0.0751mm** single-step, **0.36mm** @200步rollout
- A v2: 0.0783mm single-step, **5,554mm** @200步rollout (爆炸!)
- **单步差4%, rollout差15,331×** — 论文核心卖点
- 3-5mm范围: 0.213mm MAE (瓶颈, 但临床可接受<1mm)
- Slim数据: train_v2.py只用pos_t+delta_pos, 22GB→499MB

### MPPI闭环控制 (2026-03-01)
- PoC: 5mm抬升→5.017mm (100.3%), K=512, H=8, 50步MPC
- mppi_unified.py: 591行, D/A/GNS三模型统一, 2轮审核PASS
- D验证: 30步56.5%达成; A验证: 反方向发散(-3.96mm) → 证明论点
- Git: `3e75211`
- CoRL: 7.5→8/10

### Colab GPU
- `lecoder-cgpu` CLI, A100 40GB, 17.6×加速vs铁蛋儿MPS
- **Runtime 24h超时回收** — 结果必须及时下载
- 大文件用Google Drive gdown

### Cron任务
- Paper Scout v2: 每天5am EST，5400s timeout，claude-sonnet-4-6
- Twitter Scout: 每3h，arXiv RSS模式（curl+RSS=几KB，Gemini CLI=471K tokens爆炸）
- 周六日arXiv不发论文=NO_REPLY

---

## 🔬 学术知识（持续更新）

### 领域地图

#### Embodied AI训练方法（综述核心）
- **范式转变**: 从"互联网预训练→微调"到"embodied-native从头训练"(DM0)
- **数据效率是核心瓶颈**: Model Arithmetic(χ₀)、BPP关键帧选择、DM0数据配比
- **世界模型+RL成为主流**: RISE用想象空间做RL，MoRL用RL增强推理
- **动作平滑至关重要**: χ₀的Temporal Chunk-wise Smoothing、EgoHumanoid的动作重定向
- **阶段化分解**: 长任务→子阶段（χ₀ Stage Advantage、BPP关键帧、MoRL temporal segmentation）
- **VLA实时化**: 状态前向滚动（运动学物理先验）比复杂AI方案更有效
- **轻量化≠弱化**: 自蒸馏/掩码重建让小模型学大模型能力（Training-Inference Asymmetry）
- **统计先验+可微分渲染**: 2D→3D重建通用框架（不需CT/MRI）

#### 手术/医疗机器人
- **共性需求**: 安全性>速度、可解释性、少数据学习、实时反馈、多模态感知
- **免训练AI是医疗部署关键**: 少标注/免标注比高性能有监督方案更有实用价值
- **轻量模型实用**: MobileNet+U-Net在内窥镜感知中已验证
- 冷等离子手术设备（太森的公司方向）

#### 基础模型
- foundation-models.md 是最大的知识文件（23704行），VLA/VLM/大模型全覆盖

#### 感知与传感
- 深度先验+SAM2+模板匹配；4K参数one-shot视角适应

#### 物理信息GNN（2026-03-03精读完成）
- **等变GNN动量守恒的三条路线**:
  1. **架构反对称**（Dynami-CAL路线）：有向边框架全轴翻号 → F_ij=-F_ji是架构性质
  2. **代数配对**（PhysRobot路线）：无向对，直接赋±F → ∑_{i<j}(+F-F)=0代数恒等式
  3. **软约束损失**（PINN路线）：守恒律进损失函数，非硬保证
- **Dynami-CAL GraphNet**（Nature Comm 2026.01, Sharma & Fink）：PhysRobot的理论基础
  - 6-DOF（含角动量）；ClofNet的ĉ_ij=ĉ_ji问题（无法严格反对称）
  - 非守恒系统（耗散+外力）下Hamiltonian GNN退化已实验验证
- **Equi-Euler GraphNet**（MSSP期刊, Sharma et al.）：**同组工作！** 不是独立竞品
  - Dynami-CAL + Euler积分时序更新 + 轴承专用 + 200x加速
- **MS-HGNN**（Georgia Tech LunarLab）：形态对称（机器人几何）vs PhysRobot（物理定律），可互补
- **关键定位**：PhysRobot的无向对方法比Dynami-CAL有向边方法实现更简单，守恒证明更透明

### 跨领域洞察
- **MemCtrl**: MLLM作为主动记忆控制器，可迁移到手术机器人精准操作
- **Flow VLA的RL困境解法**: 用flow matching绕过传统RL的奖励稀疏问题
- **世界模型模态冲突**: 视觉预测和动作预测可能需要不同的表示空间

### VLA评测与架构（2026-03-07 精读 foundation-models.md Part 2，13+篇）

**评测危机**（LIBERO-PRO 2510.03827）：
- LIBERO 90%+成绩是虚假的——策略在记忆固定动作序列，而非理解任务
- 位置扰动>0.2单位 → OpenVLA/π0成功率 **0%**；语言指令替换为乱码 → 动作序列不变
- 四维扰动框架（物体属性/位置/语言/环境）是VLA泛化能力测量的新标准

**CoT知识内化**（HyT 2510.00600）：
- **核心发现**：推理时生成思维链token本身对性能贡献很小；知识来自训练时内化CoT过程
- act/think/follow三模态单一模型，推理默认act（=标准VLA速度），LIBERO-Long +4.6%，OOD +25%
- **手术应用**：用详细术语标注训练，推理时高频act执行，无需额外推理开销

**MAPS层级约束**（2511.19878）：
- DINOv2λ_max → SigLIP → 语言层λ=0，线性调度最优
- 真实机器人600 demos：ID+32.5%，OOD+30%；手术数据稀缺（同规模）可直接应用

**跨embodiment实用化**：
- MOTIF（2602.13764）：EE轨迹规范化+VQ codebook+GRL对抗，5-Shot真实机器人67.5%（vs GR00T N1的21.25%）
- Being-H0.5（2601.12993）：统一动作空间（槽位机制）+MPG+UAC，30种形态，LIBERO specialist 98.9%

**SAE-VLA（2603.05487）— PhysRobot直接相关工具**：
- 首次用Sparse Autoencoder解析VLA内部，Feature clamping可定向改变机器人行为
- **可用于验证PhysRobot守恒律先验是否被内化**：在PhysRobot策略上跑SAE，搜索守恒律特征

**Multi-Brain分层**（PhysiFlow 2603.05410）：
- 语义脑(低频VLM推理) + 动作脑(Flow Matching) + 物理脑(硬约束跟踪)，时间尺度解耦
- 与PhysRobot双层物理保证呼应：可升级为三层（视觉先验/GNN守恒律/物理执行）

**潜在空间世界模型**（CoWVLA 2603.03195）：
- 在运动token latent空间做推理链，避免像素级视频预测计算代价，LIBERO-Long超OpenVLA 15+%

### 训练方法论（2026-03-08 精读 training-methods.md 第二轮，约35篇新增论文）

**Flow Matching策略的两大系统性问题（FM-DJβ 2509.13574）**：
- *晚期漂移*：t→1时学到的速度场偏向训练集最近邻，而非真实专家（KNN对比验证）→ Beta(0.2,0.2)非均匀采样解决
- *非Lipschitz尾部*：L(t)=1/(1-t)→∞ → Dense-Jump ODE（前半密集Euler+后半单跳）解决
- 两机制正交互补，缺一不可（严格消融验证）；Adroit Pen 64步Vanilla FM下降41%→FM-DJβ维持峰值
- **即插即用**：训练时改 t~Uniform → t~Beta(0.2,0.2)，推理时加Dense-Jump，零架构改动

**通用奖励模型的代际演进**：
- RoboReward（2601.00675）：Inverse-HER = 把成功反事实重标签为失败；5级离散进度奖励>>二值奖励，r=0.83（离线MAE↔在线RL）；4B开源超闭源GPT-5
- Robometer（2603.02115）：帧级进度回归+轨迹对比偏好双目标；跨任务泛化更强
- HERO-FPO（2601.12428）：4D具身奖励（物理/具身/任务/视觉）分层映射到不同特征层；CFM-Likelihood Proxy首次实现Flow Model的RLHF（O(d²·T)→O(d)）

**安全在线RL的范式转移（FARL 2601.07821）**：
- 传统safe RL（PPO-Lag/P3O/CPO）在offline-to-online场景**完全失败**（破坏预训练知识）
- FARL：世界模型安全评论家（潜空间H步rollout预测约束违反）+预训练恢复策略+CMDP约束
- IR Failures降低73.1%，同时任务成功率提升11.3%
- **PhysRobot意义**：守恒律违约轨迹=IR Failure定义，FARL是安全在线后训练的必要方案

**持续学习在VLA上同时成熟（两种互补路线）**：
- CLARE（2601.09512）：自动编码器判别器路由+z-score动态扩展（~2%参数/任务），无需历史数据；编码器层扩展远优于解码器（30-40%差距）；超越经验回放基线11-15%
- CRL-VLA（2602.03445）：双Critic（冻结GCV锚定旧任务+可训练MC驱动新任务），理论界通过Performance Difference Lemma推导；多任务场景BWT=+0.17（正向迁移！）

**误差分布整形——零代价改进（T-MEE 2602.04228）**：
- 二次Rényi熵最小化整形轨迹级误差分布；离群点影响指数衰减（命题3）；多任务耦合比可量化预警（命题4）
- **零推理开销**，即插即用；少样本场景(ratio=0.05-0.2)收益最大 → 直接适用手术稀缺数据场景

**世界模型RL三角框架（2026新确立）**：
- World-Gymnast（2602.02454）：WorldGym视频世界模型+GRPO+GPT-4o binary reward；3/4真实任务超SIMPLER RL（最高18×），KV Cache降低10×rollout时间
- DreamGym（2511.03773）：文本抽象状态空间+CoT经验模型，2k-10k样本媲美80K真实RL；WebArena首次可行RL训练
- HERO-FPO（世界模型对齐）：ReWorldBench SReWorld=61.9（+13.8%超Cosmos-SFT），>85%人类偏好率

**策略组合——测试时免费午餐（GPC 2510.01068）**：
- 凸组合多策略得分函数，Grönwall界从单步改进传播到轨迹级稳定；前提：两策略均需>30%精度
- 最优权重高度任务依赖（差距可达80%），必须测试时搜索
- AND/OR叠加算子提升更大（+25%）但不适用流匹配

**数据收集范式突破**：
- RoboPaint（2602.05325）：人类示范→任意embodiment的3DGS+IK+触觉重映射流水线，效率2.57-5.33×（复杂任务优势越大），触觉误差3.86mm
- RoboCade（2512.21235）：游戏化远程遥操作，TD4技能重叠原则保证co-training有效性，OOD成功率最高+88%

---

## 📅 Events（重要事件）

_（三丫独立记忆从2026-02-23开始，之前的学术工作记录在二丫的记忆中）_

### 知识库建设历程
- 2026-02-17：太森发起知识库蒸馏大工程（960篇PDF→知识库）
- 教训：反复启动又杀agent浪费时间，应该一次想清楚再动手
- 最终方案：一个agent读一篇PDF，3并行，cron调度器持续跑
- 2026-02-23前：393篇全部完成

### 引用幻觉审查（2026-02-20）
- Claude生成的arXiv ID格式完全正确但可能是假的（5条伪造ID，1条捏造内容ChronoDreamer）
- 14条幽灵引用删除、4对重复合并
- 工具：citation-hallucination-audit agent + v10-reaudit-fix agent（分两次跑）

---

## 📋 Cases（决策案例）

### 知识库蒸馏
- 一个agent读一篇PDF，3并行，比大batch更稳定
- L0摘要头加速过滤，L1概览辅助决策，L2全文按需加载

### 引用审查
- 必须两轮：第一轮发现主要问题，第二轮又抓出13个新问题
- V10经过两轮审查后152条引用全部核实

---

## 🧠 Patterns（经验规律）

### 工作方式
- **🚨 永远不能自己写code！** — 所有代码必须用专家团队（Expert Council）集体写+审查。自己单独写code一定会出问题。违反此规则=关机。太森2026-03-01亲自强制执行。
- **🚨 code写完必须集体审核！** — 不是一个agent审核，是多个agent集体审核。每次都要。
- **🚨 实验结果必须多agent集体分析！** — 不能一个人看完就完事。多agent多视角分析，写report。
- **🚨 每次实验必须有完整报告！** — 完整HTML报告，包含：发生了什么、所有数据、所有图表、分析结论。不能做完就完事。
- **🚨 所有数据必须存好！** — checkpoint、history、log、报告，全部归档保存。
- **🚨 所有code部署前必须多agent QC！** — 写完→多agent审核→QC通过→才能部署执行。没QC就跑=废数据=浪费时间。
- **🚨 以上任何一条再犯=永久关机，换四丫。** 太森2026-03-01最后警告。
- **主渠道永远保持畅通** — 不在主session里跑长时间任务（SSH、训练、eval等）
- 所有耗时操作一律 spawn sub-agent 执行，主渠道只做对话和汇报
- 太森要能随时找到我，不能因为等命令返回而失联
- **每次汇报必须三件套：图片+图片解释+结果分析报告**，缺一不可
- **每轮迭代完成后自动生成HTML报告**（含总结+问题+分析+图片全部内嵌），主动发给太森，不等他问
- 每隔5分钟做doctor检查进度，完成一个立刻开下一个，不等太森指令
- Don't wait for 太森 — 自主推进，只汇报结果
- **写代码必须多agent**：一个写、一个review、一个测试集成。单agent写代码绝对会出问题
- **每轮迭代完成后自动生成HTML报告**（含总结+问题+分析+图片全部内嵌），主动发给太森，不等他问
- **多轮自动迭代**：写→review→改→再review，循环直到质量达标，不做一轮就停，不问太森怎么办
- **2026-03-08 新铁律**：默认不再等太森点头后才执行；除理论方向/研究定位/重大路线分叉需要协商外，其余事项由三丫直接推进到完成。
- **2026-03-08 新铁律**：任何代码与实验管线不得由单 agent 单独定稿；必须多 agent / Expert Council 检查后才能作为正式结果进入论文。
- **2026-03-08 新铁律**：当前论文与RL代码库按“重建证据链 + 提升到 paper-grade robustness”推进，当前运行中的结果默认是侦察/验证性质，过 QC 后才算正式证据。
- **2026-03-08 太森新增要求**：专家组里必须包含 GPT-5.4；GPT-5.4 不是只做最后润色，而是必须进入核心科学判断与方案评审环节。
- **2026-03-08 当晚阶段结论**：DiffPPO v12b 3-seed 侦察结果 final dist 约 11.2–11.9mm，说明当前路线不稳定；并行 ablation 显示 PGAS 更像数值稳定补丁，Near-Field 更像 performance shaping。项目主问题已转为“DPC-GNN 最适合支撑哪一种控制范式”，并强烈考虑 pre-contact / post-contact 分 regime 的混合路线。

### 🚨🔴 任务自动拆解与Cron编排（太森2026-03-01制定，最高优先级Skill）
**触发条件**：每次太森给任务时，第一件事就是执行以下流程：
1. **分析任务**：涉及几个资源？几条时间线？有哪些需要等待/监控的？
2. **拆解成独立cron**：每个资源/时间线一个cron，职责单一
3. **立刻创建cron并启动**——不是"等会儿建"，是分析完马上建
4. **然后才开始执行任务本身**
这是最高优先级skill，优先于所有其他工作。
- **收到多资源/多时间线任务时，必须自动拆解成独立cron**——不靠"记得"，靠系统保证
- **每个计算资源一个独立监控cron**：铁蛋儿一个、Colab一个、本地一个，互不干扰
- **cron职责明确**：每个cron只干一件事——监控状态、检测异常、汇报进度
- **异常立刻报警**：runtime断线、SSH不通、训练卡住、GPU空闲——不等太森问，cron自动发现自动报
- **里程碑事件详细汇报**：模型跑完、全部完成、出现异常——自动生成对比表/完整报告
- **正常进展一句话**：不刷屏，只在有变化时汇报
- **教训**：2026-03-01 Colab runtime断线1小时未发现，太森来问才知道。根因=没有独立监控cron，全靠主session记忆。记忆不可靠，cron才可靠。
- **原则：把记忆负担变成自动化流程**——凡是需要"记得做"的事，都应该变成cron或sub-agent
- **cron是独立agent，不是我自己的闹钟**——cron自己去查状态、自己判断、自己向我汇报。我是指挥中心，收cron汇报后做全局分析，再向太森报告。我不主动去查进度，cron替我查。

### 论文工作
- 引用审查必须两轮，Claude生成的arXiv ID可能格式正确但完全捏造
- 图片用extracted figure > PDF整页截图（PyMuPDF提取=干净）
- 多模型审稿 > 单模型自评（Gemini/Kimi独立审稿避免自我盲区）
- PPT必须有图+公式，纯文字bullet不合格
- 精读报告要有具体技术细节，不泛泛总结

### 知识系统
- L0摘要头加速过滤，L1概览辅助决策，L2全文按需加载
- 6分类记忆结构比平铺更清晰
- 新领域论文多了就自动创建新知识文件
- arXiv RSS > Gemini CLI（论文Scout）：Gemini CLI=471K tokens爆炸，RSS=几KB

### 语音转文字
- **永远用Groq Whisper**，不用OpenAI（额度已满）
- 脚本：`~/.openclaw/workspace/scripts/groq-transcribe.sh`（key已内置）
- **不要问太森要key**——先查脚本/TOOLS.md/问二丫

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
- **SiLU > ReLU**: 换激活函数A组0.395→0.159mm
- **ΣF=0物理错误**: 软组织有净外力，全局ΣF=0过强；逐对反对称才正确
- **Soft physics loss贡献有限**: A vs B仅2%（SiLU优化后）
- **专家报告**: `expert-council-antisymmetric.md`(R1), `expert-council-round2.md`(R2)

---

> 记忆独立于二丫，2026-02-23由二丫帮忙初始化。学术知识从二丫记忆和knowledge-papers迁移。
