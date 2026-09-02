# EXP-006e power 抑制定价 × g2110 细扫

## 动机（EXP-006d 盘面诊断直接产物）

- P90−P10 属性差：speed+489 / wisdom+459 / guts+405 / stamina+331 / **power−204（唯一负）**
- 高分局力量反而更低 ⇒ 力量被过度喂养：凹表尾巴 + 训练位冲突吃掉速/智/根回合
- g2110（Y2 短板追赶 1.1）+19.3 已采纳 ⇒ 本轮同时细扫确认峰值（g295 / g2130）

## 机制设计

上游 `dynamic_status_adjustment` 用统一 `status_gap_strength` / `status_overflow_strength`
作用五维。本补丁加 per-attribute 覆盖（仅 power 位 i==2）：

- `power_overflow_strength`：power 近上限衰减覆盖（NAN=不覆盖，base 逐位不变）
- `power_gap_strength`：power 短板追赶覆盖，**可为负**（= 允许 power 更落后）

token（006d 链上追加）：`poN`（全年前缀统一）、`p1o/p2o/p3oN`（分年）、`pgN`（可负）

## 变体矩阵（12）

| 变体 | 语义 |
|---|---|
| base | 对照（必须 65438.2±4SE 保真） |
| po100/po150/po200 | power 近上限衰减 1.0/1.5/2.0（base over=0.5） |
| pg-30 / pg-60 | power 短板追赶 −0.3/−0.6（base gap=0.5 → power 允许落后） |
| p2o300 | 仅第 2 年 power 衰减 3.0 |
| g295 / g2130 | g2110 峰值细扫（0.95 / 1.30） |
| g2110-cook60 | 已采纳最优组合复验 |
| po150-g2110 | power 衰减 + 已采纳最优组合 |
| pg-60-po150-g2110 | 三重组合 |

## 判定

- 配对 t（同种子 4200 局配对差），t≥2 且 Δ>0 采纳
- power 均值列：验证"抑制后 power 实际下降、总分上升"的因果链
- 下轮：胜出组合进 preset 或再细扫

## 状态

- [x] patch 提交
- [x] workflow 提交
- [ ] 跑批 + 裁决
- [ ] 结论回填
