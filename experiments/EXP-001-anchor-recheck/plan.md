# EXP-001：锚点复现（口径复现，准则 §5 ⚠ 条款）

## 假设
旧管线锚点（手写 65445 / top6 集成 66949）在当前 commit
`muxueliunian/umaai-rs-muxue@feat/ramen-nn-schema` (43f532c) 上不可直接复现——
因为 changelog 8/23-8/27 五次「改变拉面模拟数值，基线作废」+ 8/31 SpecialSelect
还原全部发生在锚点截图数据采集之后或期间，且锚点未绑 commit。

## 方法
1. CI 跑 `ramen_space_bench`：手写基线（`RecommendedRamenTrainer`）N≥300 局，
   采样空间与教师数据同构（准则 §0.3）。
2. 若 EXP-001 开跑时有 top6 checkpoint 可用（待用户确认位置），加测 300 局
   配对（同局同种子，准则 §0.2）；没有则本实验只重测基线，集成复现顺延。
3. 配对 t 检验输出：均分、差值 ±95%CI、t、局数（准则 §0.4）。

## 验收标准
- 基线均分与 65445 偏差 ≤ CI 宽度 → 锚点保留，标注「复现通过」。
- 偏差超 CI → 锚点区整体标注「口径已漂移」，LEDGER 写 ANCHOR-003 以新基线重开，
  旧锚点只作历史参考。
- 无论结果，`upstream_commit.txt` 必须落盘并进 results.md。

## 状态
- [ ] plan 写就（本文件）
- [ ] CI run 链接：待填
- [ ] results.md：待跑后创建

## 备注
- 30GB 教训适用：本实验是全链路第一次正式跑，先 smoke job 绿了才准进 experiment job（准则 §1.1）。
- 手写基线数字本身没有「应当是多少」的神谕——它随模拟器数值变更漂移，
  这正是准则 §0.2 存在的原因。
