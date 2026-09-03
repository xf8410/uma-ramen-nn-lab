#!/usr/bin/env bash
# EXP-009：蒸馏 v3 采数分片（search_n=64）——80 分片 × CHUNK=2000，index [0,160000)
# 与 EXP-008 同教师（冠军配方）；唯一区别 = CHUNK 2000（index 前半 [0,80000) 与 008 完全重合，后半为新增）
# ★ --count 是累计长度：区间 = [--start, --start + --count)（INCIDENT-20260902 教训）
set -euo pipefail

SHARD="${1:?用法: run.sh <shard_id> [CHUNK]}"
SN=64
CHUNK="${2:-2000}"
START=$((SHARD * CHUNK))
DATA="experiment_output/shard_${SHARD}"

mkdir -p "$DATA" experiment_output

{
  echo "arm: EXP-009 sn=${SN}  shard: ${SHARD}/80  chunk: ${CHUNK}"
  echo "index_range: [${START}, $((START + CHUNK)))"
  echo "teacher: with_tokens(g2420-o2150-o3150-g3160-cook60)（与 EXP-008 同）"
  echo "upstream_commit: $(git rev-parse HEAD)"
  echo "gamedata_signature: $(cat gamedata/*.json gamedata/*.toml 2>/dev/null | sha256sum | cut -c1-16)"
  echo "search_n: ${SN}  shard_size: 256  radical_factor_max: 1.4  quota_permille: 20,30"
  echo "date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
} | tee "experiment_output/env_shard_${SHARD}.txt"

cargo build --release -p umasim --bin ramen_teacher_collect

echo "=== 单条冒烟（index=${START}） ==="
./target/release/ramen_teacher_collect \
  --count 1 --start "$START" --search-n "$SN" \
  --output-dir "$DATA" --shard-size 256 2>&1 | tail -6

echo "=== 本分片全量 [${START}, $((START + CHUNK))) sn=${SN} ==="
./target/release/ramen_teacher_collect \
  --count "$CHUNK" --start "$START" --search-n "$SN" \
  --output-dir "$DATA" --shard-size 256 2>&1 | tail -20

cp "$DATA/manifest.json" "experiment_output/manifest_shard_${SHARD}.json"
echo "=== shard ${SHARD} 完成 ==="
