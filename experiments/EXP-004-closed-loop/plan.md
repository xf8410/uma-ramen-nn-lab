# EXP-004：Rust 闭环验收（最终裁决场）

## 假设 H4
`ramen_space_bench --trainer nn`（feature onnx，race_shield 开、special_mode=canonical）跑 gen1 全空间，NN 均分与 ANCHOR-003（64958±137.7）同口径可比；EXP-003 劣化模型预期低于手写，本实验同时标定「Python regret ↔ 闭环分数」映射。

## 口径（bench bin 头注钉死）
> 把 --trainer 换成网络策略、其余参数不动，两个数字才可比

- 同 525 计划、同 seed 基 61444（计划 +i×1000003）、同 gen1_inherit
- **runs_per_plan=8**（ANCHOR-003 是 1 局/计划：seed 方差未测；本次 8 局/计划补上，同时给 NN 组与手写对照组各 4200 局，配对检验用）
- NN 口径：race_shield=on，special_mode=canonical（bench 默认）

## 矩阵（用户裁定的做法）

| job | 策略 | runs_per_plan | 局数 |
|---|---|---:|---:|
| bench-handwritten | handwritten | 8 | 4200 |
| bench-nn-seed20260830 | nn --model seed030.onnx | 8 | 4200 |
| bench-nn-seed20260831 | nn --model seed031.onnx | 8 | 4200 |
| bench-nn-seed20260832 | nn --model seed032.onnx | 8 | 4200 |

4 job 并行；NN 每 ~4096 决策一次前向 vs 手写每决策局部搜索，预计 NN job 更快或相近（构建后每 job 分钟级）。

## 验收（§0.4 最终裁决）

- [ ] 4/4 job 成功，逐局 CSV 落 artifact
- [ ] 每组给出均分 ± SE；NN vs 手写**同计划配对差值**（同计划同种子段）与配对 t 值
- [ ] **t > 2 才判"NN 超手写"**；否则如实记"未超过"
- [ ] 「regret 309.7 ↔ 闭环 Δ」映射记录进 LEDGER（供 EXP-003b 调标签后预估）

## 不做

- no_race_shield / special_mode=raw 的消融组（研究项，另行立项）
- 模型间互相比较出结论（3 种子只是散布度量，非 3 个候选）
