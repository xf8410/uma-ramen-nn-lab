# uma-ramen-nn-lab

拉面杯 NN 决策模型迭代实验室。**独立仓库，上游只读，自持迭代**——目标把决策分从 66949（同代集成 top6）推到 70000。

**上游管线**：[`muxueliunian/umaai-rs-muxue`](https://github.com/muxueliunian/umaai-rs-muxue)（Rust 教师采集/格位表/闭环基准 + Python 训练侧）。本仓**不复制、不 fork、不向上游提 PR**——CI 以固定 SHA 只读 checkout（pin 见 [`experiments/UPSTREAM.md`](experiments/UPSTREAM.md)），需要修改上游行为时用 `patches/` 管理。

**下游**：[`xf8410/uma-juece-ramen`](https://github.com/xf8410/uma-juece-ramen)（手机端，JNI 消费 `model.onnx`）。

## 文件

- [`PRINCIPLES.md`](PRINCIPLES.md) — 迭代准则 v1.1。先读这个，尤其 §0 铁律与 §0.5 上游关系。
- [`experiments/LEDGER.md`](experiments/LEDGER.md) — 实验账本（append-only）。
- [`experiments/UPSTREAM.md`](experiments/UPSTREAM.md) — 上游 pin 白名单（当前 43f532c）。
- `experiments/EXP-*/` — 各实验 plan/results。

## 当前状态（2026-09-01）

| 口径 | 均分 | 备注 |
|---|---:|---|
| 旧管线锚点（未绑 commit） | 65445 | 仅历史参考 |
| 旧管线 top6 集成 | 66949 | checkpoint 不可得，作目标参考 |
| **本仓锚点（EXP-001a）** | 待测 | pin 43f532c 手写 300 局 |
| 目标 | 70000 | 缺口 ~3050 |

## 迭代方向（准则 §6）

1. **特征/价值侧**（用户方向）：SpecialSelect 补采重训
2. **搜索侧**（Claude 方向）：NN leaf 截断估值接入拉面 MCTS（手机端算力释放）
3. **口径侧**（共同前提）：模拟器诚实性（因子校准/URA buffs/换皮 id，主仓 v0.4.2 已修大半）

## CI

- **smoke**（每次 push）：编译（default+onnx）+ pytest + CLI 入口冒烟。已实测绿。
- **upstream-suite**（schedule/dispatch，informational）：上游全套测试，不拦门禁（其逐位断言绑上游本地 gamedata）。
- **experiment**（dispatch，6h 上限）：教师采集 → 导出 → 标签 → 训练 → ONNX 导出，产物只留 onnx+元数据。
- 免费档 4 vCPU 无 GPU——本模型量级 CPU 足够，瓶颈在采集与基准，靠分片+断点续训覆盖。

## 跑实验

```bash
# 1. 合 PR 后 dispatch：
gh workflow run lab.yml -f experiment=EXP-001a
# 2. 结果回 LEDGER（append-only）
```
