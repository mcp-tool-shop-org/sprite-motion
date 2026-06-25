"""Build the roster manifest for apply_placement.py from folders of rigged character GLBs and
weapon GLBs — no Blender needed.

  character key = the GLB's filename stem (the name _export_skeleton.py emits, which the editor
                  uses as the skeleton name).
  weapon key    = the GLB's filename stem with build suffixes stripped (_trellis, _wpn, ...) so it
                  matches the editor's library prop names (a "halberd" prop ← halberd_trellis.glb).

Optionally --check a placements.json (single or "Export all placements") and warn about any character
or asset it references that the manifest doesn't cover — catch naming gaps before the batch run.

Run: python build_manifest.py --chars <dir> --weapons <dir> --out manifest.json
     [--char-glob "*_rigged.glb"] [--weapon-glob "*.glb"] [--strip _trellis,_wpn] [--check placements.json]
"""
import os, json, argparse, glob

ap = argparse.ArgumentParser()
ap.add_argument("--chars", required=True, help="folder of rigged character GLBs")
ap.add_argument("--weapons", required=True, help="folder of weapon GLBs")
ap.add_argument("--out", default="manifest.json")
ap.add_argument("--char-glob", default="*.glb", help="glob within --chars (use **/*.glb to recurse)")
ap.add_argument("--weapon-glob", default="*.glb", help="glob within --weapons")
ap.add_argument("--strip", default="_trellis,_wpn,_weapon,_mesh,_placed", help="suffixes stripped from weapon stems")
ap.add_argument("--check", default=None, help="a placements.json to validate coverage against")
args = ap.parse_args()

def find(d, pat): return sorted(glob.glob(os.path.join(d, pat), recursive=True))
def stem(p): return os.path.splitext(os.path.basename(p))[0]
strips = [s for s in args.strip.split(",") if s]
def asset_name(s):
    for suf in strips:
        if s.endswith(suf): return s[:-len(suf)]
    return s

chars, weapons, dups = {}, {}, []
for p in find(args.chars, args.char_glob):
    k = stem(p)
    if k in chars and os.path.abspath(chars[k]) != os.path.abspath(p): dups.append(("character", k, chars[k], p))
    chars[k] = p.replace("\\", "/")
for p in find(args.weapons, args.weapon_glob):
    k = asset_name(stem(p))
    if k in weapons and os.path.abspath(weapons[k]) != os.path.abspath(p): dups.append(("weapon", k, weapons[k], p))
    weapons[k] = p.replace("\\", "/")

json.dump({"characters": chars, "weapons": weapons}, open(args.out, "w", encoding="utf-8"), indent=2)
print(f"[manifest] {len(chars)} character(s), {len(weapons)} weapon(s) -> {args.out}")
for kind, k, a, b in dups: print(f"  WARN duplicate {kind} '{k}': {os.path.basename(a)} vs {os.path.basename(b)} (kept latter)")

if args.check:
    P = json.load(open(args.check, encoding="utf-8"))
    blocks = P.get("characters", [P]) if ("characters" in P or P.get("format") == "sprite-motion.placements") else [P]
    miss_c = {b.get("skeleton") for b in blocks if b.get("skeleton") and b.get("skeleton") not in chars}
    miss_w = {w.get("asset") for b in blocks for w in b.get("weapons", []) if w.get("asset") not in weapons}
    if miss_c or miss_w:
        print("  CHECK - uncovered references:")
        for n in sorted(miss_c): print(f"    character '{n}' has no rigged GLB in --chars")
        for a in sorted(miss_w): print(f"    weapon '{a}' has no GLB in --weapons")
    else:
        print(f"  CHECK - all {len(blocks)} character block(s) fully covered: OK")
