#!/usr/bin/env python3
"""EXP-008 补丁：蒸馏 v2——教师 rollout 切到 006 定稿冠军配方。

背景（EXP-004b → EXP-006l 结论链）：
- gen2 NN（sn64 标签，教师=for_rollout() 默认 preset）闭环 Δ=−1139/−2224/−613，未超手写 65438.2
- 归因：剩余差距在标签配方与教师质量，非数据量/容量
- EXP-006c~l 把手写教师调到 65554.2（+116.1 t=5.91），换种子 70000 世界 4/4 泛化（+62.3 t=3.33）
- 蒸馏 v2 唯一变量：教师 rollout 配方 → 冠军 g2420-o2150-o3150-g3160-cook60

改点（1 处精确替换，恰好 1 次断言防 pin 漂移）：
- searchable.rs `impl FlatSearchGame for RamenGame::default_rollout_trainer()`
  `RecommendedRamenTrainer::for_rollout()` → `with_tokens("g2420-o2150-o3150-g3160-cook60")`
  for_rollout() 的 breakdown 关闭与 with_tokens 正交（后者只写 config 字段），
  断点续跑/manifest/前提均不受影响；采样器与采样空间零改动。

打完必须跑 smoke：token 不被 with_tokens 识别会直接 bail（EXP-006c 起的行为）。
"""
from pathlib import Path
import sys

TARGET = Path("crates/umasim/src/search/searchable.rs")

OLD = """    fn default_rollout_trainer() -> Self::RolloutTrainer {
        crate::trainer::RecommendedRamenTrainer::for_rollout()
    }"""

NEW = """    fn default_rollout_trainer() -> Self::RolloutTrainer {
        // EXP-008 蒸馏 v2：教师 rollout 切 006 定稿冠军配方（g2420-o2150-o3150-g3160-cook60）。
        // 依据：EXP-006l 换种子泛化 4/4（+62.3 t=3.33）、61444 世界 +116.1 t=5.91。
        // for_rollout() 的 breakdown 关闭与 with_tokens 正交（后者只写 config 字段）。
        // 未打 006c/006d/006e patch 链时 with_tokens 不识别 token 会直接报错——预期行为。
        crate::trainer::RecommendedRamenTrainer::with_tokens("g2420-o2150-o3150-g3160-cook60")
            .expect("EXP-008: 冠军 token 必须可解析（检查 006 patch 链是否已应用）")
    }"""


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    count = text.count(OLD)
    if count != 1:
        print(f"PATCH FAIL: 锚点出现 {count} 次（应为 1）——pin 漂移或上游变更，拒绝打补丁")
        return 1
    text = text.replace(OLD, NEW)
    TARGET.write_text(text, encoding="utf-8")
    print("PATCH OK: RamenGame::default_rollout_trainer → with_tokens(g2420-o2150-o3150-g3160-cook60)（EXP-008 蒸馏 v2 教师）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
