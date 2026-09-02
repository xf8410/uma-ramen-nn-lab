#!/usr/bin/env bash
# EXP-002：教师采集（矩阵分片版）——每 shard 领一段互斥 index 区间并行跑
# 用法: run.sh <shard_id> ；SHARD_COUNT/CHUNK 必须与 exp-002.yml 的 matrix 一致
# 依据: sample_position 按 index 确定性采样 → 分片并行 ≡ 顺序采集（plan.md §方法）
#
# ★ --count 是「累计长度」不是终点：区间 = [--start, --start + --count)
#   （INCIDENT-20260902：写成 START+CHUNK 导致 shard1-7 多采/越界）
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

echo "=== 单条冒烟（--count 1，区间 [START, START+1)）==="
./target/release/ramen_teacher_collect \
  --count 1 --start "$START" --search-n 8 \
  --output-dir "$DATA" --shard-size 256 2>&1 | tail -8

echo "=== 本分片全量 [${START}, $((START + CHUNK)))（同目录续跑，--count 仍从 START 起算的累计长度）==="
./target/release/ramen_teacher_collect \
  --count "$CHUNK" --start "$START" --search-n 8 \
  --output-dir "$DATA" --shard-size 256 2>&1 | tail -25

cp "$DATA/manifest.json" "experiment_output/manifest_shard_${SHARD}.json"
echo "=== shard ${SHARD} 完成 ==="
