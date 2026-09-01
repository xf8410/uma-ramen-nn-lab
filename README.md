# uma-ramen-nn-lab

拉面杯 NN 决策模型迭代实验室。CI 训练、配对闭环验收、append-only 实验账本。

**上游管线**：[`muxueliunian/umaai-rs-muxue@feat/ramen-nn-schema`](https://github.com/muxueliunian/umaai-rs-muxue/tree/feat/ramen-nn-schema)（Rust 教师采集/格位表/闭环基准 + Python 训练侧，均已含守门测试）。本仓不复制上游代码——CI 直接 checkout 上游分支，本仓只放**迭代层**：准则、实验、账本、workflow。

**下游**：[`xf8410/uma-juece-ramen`](https://github.com/xf8410/uma-juece-ramen)（手机端，JNI 消费 `model.onnx`）。

## 文件

- [`PRINCIPLES.md`](PRINCIPLES.md) — 迭代准则 v1。先读这个。
- [`experiments/LEDGER.md`](experiments/LEDGER.md) — 实验账本（append-only）。
- `experiments/EXP-*/` — 各实验 plan/results。

## 当前状态（2026-08-31）

| 口径 | 均分 | 备注 |
|---|---:|---|
| 手写基线 | 65445 | 旧管线锚点，EXP-001 复现中 |
| 同代集成 top6 | 66949 (+1504.7) | 导入时最优；旧管线未绑 commit |
| 目标 | 70000 | 缺口 ~3050 |

旧 ens6(v5) 已作废（权重混淆，禁复用）。

## 迭代方向（准则 §6）

1. **特征/价值侧**：SpecialSelect 补采重训（用户方向）
2. **搜索侧**：NN leaf 截断估值接入拉面 MCTS（手机端算力释放）
3. **口径侧**：模拟器诚实性（因子校准/URA buffs/换皮 id，主仓 v0.4.2 已修大半）

## 跑实验

```bash
# smoke（默认 push 触发）：守门测试 + 冒烟
# 正式实验（6h 上限，禁 --raw）：
gh workflow run lab.yml -f experiment=EXP-001
```
