#!/usr/bin/env python3
"""EXP-006c 补丁：智力体力豁免（wisf）× 副属性折扣（capd）矩阵旋钮。

三处上游文件、8 处精确替换，每处断言恰好出现一次（防 pin 漂移）：
1. policy.rs   —— RamenPolicyConfig +wisdom_vital_floor（默认 i32::MAX=旧行为）+ 守门 2 豁免分支
2. local_ramen_trainer.rs —— RecommendedRamenTrainer::with_tokens（wisfN/capdN/base）
3. ramen_space_bench.rs —— --variant 参数（handwritten 变体入口）

默认值保证基线逐位不变（base 变体重跑必须 == 65438.2）。
"""
from pathlib import Path
import sys

REPLACEMENTS = [
    # ---- policy.rs ----
    (
        Path("crates/umasim/src/game/ramen/policy.rs"),
        # 1) 结构体加字段
        """    pub vital_rest_eating: i32,
    /// 心情低于此值强制外出（经验：<3 训练数值损失大）
""",
        """    pub vital_rest_eating: i32,
    /// 智力训练体力豁免下限（EXP-006c）：vital >= 此值时，智力训练不受
    /// [`vital_rest`](Self::vital_rest) 强制休息。智力是唯一体力增量为正（+5）
    /// 的训练位，且失败率体力阈值（~32）远低于其他位（~50-54）——低体力下
    /// 智力训练近乎零风险。`i32::MAX`（默认）= 不豁免，行为与旧版逐位一致。
    pub wisdom_vital_floor: i32,
    /// 心情低于此值强制外出（经验：<3 训练数值损失大）
""",
    ),
    (
        Path("crates/umasim/src/game/ramen/policy.rs"),
        # 2) 默认值
        """            vital_rest_eating: 0,
            motivation_outing: 3,
""",
        """            vital_rest_eating: 0,
            wisdom_vital_floor: i32::MAX,
            motivation_outing: 3,
""",
    ),
    (
        Path("crates/umasim/src/game/ramen/policy.rs"),
        # 3) 守门 2 豁免分支
        """            self.config.vital_rest
        };
        if uma.vital < rest_threshold {
""",
        """            self.config.vital_rest
        };
        // 智力体力豁免（EXP-006c）：智力是唯一体力增量为正（+5）的训练位，且失败率
        // 体力阈值（~32）远低于其他位（~50-54）——低体力下智力训练近乎零风险，
        // 无需为省体力放弃智力回合去休息/外出。仅 vital >= wisdom_vital_floor 时豁免
        // （默认 i32::MAX = 永不豁免，行为与旧版逐位一致）。
        let wisdom_exempt = uma.vital < rest_threshold
            && uma.vital >= self.config.wisdom_vital_floor
            && actions
                .iter()
                .any(|a| matches!(&a.operation, Operation::Train(t) if *t as usize == 4));
        if uma.vital < rest_threshold && !wisdom_exempt {
""",
    ),
    # ---- local_ramen_trainer.rs ----
    (
        Path("crates/umasim/src/trainer/local_ramen_trainer.rs"),
        # 4) with_tokens 构造器（插在 new() 文档前）
        """    /// 构造当前正式推荐 preset。
    pub fn new() -> Self {
""",
        """    /// EXP-006c：从 token 串构造 preset 变体（逐 token 覆盖三年同配置）。
    ///
    /// - `wisfN`：智力训练体力豁免下限 = N（见 [`RamenPolicyConfig::wisdom_vital_floor`]）
    /// - `capdN`：副属性残余收益折扣 = N/100（[`RamenPolicyConfig::cap_discount_weight`]）
    /// - `base`：无覆盖（对照）
    ///
    /// 未识别 token 直接报错，防止实验名拼错静默跑成 base。
    pub fn with_tokens(tokens: &str) -> Result<Self> {
        let mut trainer = Self::new();
        for token in tokens.split('-') {
            if token == "base" {
                continue;
            } else if let Some(v) = token.strip_prefix("wisf") {
                let floor: i32 = v.parse()?;
                for year in trainer.years.iter_mut() {
                    year.policy.config.wisdom_vital_floor = floor;
                }
            } else if let Some(v) = token.strip_prefix("capd") {
                let weight: f32 = v.parse::<f32>()? / 100.0;
                for year in trainer.years.iter_mut() {
                    year.policy.config.cap_discount_weight = weight;
                }
            } else {
                anyhow::bail!("未知 EXP-006c token: {token}（完整: {tokens}）");
            }
        }
        Ok(trainer)
    }

    /// 构造当前正式推荐 preset。
    pub fn new() -> Self {
""",
    ),
    # ---- ramen_space_bench.rs ----
    (
        Path("crates/umasim/tools/data_collection/ramen_space_bench.rs"),
        # 5) CLI 加 --variant
        """    /// 把逐局结果写成 CSV
    #[arg(long)]
    csv: Option<PathBuf>,

    /// 关闭网络策略的自选比赛硬守门（纯网络，仅供研究守门能否移除；不作为验收口径）
""",
        """    /// 把逐局结果写成 CSV
    #[arg(long)]
    csv: Option<PathBuf>,

    /// EXP-006c 手写变体 token 串（如 `wisf0-capd0`）；仅 trainer=handwritten 时生效
    #[arg(long)]
    variant: Option<String>,

    /// 关闭网络策略的自选比赛硬守门（纯网络，仅供研究守门能否移除；不作为验收口径）
""",
    ),
    (
        Path("crates/umasim/tools/data_collection/ramen_space_bench.rs"),
        # 6) 枚举加变体臂
        """    /// 手写规则
    Handwritten,
""",
        """    /// 手写规则
    Handwritten,
    /// 手写规则 EXP-006c token 变体（trainer 按 --variant 现场构造，无需 Clone）
    HandwrittenVariant,
""",
    ),
    (
        Path("crates/umasim/tools/data_collection/ramen_space_bench.rs"),
        # 7) select_trainer 分派
        """        "handwritten" => Ok(SelectedTrainer::Handwritten),
""",
        """        "handwritten" => Ok(if args.variant.as_deref().is_some_and(|v| v != "base") {
            SelectedTrainer::HandwrittenVariant
        } else {
            SelectedTrainer::Handwritten
        }),
""",
    ),
    (
        Path("crates/umasim/tools/data_collection/ramen_space_bench.rs"),
        # 8) run_plan 执行臂（逐局构造变体 trainer，构造只建配置结构，开销可忽略）
        """            SelectedTrainer::Handwritten => {
                let t = LoggingTrainer::new(RecommendedRamenTrainer::new(), base_seed + run_idx);
                bench::run_seeded(plan.uma, &plan.deck, &inherit, base_seed, run_idx, &t)?
            }
""",
        """            SelectedTrainer::Handwritten => {
                let t = LoggingTrainer::new(RecommendedRamenTrainer::new(), base_seed + run_idx);
                bench::run_seeded(plan.uma, &plan.deck, &inherit, base_seed, run_idx, &t)?
            }
            SelectedTrainer::HandwrittenVariant => {
                let tokens = args.variant.as_deref().unwrap_or("base");
                let t = LoggingTrainer::new(RecommendedRamenTrainer::with_tokens(tokens)?, base_seed + run_idx);
                bench::run_seeded(plan.uma, &plan.deck, &inherit, base_seed, run_idx, &t)?
            }
""",
    ),
]


def main() -> int:
    for i, (path, old, new) in enumerate(REPLACEMENTS, 1):
        text = path.read_text(encoding="utf-8")
        count = text.count(old)
        if count != 1:
            print(f"PATCH FAIL: 替换 #{i}（{path}）锚点出现 {count} 次（应为 1）——pin 漂移或上游变更，拒绝打补丁")
            return 1
        path.write_text(text.replace(old, new), encoding="utf-8")
    print("PATCH OK: policy.rs +wisdom_vital_floor(+守门豁免) / trainer +with_tokens / bench +--variant（共 8 处）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
