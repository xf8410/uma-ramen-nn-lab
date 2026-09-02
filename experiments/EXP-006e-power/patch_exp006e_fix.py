
from pathlib import Path
import sys

TARGET = Path("crates/umasim/src/trainer/local_ramen_trainer.rs")

# 追加在 006e 的 p3o 分支之后（v1 的 pg 锚点在 "po" 之后，被 strip_prefix("po") 抢先命中，
# "pg-30" 剥不掉 "po" 前缀导致 parse("") 报 cannot parse float from empty string）。
# v2 修正：pg 判定必须在 po 之前（strip_prefix 精确匹配 pgo 也不行——pgN 无 o 尾）。
P3O_ANCHOR = """            } else if let Some(v) = token.strip_prefix("p3o") {
                trainer.years[2].config.power_overflow_strength = v.parse::<f32>()? / 100.0;
"""
P3O_NEW = """            } else if let Some(v) = token.strip_prefix("p3o") {
                trainer.years[2].config.power_overflow_strength = v.parse::<f32>()? / 100.0;
            } else if let Some(v) = token.strip_prefix("pg") {
                // EXP-006e：power 短板追赶覆盖，可为负（pg-30 → −0.30）。
                // ⚠ 必须排在 "po" 分支**之前**：strip_prefix("po") 对 "pg-30" 返回 None
                // 本无害，但旧版把 pg 放在 po 之后时 token 顺序匹配语义没错——真正问题
                // 是 v1 的 pg 分支锚点错误地落在 po 分支内部注释之后导致从未生效，
                // "pg-30" 落进末尾 bail。v2 以独立锚点插入，顺序明确。
                let s: f32 = v.parse::<f32>()? / 100.0;
                for year in trainer.years.iter_mut() {
                    year.config.power_gap_strength = s;
                }
"""


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")

    # v1 的 pg 分支可能已存在（可重入）：先删除旧 pg 分支再插入修正版
    OLD_PG = """            } else if let Some(v) = token.strip_prefix("pg") {
                // power 短板追赶覆盖：可为负（pg-50 → −0.50 = 允许 power 更落后）
                let s: f32 = v.parse::<f32>()? / 100.0;
                for year in trainer.years.iter_mut() {
                    year.config.power_gap_strength = s;
                }
"""
    if OLD_PG in text:
        text = text.replace(OLD_PG, "")
        print("移除 v1 遗留 pg 分支")

    count = text.count(P3O_ANCHOR)
    if count != 1:
        print(f"PATCH FAIL: p3o 锚点出现 {count} 次（应为 1）——006e v1 patch 未应用或已漂移")
        return 1
    text = text.replace(P3O_ANCHOR, P3O_NEW)
    TARGET.write_text(text, encoding="utf-8")
    print("PATCH OK: pg 分支修正（独立锚点插在 p3o 后，可与 v1 重入）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
