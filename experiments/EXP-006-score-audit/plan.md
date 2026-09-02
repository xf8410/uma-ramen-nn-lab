# EXP-006：评分审计（"算两遍"）+ 手写逻辑优化的机制底座

## 背景（用户质询）

用户怀疑评分口径：评分 = 属性 + PT + 技能点，PT（训练获得的技能点）的技能分是否被算了两遍。

## 上游公式（crates/umasim/src/game/uma.rs @ pin 43f532c，直接引用非我方实现）

```
calc_score() = skill_score                                  （已学技能评分，含固有 510 起）
             + floor(skill_pt + total_hints × 6.5) × 2.0    （PT 折算分：pt_score_rate=2.0, hint_pt_rate=6.5）
             + Σ five_status_final_score[min(属性, 上限)]   （五维查表分，凸函数查表）
```

## "算两遍"判定：结构上不可能

- `skill_pt`（终局**剩余**技能点）在公式里只出现一次（total_pt 内）
- 花掉的 PT 变成已学技能 → 进 `skill_score`，同时**从 skill_pt 里扣掉**
- 一点 PT 要么按"未花"计 PT 折算分，要么按"已花"计技能分，**互斥且各计一次**
- RMJ PT（scenario_pt_yN）**完全不进 calc_score**——它只决定 RMJ 大成功与后续 buff，与评分无直接加法关系
- bench 的 score 列 = `game.uma.calc_score()` 原值，报告侧从不重算评分，无双算路径

## 但口说无凭 → 审计（本实验）

CSV 原缺 `skill_score` / `total_hints` 两列，无法从 CSV 独立重算评分。本实验：

1. **patch_bench.py**（lab 侧，upstream 只读）：bench.rs 精确替换 4 处，CSV 增加两列（31→33）
2. **exp-006-audit.yml**：同锚点协议重跑 bench（handwritten + nn-seed20260830，525×8rep、seed 61444）
3. **审计步**：用 constants.json 的查表+系数**独立重算每局评分**，逐局断言 == 模拟器结算；输出分量分解（五维分 / PT 分 / 技能分占比）

## 验收

- [ ] 补丁 4 锚点各恰好命中 1 次（防 pin 漂移）
- [ ] 两组成 itertools4200 局 × 2 重算逐位相等（max|diff| = 0，mismatch = 0）
- [ ] 输出三分量占比表（回答"评分是怎么构成的"）

## 与 EXP-006 主线（手写逻辑优化）的关系

本 patch 机制（lab 侧改 upstream checkout → 本地构建）就是后续手写优化 `OptimizedRamenTrainer` 的同一底座；评分审计先把它跑通。
