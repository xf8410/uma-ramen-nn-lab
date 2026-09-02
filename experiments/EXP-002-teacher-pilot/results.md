# EXP-002 结果：教师数据采集完成（矩阵并行）

- **CI run**: [33585590880](https://github.com/xf8410/uma-ramen-nn-lab/actions/runs/33585590880) ✅（2026-09-02 03:03–03:07，全 9 job 绿）
- **产物**: `EXP-002-dataset` artifact（manifest.json + 56 个 part_*.bin + SUMMARY）

## 数字

| 项 | 值 |
|---|---|
| 计划采集 | 12000 条（8 shard × 1500，index 互斥区间） |
| 实际接受 | **11837 条**（每片 1471–1491） |
| 未捕获跳过 | 163 次（采样器部分局面无合法候选，预期行为） |
| 分片 part 文件 | 56 个（8×7） |
| **矩阵 wall-clock** | **3 分 12 秒**（含构建+合并） |
| 配方哈希 | 8 片一致；区间 [0,12000) 无缝无重叠；finished_at 齐 |

## 矩阵并行实测证据（用户裁定的做法）

| 运行 | 方式 | wall-clock |
|---|---|---|
| run 33580762360（8 shard，含错误区间） | 矩阵并行 | 采集 ~10 min（含冷构建） |
| run 33585590880（修正后） | **矩阵并行** | **3.2 min**（缓存热） |
| 单 job 顺序估算 12000 条 | 串行 | ~26 min（8×3.2）+ 无并行余量 |

## 两次失败复盘（都在胶水层，采集/校验本体零事故）

1. **INCIDENT-20260902**：`--count` 累计长度语义误当终点 → shard1-7 多采/越界 → assemble 区间断言拦截（闸门起效）→ run.sh 修复（PR #5）
2. **assemble FileNotFoundError**：manifest 复制件在 artifact 根、part 在子目录 → 改以 `part_000000.bin` 实际位置定位数据目录（PR #6）

## 下游消费

EXP-003 训练直接 `ramen_export_npy --input <dataset> --raw` 起步——上游导出 bin 只认 manifest+part 目录，本产物即为该格式，无需再加工。
