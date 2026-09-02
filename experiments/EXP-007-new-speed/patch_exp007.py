#!/usr/bin/env python3
"""EXP-007 新速度卡对比 patch v2（在 d27a6eb 上重放）

v1 失败教训：「乐透心」在 cardDB 命中 2 条（同名不同突破/不同卡面），v1 断言唯一过严。
v2 策略：
- 按名收集全部候选，过滤条件收紧为「SSR(rarity=3) 且 cardType=0 速 且 cardValue≥5 级」；
  过滤后仍多张则取 cardId 最大（=最新卡面）并打印全部候选留痕——这是确定性规则，
  不允许静默猜。
- 其余同 v1：扩池 6→8、CSV build 列=uma|shape|deck、写 manifest。
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
    hits = []
    for obj, name in walk(raw):
        if kw in name:
            cid = obj.get("cardId") or obj.get("card_id")
            ctype = obj.get("cardType") or obj.get("card_type")
            rar = obj.get("rarity")
            cv = obj.get("cardValue") or obj.get("card_value") or []
            if cid and ctype == 0 and rar == 3 and len(cv) >= 5:
                hits.append((int(cid), name))
    assert hits, f"cardDB 中没有满足「SSR满破速卡」的「{kw}」——卡名或数据口径需人工核对"
    hits = sorted(set(hits))  # 去重（walk 可能重复触达同一 dict）
    if len(hits) > 1:
        print(f"  「{kw}」多候选（取 cardId 最大=最新）: {hits}")
    cid, name = hits[-1]
    print(f"选定「{kw}」: id={cid} name={name}")
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
assert s.count(anchor) == 1, "sampler.rs GEN1_CARD_POOL 尾锚点不唯一"
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

# --- manifest ---
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
print("patch v2 完成: 速卡池 6→8；CSV build 列 = uma|shape|deck；manifest 已写")
