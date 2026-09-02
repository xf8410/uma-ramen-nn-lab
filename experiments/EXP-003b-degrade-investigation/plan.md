# EXP-003b：劣化排查（数据/标签侧）

## 假设 H3b
EXP-003 的 regret 劣化（309.7 vs pilot 148.8）主因是**教师 rollout 列数不足**（search_n=8 使 bootstrap 概率趋近 one-hot、cross-fit value 方差大），其次才是协议/数据分布差异；用更大 search_n 重采 + 重训可显著回落。

## 方法（矩阵两线）

### 线 1：标签统计对拍（零采集成本，先跑）
- 用 EXP-002-dataset 的 labels.json（convert job 已产出）对比 DESIGN §1/§2 公布的 pilot 数值（11957 条口径）：
  - `policy_entropy_mean` 按阶段（pilot 数值待从 labels meta 或 DESIGN 恢复；若 DESIGN 无数值则以"分布形状"判读）
  - `selector_stability_mean`（pilot：CRN 后 leave-one-out 稳定率约 99%）
  - value_mean/value_stdev（pilot：center=[60988.10, 2140.95, 62465.22] scale=[4244.10, 791.90, 4678.82]）
- 判读：若本次 entropy 显著更低（更接近 one-hot）→ 支持假设 H3b 主因

### 线 2：search_n 对照采集+重训（矩阵）
- 矩阵 2 组：search_n ∈ {8（对照，复用 EXP-002 数据）, 32}，各 3 种子
- search_n=32 组：EXP-002 同款 8 分片矩阵重采（每片 ~4× 时长，估 10-15 min）→ convert → 3 种子训练
- 汇总：4 组（2 search_n × 3 种子）regret 对比

## 验收
- [ ] 线 1 统计对拍表落 results.md
- [ ] search_n=32 组 3 种子 regret 均值 vs 8 组（309.7）
- [ ] 判定：32 组均值 < 8 组均值 − 10%（超出种子散布 ±15 的可解释范围）→ H3b 成立，正式采集升 search_n=32；差异不显著 → 转查其他因素（协议/分布/容量档）

## 不做
- 不动标签配方/模型结构（等 H3b 判定）
- 不做完整 5 万条重采（排查阶段 12000 条够用）
