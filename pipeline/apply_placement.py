"""sprite-motion BRIDGE — apply an exported placement.json to a rigged character GLB.

Attaches weapon GLB(s) at the EXACT editor-placed attachPoint (+ rotation + scale) — no coordinate
guessing. Per weapon: import + join the weapon, canonicalize it (haft along +Z, head up, grip at the
origin derived from the editor's gripAnchor), uniform-scale to scale*figureHeight, rotate in-plane,
drop the grip onto attachPoint, add a NON-DEFORM weapon_grip bone (child of the named bone) and
bone-parent the weapon to it so it rides the hand. Exports the game-ready GLB.

Run: blender -b --python apply_placement.py -- --char <rigged>.glb --placement <p>.json \
     --weapons halberd=<halberd>.glb[,axe=<axe>.glb] [--out <out>.glb]
"""
import bpy, sys, os, json, math, mathutils, numpy as np
argv = sys.argv[sys.argv.index("--")+1:]
def arg(n, d=None): return argv[argv.index(n)+1] if n in argv else d
CHAR = arg("--char"); PLACE = arg("--placement")
OUT = arg("--out") or os.path.splitext(CHAR)[0] + "_placed.glb"
ASSETS = dict(kv.split("=", 1) for kv in arg("--weapons", "").split(",") if "=" in kv)
V = mathutils.Vector
P = json.load(open(PLACE, encoding="utf-8"))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=CHAR)
arm = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]
_cm = [m for m in bpy.context.scene.objects if m.type == "MESH"]
if len(_cm) > 1:                                  # drop UniRig's stray bounding sphere
    keep = max(_cm, key=lambda m: len(m.data.vertices))
    for o in _cm:
        if o is not keep: bpy.data.objects.remove(o, do_unlink=True)
charmesh = max([m for m in bpy.context.scene.objects if m.type == "MESH"], key=lambda m: len(m.data.vertices))
zs = [(charmesh.matrix_world @ v.co).z for v in charmesh.data.vertices]
figureH = max(zs) - min(zs)
print(f"[bridge] figureH={figureH:.3f}  weapons={len(P.get('weapons', []))}", flush=True)

def co(o): return np.array([(v.co.x, v.co.y, v.co.z) for v in o.data.vertices])

def place(w):
    asset = w["asset"]; path = ASSETS.get(asset); bone = w["bone"]
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

    c = co(hal); ext = c.max(0) - c.min(0); la = int(np.argmax(ext))     # longest axis -> Z (haft)
    if la != 2:
        hal.rotation_euler = (0, math.radians(90), 0) if la == 0 else (math.radians(90), 0, 0)
        bpy.ops.object.transform_apply(rotation=True); c = co(hal)
    zmin, zmax = c[:, 2].min(), c[:, 2].max(); zr = zmax - zmin           # head (wider end) -> +Z
    top = c[c[:, 2] > zmin + 0.78*zr]; bot = c[c[:, 2] < zmin + 0.22*zr]
    tw = (top[:, 0].max() - top[:, 0].min()) if len(top) > 3 else 0
    bw = (bot[:, 0].max() - bot[:, 0].min()) if len(bot) > 3 else 0
    if bw > tw:
        hal.rotation_euler = (math.radians(180), 0, 0); bpy.ops.object.transform_apply(rotation=True); c = co(hal)
    zmin, zmax = c[:, 2].min(), c[:, 2].max(); haft = c[c[:, 2] < zmin + 0.4*(zmax - zmin)]
    cx, cy = haft[:, 0].mean(), haft[:, 1].mean()                          # recenter haft to x=y=0, butt to z=0
    for v in hal.data.vertices: v.co.x -= cx; v.co.y -= cy; v.co.z -= zmin
    c = co(hal); Hn = c[:, 2].max() - c[:, 2].min()                        # uniform scale -> scale*figureH
    s = (w.get("scale", 1.0) * figureH) / max(1e-6, Hn)
    for v in hal.data.vertices: v.co *= s
    gf = 1.0 - w.get("gripAnchor", [0.5, 0.5])[1]                          # grip frac up the haft (v is from the top)
    c = co(hal); Hn = c[:, 2].max() - c[:, 2].min(); gz = c[:, 2].min() + gf*Hn
    for v in hal.data.vertices: v.co.z -= gz                               # grip -> origin
    hal.data.update()

    ap = w["attachPoint"]
    hal.rotation_euler = (0, math.radians(w.get("rotationDeg", 0)), 0)     # in-plane (about depth axis)
    hal.location = V((ap[0], ap[1], ap[2]))
    bpy.context.view_layer.update()

    handlocal = arm.data.bones[bone].head_local.copy()
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones; hb = eb[bone]; gn = "weapon_grip_" + asset; tn = "weapon_tip_" + asset
    g = eb.new(gn); g.head = handlocal; g.tail = handlocal + V((0, 0, 0.12)); g.parent = hb; g.use_deform = False; g.use_connect = False
    t = eb.new(tn); t.head = g.tail; t.tail = g.tail + V((0, 0, 0.30)); t.parent = g; t.use_deform = False; t.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT'); hal.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    arm.data.bones.active = arm.data.bones[gn]
    bpy.ops.object.parent_set(type='BONE', keep_transform=True)
    print(f"[placed] {asset} -> {bone}  at {ap}  rot={w.get('rotationDeg',0)} scale={w.get('scale',1.0)}", flush=True)

for w in P.get("weapons", []): place(w)

for o in [m for m in list(bpy.context.scene.objects) if m.type == "MESH" and len(m.data.vertices) < 300]:
    bb = [o.matrix_world @ V(c) for c in o.bound_box]
    if max(max(p[i] for p in bb) - min(p[i] for p in bb) for i in range(3)) > 1.4: bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True)
print(f"[export] {OUT} ({os.path.getsize(OUT)//1024} KB)", flush=True)
print("BRIDGE DONE", flush=True)
