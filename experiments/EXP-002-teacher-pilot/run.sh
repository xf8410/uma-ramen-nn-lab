#!/usr/bin/env bash
# EXP-002：教师采集（矩阵分片版）——每 shard 领一段互斥 index 区间并行跑
# 用法: run.sh <shard_id> ；SHARD_COUNT/CHUNK 必须与 exp-002.yml 的 matrix 一致
# 依据: sample_position 按 index 确定性采样 → 分片并行 ≡ 顺序采集（plan.md §方法）
set -euo pipefail

SHARD="${1:?用法: run.sh <shard_id>}"
SHARD_COUNT=8
CHUNK=1500
START=$((SHARD * CHUNK))
DATA="experiment_output/shard_${SHARD}"

mkdir -p "$DATA" experiment_output

{
  echo "shard: ${SHARD}/${SHARD_COUNT}"
  echo "index_range: [${START}, $((START + CHUNK)))"
  echo "upstream_commit: $(git rev-parse HEAD)"
  echo "gamedata_signature: $(cat gamedata/*.json gamedata/*.toml 2>/dev/null | sha256sum | cut -c1-16)"
  echo "search_n: 8  shard_size: 256  radical_factor_max: 1.4  quota_permille: 20,30"
  echo "date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
} | tee "experiment_output/env_shard_${SHARD}.txt"

echo "=== 构建 ramen_teacher_collect ==="
cargo build --release -p umasim --bin ramen_teacher_collect

echo "=== 单条冒烟（count 累计语义，先落 1 条）==="
./target/release/ramen_teacher_collect \
  --count $((START + 1)) --start "$START" --search-n 8 \
  --output-dir "$DATA" --shard-size 256 2>&1 | tail -8

echo "=== 本分片全量 [${START}, $((START + CHUNK))) （同目录续跑拉满）==="
./target/release/ramen_teacher_collect \
  --count $((START + CHUNK)) --start "$START" --search-n 8 \
  --output-dir "$DATA" --shard-size 256 2>&1 | tail -25

cp "$DATA/manifest.json" "experiment_output/manifest_shard_${SHARD}.json"
echo "=== shard ${SHARD} 完成 ==="
