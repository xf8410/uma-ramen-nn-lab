# 上游 pin 白名单（准则 §0.5）

> 本仓对上游只读。下表是当前唯一合法的上游引用；变更必须走账本新条目 + 基线重测。

## 当前 pin（2026-09-02 换 pin，待基线重测确认）

| 项 | 值 |
|---|---|
| 仓库 | `muxueliunian/umaai-rs-muxue` |
| 分支 | `feat/ramen-nn-schema` |
| commit SHA | `d27a6ebd3e0e0daeadb1bd5a3d137b97747009d1` |
| 换 pin 日期 | 2026-09-02 |
| CI 消费方式 | `actions/checkout@v4`（ref 锁 SHA），只读 |

### 为什么换 pin（43f532c → d27a6eb，ahead 8 commits）

- **数据更新 260901**（与 xulai1001/umaai-rs master 74002cf 同源）：cardDB.json +755 行（新支援卡）、
  umaDB.json +73 行（新马娘）、text_data_dict.json +783/−33——用户 2026-09-02 提出"可能更新了支援卡"，
  核实属实
- 上游 8 commits 代码：mcts_profiler bin + perf_profiling.md、output/reason.rs 决策理由排序改造、
  **sampler.rs +209/−49（需确认 gen1 空间是否受影响）**、ramen_space_bench.rs +123/−8（CSV 列可能变化）、
  search/config.rs 重构、gamedata/config.rs 微调、scripts/ramen_nn（compare_bench.py 等）
- 旁支勘察结论：xulai1001/umaai-rs 共 4 分支（master e5601c / ramen_workbench 087bad7 /
  ramen_workbench_alter d10872a / onsen_backup），拉面线活跃分支已并回 master；muxue fork 的
  feat/ramen-nn-schema 是含 NN 管线与最新数据的唯一线

### 换 pin 生效条件（未完成前旧数字仍按 43f532c 口径解读）

1. `EXP-SYNC-260901` 保真检查：新 pin 上 base 4200 局 mean 落在 65438.2 ± 4×54.5 内 → 数据更新未影响 gen1 空间；
   超出 → 基线重定义，历史所有对照数字标注「43f532c 口径」，新旧数字不跨池比较
2. EXP-006c/006d patch 锚点在新 pin 上重放验证（bench +123 行改动可能影响 patch_exp006c 的 bench 锚点）
3. 账本登记换 pin 条目

## 历史 pin

| 项 | 值 |
|---|---|
| 仓库 | `muxueliunian/umaai-rs-muxue` |
| 分支 | `feat/ramen-nn-schema` |
| commit SHA | `43f532c599d8591f16b1fcdd2e301ebff858d511` |
| pin 日期 | 2026-09-01 → 2026-09-02 由 d27a6eb 接替 |
| 口径 | 手写基线 65438.2（三重复现）、EXP-001~006 全部结论 |
| 首次 pin 说明 | master(eeae510b) + 8 commits NN 管线（policy_schema 冻结格位 / teacher_collect / export_npy / ramen_nn_trainer / advantage_probe / SpecialSelect 还原）；43f532c 含 8/31 最后一批修复 |

## 已知上游缺陷（pin 时不修，patch 方式处理）

- `--features onnx` 下 3 处 dead_code（`leaf_nn` / `simulate_until_terminal_or_leaf` / `SimOutcome`，E4/E6 预留接口）——`-D warnings` 编译红，dtolnay toolchain 不注入 RUSTFLAGS 可过；EXP-004 消费这些接口时再以 patch 激活
- `ramen_handwritten_choice.rs` 1 处 dead field warning（ChoiceRow.stage）
- gamedata 入库于 pin commit（260901 起 cardDB/umaDB/text 已在树内，CI 直接用 pinned 数据，不再依赖 master raw 下载）

## 永不做的事

- ❌ fork 上游并维护本地分支副本（用户 2026-09-01 明确裁定）
- ❌ 向上游提 PR / issue（迭代自持，改动落本仓 patches/ 与 scripts/）
- ❌ 引用未在上表的 SHA / 分支名（含 floating ref `feat/ramen-nn-schema` 不带 SHA）
