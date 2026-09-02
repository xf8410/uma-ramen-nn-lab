#!/usr/bin/env bash
# EXP-003b：search_n 剂量对照采集分片——同 index 区间、不同 search_n
# 用法: run.sh <shard_id> <search_n> ；CHUNK 与 exp-003b.yml 的矩阵定义一致
# ★ --count 是累计长度：区间 = [--start, --start + --count)（INCIDENT-20260902 教训）
set -euo pipefail

SHARD="${1:?用法: run.sh <shard_id> <search_n>}"
SN="${2:?缺少 search_n}"
CHUNK=375
START=$((SHARD * CHUNK))
DATA="experiment_output/sn${SN}_shard_${SHARD}"

mkdir -p "$DATA" experiment_output

{
  echo "arm: search_n=${SN}  shard: ${SHARD}/8"
  echo "index_range: [${START}, $((START + CHUNK)))"
  echo "upstream_commit: $(git rev-parse HEAD)"
  echo "gamedata_signature: $(cat gamedata/*.json gamedata/*.toml 2>/dev/null | sha256sum | cut -c1-16)"
  echo "search_n: ${SN}  shard_size: 256  radical_factor_max: 1.4  quota_permille: 20,30"
  echo "date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
} | tee "experiment_output/env_sn${SN}_shard_${SHARD}.txt"

cargo build --release -p umasim --bin ramen_teacher_collect

echo "=== 单条冒烟 ==="
./target/release/ramen_teacher_collect \
  --count 1 --start "$START" --search-n "$SN" \
  --output-dir "$DATA" --shard-size 256 2>&1 | tail -6

echo "=== 本分片全量 [${START}, $((START + CHUNK))) search_n=${SN} ==="
./target/release/ramen_teacher_collect \
  --count "$CHUNK" --start "$START" --search-n "$SN" \
  --output-dir "$DATA" --shard-size 256 2>&1 | tail -20

cp "$DATA/manifest.json" "experiment_output/manifest_sn${SN}_shard_${SHARD}.json"
echo "=== sn${SN} shard ${SHARD} 完成 ==="
