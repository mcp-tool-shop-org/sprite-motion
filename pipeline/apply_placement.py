"""sprite-motion BRIDGE — apply editor placement(s) to rigged character GLB(s).
Each weapon is dropped at its exact attachPoint (+ in-plane rotation + scale), with a non-deform
weapon_grip bone (child of the named bone) so it rides the hand. No coordinate guessing.

SINGLE character ("Export JSON" from the editor):
  blender -b --python apply_placement.py -- --char <rigged>.glb --placement <placement>.json \
      --weapons halberd=<halberd>.glb [--out <out>.glb]

WHOLE ROSTER ("Export all placements"):
  blender -b --python apply_placement.py -- --placement <placements>.json \
      --manifest <manifest>.json --outdir <dir>
    placements = { "format":"sprite-motion.placements", "characters":[ <block>, ... ] }
    manifest   = { "characters": { "<skeleton name>": "<rigged glb>", ... },
                   "weapons":    { "<asset>": "<weapon glb>", ... } }
  --weapons asset=glb,... augments/overrides the manifest's weapon map.
"""
import bpy, sys, os, json, math, mathutils, numpy as np
argv = sys.argv[sys.argv.index("--")+1:]
def arg(n, d=None): return argv[argv.index(n)+1] if n in argv else d
PLACE = arg("--placement"); CHAR = arg("--char"); OUT = arg("--out")
MANIFEST = arg("--manifest"); OUTDIR = arg("--outdir")
ASSETS_CLI = dict(kv.split("=", 1) for kv in arg("--weapons", "").split(",") if "=" in kv)
V = mathutils.Vector
P = json.load(open(PLACE, encoding="utf-8"))

def co(o): return np.array([(v.co.x, v.co.y, v.co.z) for v in o.data.vertices])

def place(w, arm, figureH, assets):
    asset = w["asset"]; path = assets.get(asset); bone = w["bone"]
    if not path or not os.path.exists(path): print(f"[skip] no GLB for '{asset}'", flush=True); return
    if bone not in arm.data.bones: print(f"[skip] bone '{bone}' absent", flush=True); return
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.context.scene.objects if o not in before]
    hm = [o for o in new if o.type == "MESH"]
    bpy.ops.object.select_all(action='DESELECT')
    for o in hm: o.select_set(True)
    bpy.context.view_layer.objects.active = hm[0]
    if len(hm) > 1: bpy.ops.object.join()
    hal = bpy.context.view_layer.objects.active; hal.name = "wpn_" + asset
    for o in new:
        if o.type == "EMPTY":
            try: bpy.data.objects.remove(o, do_unlink=True)
            except Exception: pass
    bpy.ops.object.select_all(action='DESELECT'); hal.select_set(True); bpy.context.view_layer.objects.active = hal
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    c = co(hal); ext = c.max(0) - c.min(0); la = int(np.argmax(ext))     # longest axis -> Z
    if la != 2:
        hal.rotation_euler = (0, math.radians(90), 0) if la == 0 else (math.radians(90), 0, 0)
        bpy.ops.object.transform_apply(rotation=True); c = co(hal)
    zmin, zmax = c[:, 2].min(), c[:, 2].max(); zr = zmax - zmin          # head (wider end) -> +Z
    top = c[c[:, 2] > zmin + 0.78*zr]; bot = c[c[:, 2] < zmin + 0.22*zr]
    tw = (top[:, 0].max() - top[:, 0].min()) if len(top) > 3 else 0
    bw = (bot[:, 0].max() - bot[:, 0].min()) if len(bot) > 3 else 0
    if bw > tw: hal.rotation_euler = (math.radians(180), 0, 0); bpy.ops.object.transform_apply(rotation=True); c = co(hal)
    zmin, zmax = c[:, 2].min(), c[:, 2].max(); haft = c[c[:, 2] < zmin + 0.4*(zmax - zmin)]
    cx, cy = haft[:, 0].mean(), haft[:, 1].mean()                         # recenter haft -> x=y=0, butt -> z=0
    for v in hal.data.vertices: v.co.x -= cx; v.co.y -= cy; v.co.z -= zmin
    c = co(hal); Hn = c[:, 2].max() - c[:, 2].min(); s = (w.get("scale", 1.0)*figureH)/max(1e-6, Hn)
    for v in hal.data.vertices: v.co *= s                                # uniform scale -> scale*figureH
    gf = 1.0 - w.get("gripAnchor", [0.5, 0.5])[1]
    c = co(hal); Hn = c[:, 2].max() - c[:, 2].min(); gz = c[:, 2].min() + gf*Hn
    for v in hal.data.vertices: v.co.z -= gz                             # grip -> origin
    hal.data.update()
    ap = w["attachPoint"]
    hal.rotation_euler = (0, math.radians(w.get("rotationDeg", 0)), 0)   # in-plane (about depth axis)
    hal.location = V((ap[0], ap[1], ap[2]))
    bpy.context.view_layer.update()
    # weapon_grip (HEAD at the grip) -> weapon_tip (HEAD at the business end). glTF stores joint HEADS,
    # not tails, so the meaningful positions go in the heads (KB rigging: the tip joint feeds hit-box / tip-velocity).
    Minv = arm.matrix_world.inverted(); apw = V((ap[0], ap[1], ap[2]))
    MW = mathutils.Matrix.Translation(apw) @ mathutils.Euler((0, math.radians(w.get("rotationDeg", 0)), 0), 'XYZ').to_matrix().to_4x4()
    tipw = max((MW @ v.co for v in hal.data.vertices), key=lambda p: (p - apw).length)  # weapon's far end = business tip
    grip_local = Minv @ apw; tip_local = Minv @ tipw   # TODO: refine via the editor's tipAnchor when v3 ships
    d = tip_local - grip_local; L = d.length; d = d / L if L > 1e-5 else V((0, 0, 1))
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones; hb = eb[bone]; gn = "weapon_grip_" + asset; tn = "weapon_tip_" + asset
    g = eb.new(gn); g.head = grip_local; g.tail = grip_local + d * max(0.08, L * 0.3); g.parent = hb; g.use_deform = False; g.use_connect = False
    t = eb.new(tn); t.head = tip_local; t.tail = tip_local + d * 0.05; t.parent = g; t.use_deform = False; t.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT'); hal.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    arm.data.bones.active = arm.data.bones[gn]
    bpy.ops.object.parent_set(type='BONE', keep_transform=True)
    print(f"[placed] {asset} -> {bone}  at {ap}  rot={w.get('rotationDeg',0)} scale={w.get('scale',1.0)}", flush=True)

