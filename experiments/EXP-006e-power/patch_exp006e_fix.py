
from pathlib import Path
import sys

TARGET = Path("crates/umasim/src/trainer/local_ramen_trainer.rs")

# 根因（run 33687932634 实锤）：with_tokens 以 '-' 分隔 token，"pg-30" 被拆成
# "pg" + "30" 两个 token → strip_prefix("pg") 得到空串 → parse("") 报
# "cannot parse float from empty string"。负值不能含 '-'，改用 'm' 前缀编码负号：
# pgm30 → −0.30，pg30 → +0.30。本脚本把 v1 的 pg 分支替换为 m 前缀解析版
#（可重入：先删旧分支再插）。

OLD_PG = """            } else if let Some(v) = token.strip_prefix("pg") {
                // power 短板追赶覆盖：可为负（pg-50 → −0.50 = 允许 power 更落后）
                let s: f32 = v.parse::<f32>()? / 100.0;
                for year in trainer.years.iter_mut() {
                    year.config.power_gap_strength = s;
                }
"""
NEW_PG = """            } else if let Some(v) = token.strip_prefix("pg") {
                // EXP-006e：power 短板追赶覆盖。负值用 'm' 前缀编码（'-' 是 token
                // 分隔符）：pgm30 → −0.30，pg30 → +0.30。
                let (sign, digits) = match v.strip_prefix('m') {
                    Some(d) => (-1.0f32, d),
                    None => (1.0f32, v)
                };
                let s: f32 = sign * digits.parse::<f32>()? / 100.0;
                for year in trainer.years.iter_mut() {
                    year.config.power_gap_strength = s;
                }
"""

DOC_OLD = """    /// - `pgN`：power 短板追赶覆盖 = N/100，可为负（EXP-006e）
"""
DOC_NEW = """    /// - `pg[m]N`：power 短板追赶覆盖 = ±N/100（m 前缀=负号，'-' 是 token 分隔符不能用；EXP-006e）
"""


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if OLD_PG not in text:
        print("PATCH FAIL: v1 pg 分支未找到——006e v1 patch 未应用？")
        return 1
    text = text.replace(OLD_PG, NEW_PG)
    if DOC_OLD in text:
        text = text.replace(DOC_OLD, DOC_NEW)
    TARGET.write_text(text, encoding="utf-8")
    print("PATCH OK: pg 负值改 'm' 前缀编码（pgm30=−0.30）；与 v1 重入安全")
    return 0


if __name__ == "__main__":
    sys.exit(main())
