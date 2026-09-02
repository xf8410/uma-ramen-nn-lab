# EXP-002：教师数据采集（矩阵并行版）

## 假设 H2
在 pin 43f532c 上，用 Actions `strategy.matrix` 8 个并行分片 job 采 12000 条教师样本（gen1 采样空间），wall-clock 压进 ~10 分钟量级；各分片 manifest 配方哈希一致、index 区间互斥，合并后与顺序采集同分布等价。

## 背景（用户裁定的做法，2026-09-02）
- **「矩阵」= CI 里有并行进行的矩阵**（Actions strategy.matrix 多 job 同时跑），**不是**一个 job 内部顺序循环/断点续跑——用户此前 44 次手写逻辑迭代就是这么做矩阵的，比单 job 快得多
- 我此前"单 job 顺序 resume 12000 条"的设计属于错误理解，作废
- 可并行依据：`sample_position(space, cfg, index)` 按 index 确定性采样，分片区间互不重叠 → 并行结果与顺序等价；采集 bin 的 manifest（recipe_hash / gamedata_sig / git_commit）天然满足准则 §2

## 方法
- 矩阵 8 shard × 1500 条 = 12000；search_n=8；shard_size=256；radical_factor_max=1.4；配额默认 20‰/30‰；region=all（bin 内强制）
- 每 shard：`--count start+1` 单条冒烟 → 同目录 `--count start+1500` 续跑拉满（--count 为累计语义）
- assemble job：校验 8 个 manifest（recipe_hash 一致 / 区间连续不重叠 / finished_at 齐）→ 重排 part 文件合并为单一 dataset 目录 + merged manifest → 上传 `EXP-002-dataset`

## 验收
- [ ] 8/8 shard 成功；总 accepted ≈ 12000 − skipped_uncaptured
- [ ] recipe_hash 8 片一致；区间 [i·1500, (i+1)·1500) 无缝无重叠
- [ ] 合并读回条数 == accepted 合计
- [ ] wall-clock（矩阵版）记录进 LEDGER，与顺序版估算对比
- [ ] 数据体量 < 2GB（artifact 上传成功即证）

## 不做
- 导出 npy / 训练 → EXP-003（消费 EXP-002-dataset）
- search_n 敏感性对照 → 若后续验收分数不达标再立专项
