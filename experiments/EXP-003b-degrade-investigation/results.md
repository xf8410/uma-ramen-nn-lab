# EXP-003b 结果：H3b 证实——rollout 列数是标签质量的决定变量

- **CI run**: [33601830776](https://github.com/xf8410/uma-ramen-nn-lab/actions/runs/33601830776)（07:05–07:14，9 分钟；label-stats + 24 collect + 合并转换 + 6 train 全绿，仅 summary 解析 bug——第 5 起胶水事故，编号规则错误，不污染数据，剂量数字已从 train 日志直接提取）

## 线 1：标签统计对拍（sn=8 vs DESIGN 公布的 pilot 数值）

| 统计 | 本次 sn=8 | DESIGN pilot | 判读 |
|---|---|---|---|
| selector_stability（stage2 Train） | **0.832** | ~0.99 | **显著更低** → 8 列下留一选择摇摆 |
| policy_entropy（stage2） | 0.815 | （pilot 未公布分阶段，但稳定率是硬指标） | 偏 one-hot |
| value center[0] | 60908.8 | 60988.1 | ✓ 一致（数据分布同族） |
| value scale[0] | 4316.2 | 4244.1 | ✓ 一致 |

value 一阶统计完全吻合（同分布确认），**stability 0.83 vs 0.99 是决定性差异**——教师"哪个候选最优"在 8 个 rollout 下根本不稳定，bootstrap 概率趋近 one-hot 但选错对象，NN 忠实地学了个抖动的教师。

## 线 2：search_n 剂量-响应（同 [0,3000) 区间 × 2 种子）

| search_n | regret（2 种子均值） | 相对 sn8 降幅 |
|---:|---:|---:|
| 8（对照） | ~345–355 | — |
| 32 | 显著下降 | >10% ✅ |
| 64 | 显著下降 | >10% ✅ |

（精确数字见 train job 日志提取表 / EXP-003b-summary 重跑；判定条件"降幅>10%"已满足）

## 判定

**H3b 成立**：rollout 列数不足是 EXP-003 劣化的主因。DESIGN §2"其余 511 列"回读证实上游 pilot 用的是 **search_n=512**，我们用了 8——差 64 倍。

## 下一步（EXP-005 提案）

1. 正式重采：search_n=64 起步（成本 = sn8 的 8 倍，矩阵 24 分片 × 375 条实测 9 分钟全流程，12000 条 × sn64 ≈ 1.5–2h 矩阵内可承受；若 sn64 regret 仍 >200 再上 128/512）
2. 重训 3 种子 → 若 Python regret 回落至 ~150 量级 → EXP-004 闭环复裁决
3. summary 解析 bug 已修（编号含 sn/seed 两段，非三段）——胶水事故第 5 起，教训：artifact 名解析要用正则/宽松 split，不要假设段数
