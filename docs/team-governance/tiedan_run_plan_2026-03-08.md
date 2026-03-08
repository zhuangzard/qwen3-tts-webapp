# 铁蛋儿实验排程（2026-03-08）

## 当前主机角色
- 当前老机器：指挥 / 监控 / 汇报 / 文档
- 铁蛋儿（`ssh taisen@taisens-macbook-pro-2`）：主实验机
- 铁蛋儿硬件：Apple M3 Max, 36 GB RAM
- 主仓：`~/workspace/DPC-GNN-RL`

## 并行原则
- **训练类**：默认 3 seeds 并行（最稳）
- **轻量 eval / plot / FD check**：可提升到 6 并行
- **高风险大批次**：先 3 并行验证稳定，再扩到 6
- 任何批次都必须保留：日志 + PID + monitor log

## 已启动批次
### Batch A（已启动）
- 任务：DiffPPO v12b 主模型 3 seeds
- 入口：`run_diffppo_v12b.sh`
- 远程启动日志：`logs/launch_diffppo_v12b_20260308.log`
- 结果日志：
  - `results/diffppo_v12b_seed0_run.log`
  - `results/diffppo_v12b_seed1_run.log`
  - `results/diffppo_v12b_seed2_run.log`
- 监控日志：`logs/exp_monitor_20260308.log`

## 待启动批次（按优先级）
### Batch B — StdPPO 基线
- 目标：对齐主表 baseline
- 现有入口：
  - `scripts/train_stdppo_fixed_v2.py`（内含 3 seeds 顺序跑）
  - `scripts/run_stdppo_fixed_seed1.py`
  - `scripts/run_stdppo_fixed_seed2.py`
- 建议：优先复用现有脚本，先拿稳定 baseline 结果

### Batch C — 核心消融
- `ablation_no_pgas_seed1.py`
- `ablation_no_pgas_seed2.py`
- `ablation_no_pgas_seed3.py`
- `ablation_no_nearfield_seed1.py`
- `ablation_no_nearfield_seed2.py`
- `ablation_no_nearfield_seed3.py`

### Batch D — 继续补齐消融缺口
- `ablation_no_curriculum_seed2.py`
- `ablation_no_curriculum_seed3.py`
- `ablation_full_model_seed2.py`
- `ablation_full_model_seed3.py`
- 注：这些脚本覆盖还不完整，需要先核对是否缺 seed / 缺 wrapper

### Batch E — 评估/辅助实验
- `fd_grad_check_v2.py`
- `robustness_phase3_v2.py`
- `benchmark_scenes_v2.py`
- `mujoco_baseline_v2.py` / `mujoco_baseline_v2_fix.py`

## 监控规则
- 监控进程 PID 文件：`logs/exp_monitor_20260308.pid`
- 每 5 分钟记录：uptime / vm_stat / 相关 python 进程
- 汇报只报 verified 信息：
  - 正在跑什么
  - 跑到哪一步
  - 是否异常
  - 哪些日志已生成

## 当前执行策略
1. 先观察 Batch A 稳定性
2. Batch A 稳定后，立刻接 Batch B
3. 基线稳定后，再接 Batch C / D
4. 轻量实验（FD / robustness / benchmark）插空并行

## 备注
- 历史教训：统一以铁蛋儿主仓为准，不以本机镜像为准
- 所有最终数字必须从铁蛋儿日志/结果文件回算
