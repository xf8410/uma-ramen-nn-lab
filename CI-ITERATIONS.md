# CI 迭代记录（EXP-001 → EXP-006l）

> 本仓对上游只读（`muxueliunian/umaai-rs-muxue@feat/ramen-nn-schema`，checkout 锁 SHA）。所有改动以 patch 方式在 CI 内注入，不维护 fork 副本。本文档面向外部读者，汇总自 2026-09-01 建仓起的全部 CI 迭代；每次实验的 workflow 文件、验证内容与结论均可在本仓 Actions 历史按 workflow 名检索。

## 0. 门禁与基础设施

- `lab.yml`（PR / push 门禁）：cargo check（default + onnx features）+ release bins 构建 + pytest（scripts/ramen_nn 测试）。三轮定型：
  1. setup-rust-toolchain 注入 `-D warnings` → 上游 onnx 预留接口（leaf_nn / simulate_until_terminal_or_leaf / SimOutcome）3 处 dead_code 误红 → 改用 dtolnay toolchain（不注入 RUSTFLAGS）
  2. 上游全套 cargo test 不适合作门禁：断言绑定本地 gamedata 逐位基线（如 mean=63471.125），外部数据源与上游 feat 分支有漂移即假红；且 debug profile 下 330 个整局测试远超冒烟窗口
  3. 定型：check + bins + pytest，1m19s 通过
- 上游 gamedata 入库前（43f532c）CI 从 xulai1001/umaai-rs master raw 下载；d27a6eb 起数据已在树内，直接用 pinned 数据

## 1. 实验总表

| 实验 | workflow 文件 | 验证内容 | 结论 |
|---|---|---|---|
| EXP-001a | exp-001a.yml | 手写基线锚点重测（旧管线 checkpoint/数据未留存，从零采） | base 4200 局 mean = 65438.2（三重复现，sd=54.5），定为全项目锚点 |
| EXP-002 | exp-002.yml | 教师采数试点 | 采数链路可用；单 job 拉满 30GB 磁盘事故复盘见 [INCIDENT-20260902.md](EXP-002-teacher-pilot/INCIDENT-20260902.md)，由此确立"三步验证"准则 |
| EXP-003 | exp-003.yml | NN 训练 v1（teacher → train.py → ONNX） | 首个模型产出，见 [results.md](EXP-003-train-v1/results.md) |
| EXP-003b | exp-003b.yml | 训练退化排查 | 见 [results.md](EXP-003b-degrade-investigation/results.md)（该 workflow 无 dispatch 输入，push 事件显示 failure 属预期，不影响门禁） |
| EXP-004 / 004b | exp-004.yml / exp-004b.yml | NN leaf evaluator 进 MCTS 闭环 | 见 [results.md](EXP-004-closed-loop/results.md) |
| EXP-005 | exp-005.yml | search_n=64 重回忆对比 | 见 [results.md](EXP-005-recollection-sn64/results.md) |
| EXP-006 score-audit | exp-006-audit.yml | 评分口径审计（skill_score / PT×2 / 五维凸表与 calc_score 对齐） | bench 口径与游戏评分公式逐项核对通过 |
| EXP-006 fork-baseline | exp-006b-fork.yml | 接入 ramen_space_bench + 手写/推荐双基线 | 确立 4200 局同 seed 世界配对方法学（单局口径手写 47796 vs 推荐 58380） |
| EXP-006c | exp-006c.yml | 引入"缺哪补哪"力度旋钮（dynamic status balance gap 缩放） | 正收益，方向确立 |
| EXP-006d | exp-006d.yml | 三年分治（pt_rate=16/64/64；Y3 vital_rest_eating=0） | 稳定收益，成为 preset 骨架 |
| EXP-006e | exp-006e.yml | 松油门（Y3 晚期低性价比格松门限）o1/o2/o3 | o2/o3 有增量 |
| EXP-006f–006i | exp-006f/g/h/i.yml | 各旋钮矩阵扫描与组合收敛 | 单轮增益递减（矩阵见各 plan.md） |
| EXP-006j | exp-006j.yml（[run 33695537770](https://github.com/xf8410/uma-ramen-nn-lab/actions/runs/33695537770)） | Y2 补短板 3.5/4.0/4.5 × Y3 复测 1.4/1.9 × 近上限衰减重测 | g2=4.2、o 系 1.5/1.5 进入拼接 |
| EXP-006k | exp-006k.yml（[run 33696260156](https://github.com/xf8410/uma-ramen-nn-lab/actions/runs/33696260156)） | 收尾拼接 × o 配比微调 × 无 o 对照 | **冠军 65554.2（+116.1，t=+5.91）= g2420-o2150-o3150-g3160-cook60**，9/9 采纳 |
| EXP-006l | exp-006l.yml（[run 33696850466](https://github.com/xf8410/uma-ramen-nn-lab/actions/runs/33696850466)） | 换种子 70000 泛化验证 × 终选决胜（g2 4.0/4.2、o3 1.0/1.5） | **4/4 变体全部复现；+62.3（t=+3.33）；g2 4.2>4.0、o3 1.5>1.0 → 配方定稿** |
| EXP-SYNC-260901 | upstream-sync-260901.yml | 换 pin 43f532c → d27a6eb 保真检查 | base 4200 逐位复现 65438.2 → 数据更新未影响采样空间 |
| EXP-007 | exp-007.yml | 新速度卡对比 | 卡名→卡 ID 定位未完成，实验搁置（patch_exp007.py 留档） |

## 2. 定稿配方（手写逻辑调优终点）

RecommendedRamenTrainer 三年分治 + LocalRamenConfig 覆盖：

- 三年 pt_rate = 16/64/64；vital_rest = 40/40/40；vital_rest_eating = 40/40/0（仅 Y3 吃面必成时放掉硬门限）
- 缺哪补哪力度（dynamic balance gap 缩放）：Y2 = 4.2、Y3 = 1.6
- 材料珍惜度 cook2 = 60
- 松油门：o2 = 1.5、o3 = 1.5
- 其余保持：status_reserve_max=40、max_base_score_sacrifice=140、coupling=2.0/guarantee=3.0/starve=300/pro=150、友人配额 [0,2,5]、lookahead=0（证实有害）

证据链：

- 基线 65438.2（4200 局，seed 61444 世界，三重复现）
- 调优后 65554.2 = **+116.1（t=+5.91）**，同世界配对
- 换种子泛化：seed 70000 世界 **+62.3（t=+3.33），4/4 变体全部复现** → 排除过拟合
- 对应 patch：[EXP-006-wisdom-vital/patch_exp006c.py](EXP-006-wisdom-vital/patch_exp006c.py)、[EXP-006-yearphased/patch_exp006d.py](EXP-006-yearphased/patch_exp006d.py)、[EXP-006e-power/patch_exp006e.py](EXP-006e-power/patch_exp006e.py)（+ patch_exp006e_fix.py）

## 3. 下一步（已规划，未开工）

1. preset 固化 → 蒸馏（ramen_teacher_collect 大规模采数）
2. RL 自我对弈（蒸馏后的增益路径）
