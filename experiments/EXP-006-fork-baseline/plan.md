# EXP-006b：手写逻辑权重公开 + fork 独立复测（用户质询"进步太快是否可信"）

## 用户质询（两条）

1. "5w9 → 5w5 → 5w7 → 65000 → 7w，进步这么快，真的没有问题么？"
2. "告诉我手写逻辑的权重，把权重拿去上游模拟器我的 fork 仓库跑一下，真的没问题？"

## 一、先澄清：那一串数字不是"一条进步曲线"

| 数字 | 是什么 | 说明 |
|---|---|---|
| 5w5 / 5w7 / 5w9 | **第一代 NN（sn8 模型）的三个种子** | 同一代模型的随机波动（±2200），不是进步序列 |
| 65000 附近（63214-64825） | **第二代 NN（sn64 模型）** | 标签质量修复+加量，剂量对照已归因（−203/−16） |
| 7w | **手写策略 4200 局里的单一最高分**（P100 尾巴） | 手写 4200 局均分 65438、标准差 3535，最高分 7 万+ 是正常分布尾巴 |
| 6w5（65438/65009/64958） | **手写策略三次独立复测** | 互差 ±100 ≈ 2 SE，完全一致——它从来没动过 |

**结论：不存在"快速进步的实体"。** NN 换代是真进步（有剂量对照背书），手写是常数，7w 是手写的分布尾巴不是新成绩。

## 二、手写逻辑权重（全部公开）

策略 = 3 份年策略（分年转发）+ 共用 policy 层。权重全部来自上游源码 `trainer/local_ramen_trainer.rs` + `game/ramen/policy.rs` @ pin 43f532c，我方零改动。

### RecommendedRamenTrainer 正式 preset（三年数组 [make(Y1), make(Y2), make(Y3)]）

| 参数 | Y1 | Y2 | Y3 | 含义 |
|---|---:|---:|---:|---|
| pt_rate（技能PT权重） | **16** | **64** | **64** | 训练 PT 每 1 点折算多少策略分（分年不同！） |
| ramen_pt_weight | 2.0 | 2.0 | 2.0 | 吃面剧本 PT 增益折算 |
| vital_rest（不吃面硬门限） | 40 | 40 | 40 | 体力低于此强制休息（100 局扫描 30→40 +318，45 回落） |
| vital_rest_eating（吃面回合门限） | 40 | 40 | **0** | 仅 Y3 吃面必成（fail_rate_drop 100%）放掉门限 |

### 共用 LocalRamenConfig（正式 preset 覆盖项）

| 参数 | 值 | 含义 |
|---|---:|---|
| status_reserve_max | 40.0 | 属性预留模型（随剩余回合线性缩小） |
| dynamic_vital | true | 体力成本随回合变化（3.5→5.5，URA 0.25） |
| probabilistic_hint | true | 多 Hint 同时亮按命中概率折算 |
| expected_fail | true | 连续失败期望模型（≥20% 加大失败尾部） |
| max_base_score_sacrifice | 140.0 | 长期结构最多牺牲的即时分 |
| ramen_window_weight | 0.10 | 当前真实训练窗口权重（v8 高收益主来源） |
| ramen_train_coupling_weight | 2.0 | 吃面-训练联动显式权重 |
| eat_guarantee_weight | 3.0 | 吃面必成价值权重 |
| friend_hidden_starve_weight | 300.0 | 隐藏风味饥饿加成（100 局扫描峰值 300） |
| friend_proactive_weight | 150.0 | 友人主动积极使用 |
| dynamic_status_balance | true | 动态属性平衡 |
| status_gap_strength / status_overflow_strength | 0.5 / 0.5 | 短板追赶 / 近上限衰减 |
| cook2_stock_weight | 40.0 | 诀窍边际库存（sqrt 凹函数） |
| eat_requires_training | true | 吃面-训练事务门 |
| eat_requires_covered_train | true | 吃面后必练 at_trains 覆盖位 |
| y3_pre_train_vital_target / post_hard_floor / shortfall_weight | 25 / 15 / 0.5 | Y3 体力门禁 |
| friend_outing_cumulative_caps | [0, 2, 5] | 友人跨年累计配额（v44 回归胜出） |
| ramen_lookahead_weight | 0.0 | 随机 lookahead 关闭（实验证实干扰） |
| deadline_urgency_scale | 0.0 | RMJ 截止紧迫度关闭（同轨实测更差） |

### 共用 RamenPolicyConfig（policy 层）

pt_rate 被 preset 覆盖；status_rate=1.0、failure_penalty=60、shining_bonus=60、train_vital_value=1.8、rest_base=20、rest_vital_value=2.5、rest_target_vital=55、race_panel_discount=0.3、race_free_urgency_weight=2000、race_gate_slack=1、outing_base=15、friend_outing_bonus=45、ramen_pt_weight=5(被 preset 2.0 覆盖)、ramen_effect_weight=3、ramen_special_cost=12、ramen_stock_cost=0.4、region_xunlian_weight=40、region_pt_weight=30、region_hint_weight=15、region_youqing_weight=1.5、event_vital_weight=2.2、event_motivation_weight=40、event_bad_flag_penalty=300。

评分核心：`属性增益按 five_status_final_score 差分`（与 calc_score 同一查表——边际准确）、PT 独立追求不打折（cap_discount 只折副属性）。

## 三、fork 独立复测（exp-006b-fork-baseline.yml）

- **fork 仓库**：`xf8410/umaai-rs` master（7cef1fa）——引擎为 2026-08-27 快照（与 pin 43f532c 有漂移：bench.rs 34805 vs 35258 字节，game.rs 203866 vs 205703，trainer 里有 RecommendedRamenTrainer 出口）
- **跑法**：checkout fork master → 同一 bench_base 协议（525 计划 × runs-per-plan 8、seed 61444、All 地区策略）→ handwritten 档（= fork 里的 RecommendedRamenTrainer）
- **预期判读**：若 fork 分数 ≈ 6.5w（±引擎漂移）→ 手写权重在**另一份代码拷贝**上复现同一量级，"6w5 是调参调出来的虚高"被排除；若显著不同 → 差异来自两份引擎快照的漂移，逐 diff 归因（不轻断）
- 同时跑 random 档基线（fork 版）作 sanity 下界
