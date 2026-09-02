#!/usr/bin/env python3
"""EXP-006d 补丁：with_tokens 扩展 6 组新旋钮（RMJ 档位前瞻 / 材料预留 / 分年动态属性平衡）。

仅在 EXP-006c 已打补丁的 with_tokens 上扩展（2 处精确替换，均为本仓 006c 插入的代码）：
- `ckN`    ：剧本 PT 档位前瞻倍率 = N/100（LocalRamenConfig::checkpoint_scale，preset 现值 0=关闭）
- `cookN`  ：诀窍边际库存权重 = N（LocalRamenConfig::cook2_stock_weight，preset 40；调高=材料更保守）
- `g1/g2/g3N`：第 1/2/3 年短板追赶强度 = N/100（分年动态属性平衡）
- `o1/o2/o3N`：第 1/2/3 年近上限衰减强度 = N/100

全部默认保真：不带 token 时行为与 65438.2 基线逐位一致。
"""
from pathlib import Path
import sys

TARGET = Path("crates/umasim/src/trainer/local_ramen_trainer.rs")

DOC_ANCHOR = """    /// - `wisfN`：智力训练体力豁免下限 = N（见 [`RamenPolicyConfig::wisdom_vital_floor`]）
    /// - `capdN`：副属性残余收益折扣 = N/100（[`RamenPolicyConfig::cap_discount_weight`]）
    /// - `base`：无覆盖（对照）
"""
DOC_NEW = """    /// - `wisfN`：智力训练体力豁免下限 = N（见 [`RamenPolicyConfig::wisdom_vital_floor`]）
    /// - `capdN`：副属性残余收益折扣 = N/100（[`RamenPolicyConfig::cap_discount_weight`]）
    /// - `ckN`：剧本 PT 档位前瞻倍率 = N/100（[`LocalRamenConfig::checkpoint_scale`]；preset 现值 0=关闭）
    /// - `cookN`：诀窍边际库存权重 = N（[`LocalRamenConfig::cook2_stock_weight`]；调高=材料更保守）
    /// - `g1N/g2N/g3N`：第 1/2/3 年短板追赶强度 = N/100（分年动态属性平衡）
    /// - `o1N/o2N/o3N`：第 1/2/3 年近上限衰减强度 = N/100
    /// - `base`：无覆盖（对照）
"""

CHAIN_ANCHOR = """            } else {
                anyhow::bail!("未知 EXP-006c token: {token}（完整: {tokens}）");
            }
"""
CHAIN_NEW = """            } else if let Some(v) = token.strip_prefix("ck") {
                let scale: f32 = v.parse::<f32>()? / 100.0;
                for year in trainer.years.iter_mut() {
                    year.config.checkpoint_scale = scale;
                }
            } else if let Some(v) = token.strip_prefix("cook") {
                let w: f32 = v.parse()?;
                for year in trainer.years.iter_mut() {
                    year.config.cook2_stock_weight = w;
                }
            } else if let Some(v) = token.strip_prefix("g1") {
                let s: f32 = v.parse::<f32>()? / 100.0;
                trainer.years[0].config.status_gap_strength = s;
            } else if let Some(v) = token.strip_prefix("g2") {
                let s: f32 = v.parse::<f32>()? / 100.0;
                trainer.years[1].config.status_gap_strength = s;
            } else if let Some(v) = token.strip_prefix("g3") {
                let s: f32 = v.parse::<f32>()? / 100.0;
                trainer.years[2].config.status_gap_strength = s;
            } else if let Some(v) = token.strip_prefix("o1") {
                let s: f32 = v.parse::<f32>()? / 100.0;
                trainer.years[0].config.status_overflow_strength = s;
            } else if let Some(v) = token.strip_prefix("o2") {
                let s: f32 = v.parse::<f32>()? / 100.0;
                trainer.years[1].config.status_overflow_strength = s;
            } else if let Some(v) = token.strip_prefix("o3") {
                let s: f32 = v.parse::<f32>()? / 100.0;
                trainer.years[2].config.status_overflow_strength = s;
            } else {
                anyhow::bail!("未知 token: {token}（完整: {tokens}）");
            }
"""


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    for i, (old, new) in enumerate([(DOC_ANCHOR, DOC_NEW), (CHAIN_ANCHOR, CHAIN_NEW)], 1):
        count = text.count(old)
        if count != 1:
            print(f"PATCH FAIL: 替换 #{i} 锚点出现 {count} 次（应为 1）——请先应用 EXP-006c 补丁，拒绝打补丁")
            return 1
        text = text.replace(old, new)
    TARGET.write_text(text, encoding="utf-8")
    print("PATCH OK: with_tokens +ck/cook/g1g2g3/o1o2o3（6 组新旋钮）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
