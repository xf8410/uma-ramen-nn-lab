#!/usr/bin/env python3
"""EXP-007 新速度卡对比 patch（在 d27a6eb 上重放）

设计（用户 2026-09-02 指令）：
- 上游数据更新 260901 新增速度 SSR「乐透心」「千名代表」→ 对比而非直接替换：
  把 gen1 速卡池 6 张扩到 8 张（+两张新卡），全空间重枚举，逐卡算边际效应，
  谁的分高谁留下；同时对比评分/五维/PT。
- CSV build 列写 `uma|shape|deck6`，summary 按卡归因（在/不在卡组）。

步骤：
1. 从 gamedata/cardDB.json 按名找两张新卡（要求 SSR 满破、cardType=0 速），
   找不到或匹配不唯一则报错退出——不允许静默猜 ID
2. sampler.rs GEN1_CARD_POOL 追加两张（idrank = card_id*10+4，与池内满破约定一致）
3. ramen_space_bench.rs 的 outcome_to_row build 实参改为 `uma|shape|deck`（一行改动，
   不动 bench.rs 本体，RESULTS_HEADER 31 列不变）
4. 写 experiment_output/card_manifest.json（8 张速卡 idrank+名）供 summary 使用

预期空间：无冲突马娘 5 × (C(8,3)×2 + C(8,2) + C(8,2)×2) = 5×196 = 980；
冲突马娘 2（东海帝王/杏目 各缩一张速卡）× 133 = 266；合计 1246 计划 × 8 局 = 9968 局。
"""
import json
from pathlib import Path

ROOT = Path.cwd()
assert (ROOT / "gamedata" / "cardDB.json").exists(), f"cwd 应为上游仓库根: {ROOT}"

raw = json.loads((ROOT / "gamedata" / "cardDB.json").read_text())

def walk(o):
    if isinstance(o, dict):
        name = o.get("cardName") or o.get("name") or ""
        if isinstance(name, str) and name:
            yield o, name
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)

def pick(kw):
    hits = [obj for obj, name in walk(raw) if kw in name]
    assert hits, f"cardDB 中找不到「{kw}」——260901 数据里没有这张卡？"
    if len(hits) > 1:
        for h in hits:
            print("   候选:", h.get("cardId"), h.get("cardName") or h.get("name"))
        raise AssertionError(f"「{kw}」匹配不唯一（{len(hits)} 条）")
    c = hits[0]
    cid = int(c.get("cardId") or c.get("card_id"))
    ctype = c.get("cardType") or c.get("card_type")
    rar = c.get("rarity")
    cv = c.get("cardValue") or c.get("card_value") or []
    name = str(c.get("cardName") or c.get("name"))
    print(f"找到「{kw}」: id={cid} name={name} cardType={ctype} rarity={rar} cardValue级数={len(cv)}")
    assert ctype == 0, f"「{kw}」不是速卡 (cardType={ctype})——若实为其他类型，改设计而非硬跑"
    assert rar == 3 and len(cv) >= 5, f"「{kw}」不是满破可用 SSR (rarity={rar}, cardValue={len(cv)})"
    return cid, name

lot_id, lot_name = pick("乐透心")
sen_id, sen_name = pick("千名代表")
assert lot_id != sen_id, "两张卡解析成同一 ID"

# --- patch 1: sampler.rs 速卡池 6→8 ---
sp = ROOT / "crates" / "umasim" / "src" / "sampler.rs"
s = sp.read_text()
anchor = '''        alias: "[一杯怀旧之味]骏川手纲"
    }
];'''
assert s.count(anchor) == 1, "sampler.rs GEN1_CARD_POOL 尾锚点不唯一（d27a6eb 上应恰好 1 次）"
ins = f'''        alias: "[一杯怀旧之味]骏川手纲"
    }},
    CardEntry {{
        idrank: {lot_id}4,
        alias: "[patch]{lot_name}"
    }},
    CardEntry {{
        idrank: {sen_id}4,
        alias: "[patch]{sen_name}"
    }}
];'''
sp.write_text(s.replace(anchor, ins))

# --- patch 2: bench bin 的 CSV build 列 = uma|shape|deck ---
bp = ROOT / "crates" / "umasim" / "tools" / "data_collection" / "ramen_space_bench.rs"
b = bp.read_text()
banchor = "rows.push(bench::outcome_to_row(plan.shape, o));"
assert b.count(banchor) == 1, "ramen_space_bench.rs build 实参锚点不唯一"
brepl = (
    'rows.push(bench::outcome_to_row(&format!("{}|{}|{}", plan.uma, plan.shape, '
    'plan.deck.iter().map(|x| x.to_string()).collect::<Vec<_>>().join("-")), o));'
)
bp.write_text(b.replace(banchor, brepl))

# --- manifest 供 summary 归因 ---
known = [
    (302754, "东海帝王SSR[天才的乌托邦]"),
    (302984, "跳舞城[刀光迸发Clash！]"),
    (302424, "杏目[改变世界的目光]"),
    (302824, "气槽[铭记于心，京之华]"),
    (303024, "里见光钻[永恒的誓言，永恒的光辉]"),
    (302924, "洛林军歌[响彻吧，两人的凯歌]")
]
manifest = {
    "new": [
        {"idrank": f"{lot_id}4", "name": lot_name},
        {"idrank": f"{sen_id}4", "name": sen_name}
    ],
    "known_speed": [{"idrank": str(i), "name": n} for i, n in known],
    "friend": "303054"
}
out = ROOT / "experiment_output"
out.mkdir(exist_ok=True)
(out / "card_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
print("patch 完成: 速卡池 6→8；CSV build 列 = uma|shape|deck；manifest 已写")
