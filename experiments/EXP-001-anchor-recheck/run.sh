#!/usr/bin/env bash
# EXP-001a：本仓手写基线锚点（experiments/EXP-001-anchor-recheck/plan.md）
# pin 43f532c | 手写策略 | 7 马娘 × 525 计划 × 1 局 = 525 局（CI 首测口径）
#
# 运行环境（由 lab.yml experiment job 提供）：
#   - CWD = 上游 checkout 根（43f532c）
#   - gamedata/ 已下载（必需，失败即退出）
#   - ./target/release/ramen_space_bench 已由 needs: smoke 之前的 job 构建？
#     否——experiment job 独立 runner，必须自己构建（cargo cache 命中后 ~2min）
#   - experiment_output/ 为产物目录（lab.yml 上传）
set -euo pipefail

echo "=== EXP-001a 环境记录（准则 §2 manifest）==="
{
  echo "upstream_commit: $(git rev-parse HEAD)"
  echo "gamedata_signature: $(cat gamedata/*.json gamedata/*.toml 2>/dev/null | sha256sum | cut -c1-16)"
  echo "seed: 61444 (bin 默认，每计划 +i*1000003)"
  echo "strategy: handwritten (RecommendedRamenTrainer)"
  echo "special_mode: n/a (handwritten 不消费)"
  echo "runs_per_plan: 1 (CI 首测；正式锚点如需更窄 CI 再分片加到 4)"
  echo "date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
} | tee experiment_manifest.txt

mkdir -p experiment_output

echo "=== 构建 ramen_space_bench ==="
cargo build --release -p umasim --bin ramen_space_bench

echo "=== 跑基准（7 马娘 × 525 计划 × 1 局）==="
# 分辨力预检（准则 §1.3）：先用 --plans 8 冒烟确认链路活，再全量
./target/release/ramen_space_bench --trainer handwritten --runs-per-plan 1 --plans 8 \
  | tee experiment_output/smoke8.txt

./target/release/ramen_space_bench \
  --trainer handwritten \
  --runs-per-plan 1 \
  --seed 61444 \
  --csv experiment_output/exp001a_per_game.csv \
  2>&1 | tee experiment_output/exp001a_stdout.txt

cp experiment_manifest.txt experiment_output/
echo "=== EXP-001a 完成 ==="
tail -20 experiment_output/exp001a_stdout.txt
