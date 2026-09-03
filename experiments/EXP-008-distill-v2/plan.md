# EXP-008 立项：蒸馏 v2——强教师重采重训

## 动机（证据链）

- EXP-004b：gen2 NN（sn64 标签，教师=for_rollout() 默认 preset 65438.2 档）闭环 Δ=−1139/−2224/−613，未超手写
- EXP-005 归因：数据量 6.6× 仅 −16 regret（边际已小），标签质量是主因（−203）；教师决策质量决定标签上限
- EXP-006c~l：手写教师 65438.2 → **65554.2**（+116.1 t=+5.91），换种子 70000 世界 4/4 泛化（+62.3 t=+3.33）→ 配方定稿
- **蒸馏 v2 唯一变量：教师 rollout 配方切冠军** → 标签更准 → NN 上限上移。目标：EXP-008b 闭环裁决 NN vs 手写两口径

## 唯一变量与不变量

| 项 | EXP-005（对照） | EXP-008（本轮） |
|---|---|---|
| 教师 rollout | `for_rollout()`（默认 preset=65438 档） | **`with_tokens("g2420-o2150-o3150-g3160-cook60")`（65554 档）** |
| search_n / 数量 / 分片 | 64 / 80000 / 80×1000 | 同（index 含义不变，与 005 可对齐） |
| 采样器（状态分布） | 默认（epsilon 等不动） | 同（不改——状态分布仍=默认策略世界） |
| 前提四条 | bin 硬编码 | 同（bin 内强制，manifest 记录） |
| 标签/训练配方 | labels.py + train.py 默认 | 同（d27a6eb 新参数 split/init/eval-columns **不启用**，默认=旧行为） |

## 口径警告（防自我欺骗）

- **regret 与 EXP-005 的 90.3 不可直接比**：rollout 价值口径随教师配方改变。Python 侧本轮只做健康性检查（早停正常、种子散布、ONNX 对拍），**裁决完全移交 EXP-008b 闭环配对**（t>2 且 Δ>0 才判超）
- 采样分布与 rollout 策略错位（状态=默认策略世界、评估=冠军策略）：v1 接受（与 005 同构）；采样器轨迹策略换冠军 = EXP-009 候选，另立项

## 改点（1 处）

`crates/umasim/src/search/searchable.rs` → `RamenGame::default_rollout_trainer()`:
`RecommendedRamenTrainer::for_rollout()` → `with_tokens("g2420-o2150-o3150-g3160-cook60").expect(...)`

- for_rollout() 的 breakdown 关闭与 with_tokens 正交（后者只写 config 字段），rollout 轻量性保留
- token 由 006c/d/e 补丁链的 with_tokens 解析（"g2420"→years[1].status_gap_strength=4.2 等），**必须全链后应用**
- 锚点恰好 1 次断言（patch_exp008.py）；打完自检 grep + 冒烟由 run.sh 第一步承担

## 工作流（exp-008.yml）

1. **smoke**：全 patch 链（006c→d→e→fix→008）→ CHUNK=20 采 20 条 → manifest 断言（search_n=64、index [0,20)、recipe_hash、git_commit=d27a6eb、gamedata_sig）
2. **collect**：80 分片矩阵 × CHUNK=1000（needs: smoke）→ EXP-008-shardN artifact
3. **assemble**：区间无缝 [i*1000,(i+1)*1000) + recipe_hash 80 片一致 + accepted 汇总
4. **convert**：`ramen_export_npy --raw`（d27a6eb 树内 gamedata，无下载步）+ labels.py
5. **train**：3 种子全量 + 12k 抽稀对照（数据量效应分离，保留与 005 同构的对照臂）
6. **summary**：regret 表（健康性）→ 闸门转 EXP-008b

## 闸门

- smoke 红 = 修 patch 再跑，绝不跳过 smoke 拉满
- collect 后 assemble 必须全绿才 convert
- Python regret 只记录不设通过线（口径已变）
- **最终裁决 = EXP-008b**：NN 3 种子 vs 手写默认（65438.2）与手写冠军（--variant champion，≈65554.2）同世界配对
