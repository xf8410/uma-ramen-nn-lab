#!/usr/bin/env python3
"""EXP-010 补丁：自蒸馏 v4——搜索引擎 rollout 评估器接入 009 冠军 NN。

背景（证据链）：
- EXP-009b：gen4 NN 3 种子 66085.5/66734.8/65595.5（均 66138.6），0831=66734.8 新全仓纪录
- 距 70000：最好种子差 3265，3 种子均值差 3861
- 数据量/训练时长的边际收益已兑现，下一量级=标签质量再上台阶
- 蒸馏增益链实证：教师 +116（008）→ 闭环最优种子 +347；教师端每 +1 分，NN 侧放大 ~3 倍

设计（上游既有能力接线，非新算法）：
- searchable.rs `RamenGame::default_rollout_trainer()` 的类型必须是编译期常量——
  无法按环境变量在"手写/NN"间切换（trait 关联类型限制）
- 改用 RamenNnTrainer 替代：它是 `Trainer<RamenGame>` 的完整实现（policy argmax +
  race_shield 硬守门 + choice 头委托手写），行为完全兼容 rollout 语义
- 模型路径硬编码为环境变量（CI 注入 artifact 解压路径）；变量缺失/模型加载失败
  直接 panic——teacher collect 管线**必须**在模型就位后才启动，静默回退手写
  会污染本轮全部标签

铁律（PRINCIPLES §0.4）：
- 本轮是唯一变量实验：教师评估器 手写冠军 → NN 66734.8
- regret 口径随教师变，Python 侧 regret 只记不裁决
- 最终裁决 = EXP-010b 闭环配对（t>2 且 Δ>0 才判超）
"""
from pathlib import Path
import sys

TARGET = Path("crates/umasim/src/search/searchable.rs")

OLD = """    /// rollout 专用实例：三份年的 breakdown 全部关闭
    fn default_rollout_trainer() -> Self::RolloutTrainer {
        crate::trainer::RecommendedRamenTrainer::for_rollout()
    }"""

NEW = """    /// rollout 专用实例：三份年的 breakdown 全部关闭
    ///
    /// EXP-010 自蒸馏 v4：接 NN 评估器（66734.8 冠军模型）。
    /// - `RAMEN_NN_MODEL` 环境变量指定 ONNX 路径；缺失/加载失败即 panic（禁静默回退）
    /// - fallback choice 头用 for_rollout() 手写（与 RamenNnTrainer::load 的内部 fallback 一致）
    /// - 环境变量缺失时显式报错退出，绝不退回手写教师——本轮唯一变量就是它
    fn default_rollout_trainer() -> Self::RolloutTrainer {
        let path = std::env::var("RAMEN_NN_MODEL")
            .expect("EXP-010: RAMEN_NN_MODEL 未设置——NN 教师模式必须显式提供模型路径");
        crate::trainer::RamenNnTrainer::load(std::path::Path::new(&path))
            .expect("EXP-010: RamenNnTrainer 加载失败（检查 ONNX + 旁路 JSON 是否齐全）")
    }"""


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    count = text.count(OLD)
    if count != 1:
        print(f"PATCH FAIL: 锚点出现 {count} 次（应为 1）——pin 漂移或上游变更，拒绝打补丁")
        return 1
    text = text.replace(OLD, NEW)
    TARGET.write_text(text, encoding="utf-8")
    print("PATCH OK: RamenGame::default_rollout_trainer → RamenNnTrainer::load($RAMEN_NN_MODEL)（EXP-010 自蒸馏 v4 教师）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
