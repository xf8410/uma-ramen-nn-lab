#!/usr/bin/env bash
# EXP-005：正式重采分片（search_n=64）——80 分片 × 1000 条，index [0,80000)
# 用法: run.sh <shard_id> ；其余配方与 EXP-002 一致，唯一变量 = search_n 与数量
# ★ --count 是累计长度：区间 = [--start, --start + --count)（INCIDENT-20260902 教训）
set -euo pipefail

SHARD="${1:?用法: run.sh <shard_id>}"
SN=64
CHUNK=1000
START=$((SHARD * CHUNK))
DATA="experiment_output/shard_${SHARD}"

mkdir -p "$DATA" experiment_output

{
  echo "arm: EXP-005 sn=${SN}  shard: ${SHARD}/80"
  echo "index_range: [${START}, $((START + CHUNK)))"
  echo "upstream_commit: $(git rev-parse HEAD)"
  echo "gamedata_signature: $(cat gamedata/*.json gamedata/*.toml 2>/dev/null | sha256sum | cut -c1-16)"
  echo "search_n: ${SN}  shard_size: 256  radical_factor_max: 1.4  quota_permille: 20,30"
  echo "date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
} | tee "experiment_output/env_shard_${SHARD}.txt"

cargo build --release -p umasim --bin ramen_teacher_collect

echo "=== 单条冒烟 ==="
./target/release/ramen_teacher_collect \
  --count 1 --start "$START" --search-n "$SN" \
  --output-dir "$DATA" --shard-size 256 2>&1 | tail -6

echo "=== 本分片全量 [${START}, $((START + CHUNK))) sn=${SN} ==="
./target/release/ramen_teacher_collect \
  --count "$CHUNK" --start "$START" --search-n "$SN" \
  --output-dir "$DATA" --shard-size 256 2>&1 | tail -20

cp "$DATA/manifest.json" "experiment_output/manifest_shard_${SHARD}.json"
echo "=== shard ${SHARD} 完成 ==="
