#!/usr/bin/env python3
"""EXP-006e 补丁：power 抑制定价（EXP-006d 盘面诊断后续）。

诊断依据（EXP-006d @ d27a6eb）：
- P90−P10 属性差：speed+489 / wisdom+459 / guts+405 / stamina+331 / **power−204（唯一负）**
- 高分局力量反而更低 ⇒ 力量在被过度喂养（凹表尾巴 + 训练位冲突吃掉速/智/根回合）

机制：LocalRamenConfig 已有分年 dynamic_status_balance（gap/over），power 抑制 = 把
over/gap 按 per-attribute 覆盖。上游 dynamic_status_adjustment 用统一
status_overflow_strength / status_gap_strength，本补丁加 per-attr override 数组：
- `poN`  ：power 近上限衰减强度 = N/100（覆盖 years[2] 或全部——按 token 前缀）
- `p1/p2/p3N`：分年 power 近上限衰减 = N/100
- `q1/q2/q3N`：分年 power 短板追赶 = N/100（负值=允许 power 更落后，即进一步抑制）

实现选点（最少侵入）：dynamic_status_adjustment 内 multiplier 计算处，power 位
(i==2) 用 per-attr 字段替代统一字段。默认保持旧值 ⇒ base 逐位不变。

另加 bench --variant（同 006c 模式，HandwrittenVariant 已存在则直接复用）。
注意：本补丁依赖 EXP-006c 的 bench --variant 改造（exp-006c.yml 已并入链），
exp-006e.yml 先跑 006c patch 再跑 006d patch 再跑本补丁。
"""
from pathlib import Path
import sys

C = Path("crates/umasim/src/game/ramen/policy.rs")
L = Path("crates/umasim/src/trainer/local_ramen_trainer.rs")

