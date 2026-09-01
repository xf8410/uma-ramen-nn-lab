# 上游 pin 白名单（准则 §0.5）

> 本仓对上游只读。下表是当前唯一合法的上游引用；变更必须走账本新条目 + 基线重测。

## 当前 pin

| 项 | 值 |
|---|---|
| 仓库 | `muxueliunian/umaai-rs-muxue` |
| 分支 | `feat/ramen-nn-schema` |
| commit SHA | `43f532c599d8591f16b1fcdd2e301ebff858d511` |
| 首次 pin 日期 | 2026-09-01 |
| CI 消费方式 | `actions/checkout@v4`（ref 锁 SHA），只读 |

## 为什么 pin 这个 commit

- `feat/ramen-nn-schema` = master(eeae510b) + 8 commits NN 管线（policy_schema 冻结格位 / teacher_collect / export_npy / ramen_nn_trainer / advantage_probe / SpecialSelect 还原）
- master = eeae510b 正是手机主仓（uma-juece-ramen）pin 的上游基线，闭环口径同源
- 43f532c 含 8/31 最后一批修复（on-policy probe、SpecialSelect 还原、SpecialSelectMode 三档口径）

## 换 pin 规则（触发即账本登记）

1. 上游推送新 commit 且需要其修复/功能 → 新条目写明 diff 范围
2. 必须重测：手写基线 300 局（§0.2 基线同局可比）
3. 必须冒烟：smoke job 绿 + cli_args.txt 参数面比对（无 diff 才换）

## 已知上游缺陷（pin 时不修，patch 方式处理）

- `--features onnx` 下 3 处 dead_code（`leaf_nn` / `simulate_until_terminal_or_leaf` / `SimOutcome`，E4/E6 预留接口）——`-D warnings` 编译红，dtolnay toolchain 不注入 RUSTFLAGS 可过；EXP-004 消费这些接口时再以 patch 激活
- `ramen_handwritten_choice.rs` 1 处 dead field warning（ChoiceRow.stage）
- gamedata 不入库（manifest 记签名 ✓）——CI 走 xulai1001/umaai-rs master raw 下载

## 永不做的事

- ❌ fork 上游并维护本地分支副本（用户 2026-09-01 明确裁定）
- ❌ 向上游提 PR / issue（迭代自持，改动落本仓 patches/ 与 scripts/）
- ❌ 引用未在上表的 SHA / 分支名（含 floating ref `feat/ramen-nn-schema` 不带 SHA）
