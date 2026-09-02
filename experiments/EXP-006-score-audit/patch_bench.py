#!/usr/bin/env python3
"""EXP-006 评分审计补丁：给上游 bench 的 CSV 增加 skill_score / total_hints 两列。

用途：把 calc_score() 的全部输入暴露到 CSV，使报告侧能用公式独立重算评分
（"算两遍"），逐局断言与模拟器结算一致，排除任何重复计分/漏计。

补丁对象：upstream pin 43f532c 的 crates/umasim/src/bench.rs。
五处精确替换，每处断言恰好出现一次；任何失配立即失败（防 pin 漂移）。
（第 5 处：RESULTS_HEADER 数组声明长度 31→33，漏改会 E0308。）
"""
from pathlib import Path
import sys

TARGET = Path("crates/umasim/src/bench.rs")

REPLACEMENTS = [
    # 1) GameOutcome 增加两字段
    (
        """    /// 技能点。
    pub skill_pt: i32,
""",
        """    /// 技能点。
    pub skill_pt: i32,
    /// 已学技能评分（评分审计用：calc_score 的 skill 分量）。
    pub skill_score: i32,
    /// 总共打折级数（评分审计用：total_pt() 的 hint 项）。
    pub total_hints: i32,
""",
    ),
    # 2) run_seeded 构造处填充
    (
        """        skill_pt: game.uma.skill_pt,
""",
        """        skill_pt: game.uma.skill_pt,
        skill_score: game.uma.skill_score,
        total_hints: game.uma.total_hints,
""",
    ),
    # 3) CSV 表头扩列
    (
        """    "skill_pt",
""",
        """    "skill_pt",
    "skill_score",
    "total_hints",
""",
    ),
    # 4) outcome_to_row 落列
    (
        """        outcome.skill_pt.to_string(),
""",
        """        outcome.skill_pt.to_string(),
        outcome.skill_score.to_string(),
        outcome.total_hints.to_string(),
""",
    ),
    # 5) 数组声明长度同步（31 → 33；漏改 = E0308）
    (
        """pub const RESULTS_HEADER: [&str; 31] = [
""",
        """pub const RESULTS_HEADER: [&str; 33] = [
""",
    ),
]


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    for i, (old, new) in enumerate(REPLACEMENTS, 1):
        count = text.count(old)
        if count != 1:
            print(f"PATCH FAIL: 替换 #{i} 的锚点出现 {count} 次（应为 1）——pin 漂移或上游变更，拒绝打补丁")
            return 1
        text = text.replace(old, new)
    TARGET.write_text(text, encoding="utf-8")
    print("PATCH OK: bench.rs +skill_score +total_hints（结构体/构造/表头/落列/数组长度 共 5 处）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
