# EXP-001a：本仓手写基线锚点（EXP-001 修订版）

> 修订原因：旧管线 checkpoint 不可得（用户 2026-09-01），集成复现取消。
> 上游引用改为 SHA pin（UPSTREAM.md：43f532c）。本实验产出**本仓自己的锚点**。

## 假设
在 pin SHA 43f532c、xulai1001/umaai-rs master gamedata、固定种子表下，
`ramen_space_bench` 手写策略（`RecommendedRamenTrainer`）可测得稳定均分，
作为本仓全部后续实验的对照锚点。

旧锚点 65445（未绑 commit）不参与裁决——按准则 §0.2，跨 commit 数字不可比；
只记录偏差幅度供账本参考。

## 方法
1. CI experiment job（pin 43f532c）跑 `ramen_space_bench`：
   - 手写策略（`--trainer handwritten` 或 plan 回填后的精确参数，
     以 smoke artifact `cli_args.txt` 为准）
   - 局数 N≥300，采样空间与教师采集同构（准则 §0.3）
   - 种子区间记录进 manifest（准则 §2）
2. 输出：均分、标准差、标准误、自选比赛达标率、按 (马娘, 卡组) 分组表。
3. 体量预估（准则 §1.2）：CSV 输出 <10MB，无 --raw，单 job 可承受。

## 验收标准
- [ ] 300 局全部跑完，0 局育成失败静默丢失（失败率另计并列出）
- [ ] manifest 含 SHA + gamedata 签名 + 种子区间（准则 §2，缺一作废）
- [ ] 结果写 results.md + LEDGER 新条目 → 成为正式锚点 ANCHOR-003
- [ ] 与 65445 的偏差 > 2000 分时，在 results.md 里给出口径漂移分析
      （模拟器数值变更清单：8/23-8/27 五次 + 8/31 SpecialSelect 还原）

## 依赖
- smoke job 绿（✅ 37529450 已实测）
- PR #1 合入 main（experiment job 只在 dispatch 时跑，但 workflow 必须先在 main）
- cli_args.txt artifact 回填精确 CLI（本 plan 预留）

## 状态
- [x] plan 写就（先写后跑，准则 §3）
- [ ] cli_args 回填
- [ ] CI run 链接：待填
- [ ] results.md：待跑后创建
