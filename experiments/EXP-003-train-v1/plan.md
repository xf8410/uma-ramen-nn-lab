# EXP-003：搜索蒸馏训练（矩阵多种子）

## 假设 H3
在 EXP-002 数据集（11837 条教师样本，pin 43f532c 采集配方）上，按上游 scripts/ramen_nn 全链路（导出 npy → 生成标签 → 训练 → 导出 ONNX）训练 3 个种子的蒸馏网络；Python 留出集期望后悔值落在旧 pilot 量级（11957 条 × 3 种子均值 148.8，同协议参考值），产出可直接进 Rust 闭环验收的 model.onnx。

## 前提（已完成）
- EXP-002-dataset：run 33585590880 artifact（manifest + 56 parts，11837 条）

## 管线（全部上游 pin 代码，本仓零新算法代码）

| 步骤 | 工具 | 说明 |
|---|---|---|
| 1 导出 | `ramen_export_npy --raw` | bincode 分片 → npy 数组目录（x[754]/legal_mask[234]/CSR 候选 + cand_scores/cand_valid），meta.json 记 plan_count |
| 2 标签 | `labels.py` | policy = 配对 Bayesian bootstrap 512 draws 最优概率；value = leave-one-rollout-out cross-fit 三路（mean/std/rf=1.4 排名加权） |
| 3 训练 | `train.py` | 组合切分留出（split_by=combo，index%plan_count）；模型容量自适应（<25k → 64/1/192/2, dropout .15）；早停监控期望后悔值 patience=20 |
| 4 导出 | `export_onnx.py` | opset 13 + 算子白名单 + PyTorch/ORT batch1&7 对拍 <1e-4 |

## 矩阵（用户裁定的做法）

- **3 个训练 job 并行 = 3 种子**：20260830 / 20260831 / 20260832（train.py --seed；初始化差异 + 抽稀差异的方差覆盖）
- convert job（导出+标签）单 job 一次，产物 artifact 共享给 3 个训练 job
- summary job 汇总 3 种子 best_regret 对比

## 验收（Python 侧，非最终裁决）

- [ ] 3/3 训练 job 成功，各产出 best.pt + model.onnx + metrics.jsonl
- [ ] ONNX 对拍最大误差 < 1e-4（export 脚本内置，失败即挂）
- [ ] 3 种子 best_regret 均值与旧 pilot 148.8（11957 条 × 15 epoch 参考值）同量级；明显劣化（>200）须先查数据/标签再谈结论
- [ ] **最终裁决不在本实验**：Rust 侧纯网络完整育成 vs ANCHOR-003（64958±137.7）配对检验 = EXP-004，t>2 才放行（准则 §0.4）

## 不做

- 超参扫描/结构消融（simple vs softmax attention 等）——数据量到位后按 DESIGN §5 协议复验，另行立项
- Rust 闭环验收（EXP-004）
- choice 头训练（第一代冻结 choice loss=0，占位行为零）
