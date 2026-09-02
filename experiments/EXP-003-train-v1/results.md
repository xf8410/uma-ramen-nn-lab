# EXP-003 结果：3 种子训练完成，Python 侧判读 = 劣化（按预案停，不下结论）

- **CI run**: [33588447596](https://github.com/xf8410/uma-ramen-nn-lab/actions/runs/33588447596) ✅（03:48–03:56，全 5 job 绿；convert + 3 种子矩阵 + summary）

## 数字

| seed | best_regret | epochs | params | ONNX 对拍 |
|---|---:|---:|---:|---|
| 20260830 | 305.7 | 103 | 308,917 | ✅ <1e-4 |
| 20260831 | 327.0 | 129 | 308,917 | ✅ <1e-4 |
| 20260832 | 296.4 | 116 | 308,917 | ✅ <1e-4 |
| **均值** | **309.7** | | | |

参考：旧 pilot 11957 条 × 15 epoch × 3 种子 = **148.8**（DESIGN §5，同协议"非正式对照"）

## 判读

- 本仓 plan 预设闸门：mean > 200 = 劣化，**先查数据/标签，不许下结论** → 触发
- 产物有效：EXP-003-model-seed* ×3（best.pt + model.onnx + metrics.jsonl + run.json），EXP-004 直接可用
- 训练机制本身健康：早停正常（103–129 ep）、容量自适应选档、种子间散布 ±15（协议无种子方差异常）

## 劣化疑点清单（EXP-003b 排查项，按嫌疑排序）

1. **rollout 列数太少**：labels 的 bootstrap/cross-fit 建立在"每候选 rollout 分数列"上。本次采集 `search_n=8` → 每候选 8 列。bootstrap 512 draws 在 8 列上概率趋近 one-hot，policy 标签信息量骤减；cross-fit value 方差大。上游 pilot 的 search_n 未知，待查
2. **协议错位**：pilot 是 15 epoch 早停；我们跑满早停（100+ ep）。跑更久反而更差 → 指向标签质量而非欠拟合
3. 数据分布本身（11837 vs 11957 条，同 gen1 空间）——嫌疑最小

## 教训（胶水层第 4 事故，同种病）

summary 找 `{d}/seed{X}/metrics.jsonl` 而 artifact v4 上传 `saved_models/seedX` 会剥掉最外层目录 → 文件在 artifact 根。与 EXP-002 assemble 的 part 定位是同一病根（对 artifact 目录结构的假设）。修复：以文件实际位置为准 + 缺失时断言列出实际内容（PR #8）。