REPLACEMENTS = [
    # 1) LocalRamenConfig 加 per-attr power 覆盖字段
    (
        L,
        """    /// 近上限衰减强度。属性完成度超过 70% 后按平方曲线增长，并受同类型卡过量系数放大。
    pub status_overflow_strength: f32,
""",
        """    /// 近上限衰减强度。属性完成度超过 70% 后按平方曲线增长，并受同类型卡过量系数放大。
    pub status_overflow_strength: f32,

    /// EXP-006e：power（i==2）专属近上限衰减强度覆盖。
    /// `f32::NAN` = 不覆盖（用统一 [`Self::status_overflow_strength`]）。
    /// 诊断依据：EXP-006d 盘面 P90−P10 power=−204 唯一负值 ⇒ 力量过度喂养。
    pub power_overflow_strength: f32,

    /// EXP-006e：power（i==2）专属短板追赶强度覆盖（可为负=允许更落后）。
    /// `f32::NAN` = 不覆盖（用统一 [`Self::status_gap_strength`]）。
    pub power_gap_strength: f32,
""",
    ),
    # 2) 默认值
    (
        L,
        """            dynamic_status_balance: false,
            status_gap_strength: 0.0,
            status_overflow_strength: 0.0,
""",
        """            dynamic_status_balance: false,
            status_gap_strength: 0.0,
            status_overflow_strength: 0.0,
            power_overflow_strength: f32::NAN,
            power_gap_strength: f32::NAN,
""",
    ),
    # 3) dynamic_status_adjustment 的 multiplier 计算加 per-attr 分支
    (
        L,
        """            let gap_bonus = self.config.status_gap_strength * (leading - completion[i]).max(0.0);
            let near_cap = ((completion[i] - 0.70) / 0.30).clamp(0.0, 1.0);
            let excess_cards = (g.card_type_count[i] - 2).max(0) as f32;
            let overflow = self.config.status_overflow_strength
                * near_cap
                * near_cap
                * (1.0 + 0.5 * excess_cards);
""",
        """            // EXP-006e：power 位用专属覆盖（NAN=回退统一值，base 逐位不变）
            let gap_strength = if i == 2 && !self.config.power_gap_strength.is_nan() {
                self.config.power_gap_strength
            } else {
                self.config.status_gap_strength
            };
            let overflow_strength = if i == 2 && !self.config.power_overflow_strength.is_nan() {
                self.config.power_overflow_strength
            } else {
                self.config.status_overflow_strength
            };
            let gap_bonus = gap_strength * (leading - completion[i]).max(0.0);
            let near_cap = ((completion[i] - 0.70) / 0.30).clamp(0.0, 1.0);
            let excess_cards = (g.card_type_count[i] - 2).max(0) as f32;
            let overflow = overflow_strength
                * near_cap
                * near_cap
                * (1.0 + 0.5 * excess_cards);
""",
    ),
    # 4) with_tokens 扩展 token（锚在 006d 的 g3/o3 分支后）
    (
        L,
        """            } else if let Some(v) = token.strip_prefix("o3") {
                let s: f32 = v.parse::<f32>()? / 100.0;
                trainer.years[2].config.status_overflow_strength = s;
""",
        """            } else if let Some(v) = token.strip_prefix("o3") {
                let s: f32 = v.parse::<f32>()? / 100.0;
                trainer.years[2].config.status_overflow_strength = s;
            } else if let Some(v) = token.strip_prefix("po") {
                // EXP-006e：power 近上限衰减，全部年统一覆盖（po150 → 1.50）
                let s: f32 = v.parse::<f32>()? / 100.0;
                for year in trainer.years.iter_mut() {
                    year.config.power_overflow_strength = s;
                }
            } else if let Some(v) = token.strip_prefix("p1o") {
                trainer.years[0].config.power_overflow_strength = v.parse::<f32>()? / 100.0;
            } else if let Some(v) = token.strip_prefix("p2o") {
                trainer.years[1].config.power_overflow_strength = v.parse::<f32>()? / 100.0;
            } else if let Some(v) = token.strip_prefix("p3o") {
                trainer.years[2].config.power_overflow_strength = v.parse::<f32>()? / 100.0;
            } else if let Some(v) = token.strip_prefix("pg") {
                // power 短板追赶覆盖：可为负（pg-50 → −0.50 = 允许 power 更落后）
                let s: f32 = v.parse::<f32>()? / 100.0;
                for year in trainer.years.iter_mut() {
                    year.config.power_gap_strength = s;
                }
""",
    ),
]

DOC_ANCHOR = """    /// - `o1N/o2N/o3N`：第 1/2/3 年近上限衰减强度 = N/100
    /// - `base`：无覆盖（对照）
"""
DOC_NEW = """    /// - `o1N/o2N/o3N`：第 1/2/3 年近上限衰减强度 = N/100
    /// - `poN`：power 近上限衰减统一覆盖 = N/100（EXP-006e）；`p1o/p2o/p3oN` 分年
    /// - `pgN`：power 短板追赶覆盖 = N/100，可为负（EXP-006e）
    /// - `base`：无覆盖（对照）
"""


def main() -> int:
    text = L.read_text(encoding="utf-8")
    count = text.count(DOC_ANCHOR)
    if count != 1:
        print(f"PATCH FAIL: 006d 文档锚点出现 {count} 次——请先应用 006c/006d 补丁")
        return 1
    text = text.replace(DOC_ANCHOR, DOC_NEW)
    L.write_text(text, encoding="utf-8")

    for i, (path, old, new) in enumerate(REPLACEMENTS, 1):
        text = path.read_text(encoding="utf-8")
        count = text.count(old)
        if count != 1:
            print(f"PATCH FAIL: 替换 #{i}（{path.name}）锚点出现 {count} 次（应为 1）")
            return 1
        path.write_text(text.replace(old, new), encoding="utf-8")
    print("PATCH OK: EXP-006e power 抑制定价（po/p1o/p2o/p3o/pg token + per-attr multiplier）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