def rig_character(char_glb, block, assets, out):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=char_glb)
    arm = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]
    cm = [m for m in bpy.context.scene.objects if m.type == "MESH"]
    if len(cm) > 1:                                                       # drop UniRig's stray bounding sphere
        keep = max(cm, key=lambda m: len(m.data.vertices))
        for o in cm:
            if o is not keep: bpy.data.objects.remove(o, do_unlink=True)
    charmesh = max([m for m in bpy.context.scene.objects if m.type == "MESH"], key=lambda m: len(m.data.vertices))
    zs = [(charmesh.matrix_world @ v.co).z for v in charmesh.data.vertices]; figureH = max(zs) - min(zs)
    print(f"[char] {os.path.basename(char_glb)}  figureH={figureH:.3f}  weapons={len(block.get('weapons', []))}", flush=True)
    for w in block.get("weapons", []): place(w, arm, figureH, assets)
    for o in [m for m in list(bpy.context.scene.objects) if m.type == "MESH" and len(m.data.vertices) < 300]:
        bb = [o.matrix_world @ V(c) for c in o.bound_box]
        if max(max(p[i] for p in bb) - min(p[i] for p in bb) for i in range(3)) > 1.4: bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True)
    print(f"[export] {out} ({os.path.getsize(out)//1024} KB)", flush=True)

man = json.load(open(MANIFEST, encoding="utf-8")) if MANIFEST else {}
assets = dict(man.get("weapons", {})); assets.update(ASSETS_CLI)
man_chars = man.get("characters", {})

if P.get("format") == "sprite-motion.placements" or "characters" in P:    # whole roster
    outdir = OUTDIR or "."; os.makedirs(outdir, exist_ok=True)
    chars = P.get("characters", [])
    print(f"[bridge] roster: {len(chars)} character(s)", flush=True)
    for block in chars:
        name = block.get("skeleton"); glb = man_chars.get(name)
        if not glb or not os.path.exists(glb):
            print(f"[skip] no rigged GLB mapped for '{name}'", flush=True); continue
        rig_character(glb, block, assets, os.path.join(outdir, f"{name}_placed.glb"))
else:                                                                     # single character
    if not CHAR: print("[error] single placement needs --char <rigged>.glb", flush=True); sys.exit(1)
    rig_character(CHAR, P, assets, OUT or os.path.splitext(CHAR)[0] + "_placed.glb")
print("BRIDGE DONE", flush=True)
