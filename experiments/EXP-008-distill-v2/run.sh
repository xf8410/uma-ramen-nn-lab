#!/usr/bin/env bash
# EXP-008：蒸馏 v2 教师重采分片（search_n=64）——80 分片 × CHUNK 条
# 唯一变量 vs EXP-005：教师 rollout 配方（patch_exp008.py 切冠军 token）
# 采样器/采样空间/search_n/分片口径与 EXP-005 完全一致（index 含义不变，可对齐）
# 用法: run.sh <shard_id> [CHUNK] [START_OFFSET]
# ★ --count 是累计长度：区间 = [--start, --start + --count)（INCIDENT-20260902 教训）
set -euo pipefail

SHARD="${1:?用法: run.sh <shard_id> [CHUNK] [START_OFFSET]}"
SN=64
CHUNK="${2:-1000}"
START=$((SHARD * CHUNK))
DATA="experiment_output/shard_${SHARD}"

mkdir -p "$DATA" experiment_output

{
  echo "arm: EXP-008 sn=${SN}  shard: ${SHARD}/80  chunk: ${CHUNK}"
  echo "index_range: [${START}, $((START + CHUNK)))"
  echo "teacher: with_tokens(g2420-o2150-o3150-g3160-cook60)（EXP-006l 定稿）"
  echo "upstream_commit: $(git rev-parse HEAD)"
  echo "gamedata_signature: $(cat gamedata/*.json gamedata/*.toml 2>/dev/null | sha256sum | cut -c1-16)"
  echo "search_n: ${SN}  shard_size: 256  radical_factor_max: 1.4  quota_permille: 20,30"
  echo "date: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
} | tee "experiment_output/env_shard_${SHARD}.txt"

echo "=== 教师配置自检（期望见到冠军 token 的 config 值） ==="
grep -n "with_tokens" crates/umasim/src/search/searchable.rs

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
