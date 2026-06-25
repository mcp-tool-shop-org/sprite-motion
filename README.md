# sprite-motion

**A precise visual editor for placing skeletons and weapons/props onto game-character sprites in exact coordinate space.**

sprite-motion exists to **eliminate coordinate guessing** in the studio's 3D character-rigging pipeline. An auto-rigger gives us a character skeleton as raw 3D numbers; we then need to attach weapons (a halberd, an axe, a staff) to the right bone at the right spot. Doing that by eyeballing pixel positions in a headless renderer is slow and error-prone — it was the wall the pipeline kept hitting. This tool puts the placement in a browser where **the canvas grid *is* the rig's real coordinate space**, so you drag a weapon onto the hand, read the exact numbers, and export placement data the Blender rig step applies verbatim.

> Status: **editor v3 is in the repo** — [`app/sprite-motion.html`](app/sprite-motion.html), a self-contained offline build (made with **Claude Design**): a bone-space canvas for placing weapons/props precisely, with **snapping** (grid + bones), per-weapon **depth/Y + a 2.5D preview**, **weapon presets**, grip + **tip anchors**, a **Characters panel** (multi + bulk), a reusable **weapon/prop library**, **project save/load** (autosave), and a **command palette** (double right-click or `Ctrl/⌘K`). Export one character's placement, or the **whole roster** in one file. The **Blender bridge** ([`pipeline/apply_placement.py`](pipeline/apply_placement.py)) consumes either and attaches each weapon GLB at the exact `attachPoint` (depth, rotation, scale) with a `weapon_grip → weapon_tip` chain whose tip joint follows the editor's `tipAnchor` — a single character, or the whole roster in one run (`pipeline/build_manifest.py` auto-builds the manifest). The full loop (**export skeleton → place → apply**) is closed; the weapon lands precisely where you put it. The coordinate math (front projection, grid, render transforms) lives in [Coordinate math](#coordinate-math-editor-internals) below — ported from an earlier React/SVG exploration that has since been retired.

---

## The core idea — the canvas *is* bone-space

The editor canvas is an SVG whose coordinate system is the rig's **"bone-space."** Every gridline is **labeled with its true coordinate value**. A bone whose data says `head = (0.229, 0.029)` renders at exactly x = 0.229, z = 0.029 on the grid. No pixel math, no guessing — what the data says is where it is. That property is the whole point of the tool.

## Bone-space coordinate system

Skeleton coordinates come from the auto-rigger (UniRig) as normalized 3D values:

| Axis | Meaning | Range (typical) |
|------|---------|-----------------|
| **x** | left / right | ≈ `[-0.30, +0.30]` |
| **z** | down / up (**+z is up**; feet ≈ −0.5, head ≈ +0.5) | ≈ `[-0.50, +0.50]` |
| **y** | depth (character **faces −Y**) | ≈ `[-0.16, +0.16]` |

The editor is the **front view**: screen-horizontal = **x**, screen-vertical = **z** (drawn with +z upward; since SVG's y grows downward, render z as `−z`). The **y / depth** value is shown numerically and carried through export, but isn't positioned in the 2D view. The figure is ~1.0 unit tall, centered near the origin.

## The three layers

1. **Sprite** — a reference character image (PNG), placed in bone-space by centre + height and registered under the skeleton (opacity adjustable). A visual aid; the skeleton numbers are ground truth.
2. **Skeleton** — loaded from JSON (see schema below). Bones draw as `head → tail` lines with draggable joint circles; deform bones vs non-deform "socket" bones are styled differently; selecting a joint shows its exact `(x, y, z)`.
3. **Weapons / props** — uploaded transparent PNGs, dragged onto a bone. Each carries a **grip anchor** (where the hand grips the image), a bone-space **offset**, an in-plane **rotation**, and a **scale**. This is the main job: place the weapon precisely on the hand.

## Data schemas

### Skeleton (input) — `public/samples/blackguard.skeleton.json`
```json
{
  "name": "blackguard_dec_rigged",
  "facing": "-Y",
  "bbox": { "x": [-0.30, 0.30], "y": [-0.16, 0.15], "z": [-0.50, 0.50] },
  "bones": [
    { "name": "bone_9", "parent": "bone_8",
      "head": [0.2292, 0.009, 0.0291], "tail": [0.2488, 0.0068, 0.0009], "deform": true }
  ]
}
```
Exported by `_export_skeleton.py` straight from the rigged GLB — exact numbers, no transcription. The sample is the **blackguard** villain (40 bones; `bone_9` is the right-hand wrist that holds the halberd).

### Placement (output) — `sprite-motion.placement.json`
```json
{
  "skeleton": "blackguard_dec_rigged",
  "facing": "-Y",
  "sprite": { "cx": 0.0, "cz": 0.0, "height": 1.18 },
  "weapons": [
    { "asset": "halberd", "bone": "bone_9",
      "offset": [0.018, -0.004], "gripAnchor": [0.5, 0.6],
      "rotationDeg": 0, "scale": 1.2,
      "attachPoint": [0.2472, 0.009, 0.0251] }
  ]
}
```
`attachPoint = bone.head + [offset.x, 0, offset.z]` — the exact bone-space point the Blender rig drops the weapon's grip onto. This replaces hand-guessed coordinates.

## Coordinate math (editor internals)

Reference for the bone-space ↔ screen projection and the render transforms — ported here from an earlier React/SVG exploration (the retired `src/` tree) so the math survives the editor's move to self-contained HTML. The shipping editors (`app/*.html`) and the Python pipeline have no build step; nothing below requires one.

**Front projection.** Bone-space is 3D — `x` = screen-right, `z` = up, `y` = depth (camera faces −Y). The editor draws the `(x, z)` front view; `y` is shown numerically and carried through export, never positioned in 2D. SVG's y-axis grows downward, so +z must render up:

```
toSvg(x, z)     = (x, −z)     // bone-space → SVG user space
fromSvg(sx, sy) = (sx, −sy)   // SVG → bone-space (cursor hit-testing)
```

The SVG `viewBox` is expressed in these flipped coords, so the canvas grid *is* bone-space: 1 SVG unit = 1 bone-space unit.

**Fit the view to a skeleton.** Pad the bbox ~18 % and frame it. The top edge is `z = z1` (max z), so the viewBox origin's y is `−(z1 + pad)`:

```
w  = x1 − x0,          h  = z1 − z0
px = w·0.18 + 0.04,    pz = h·0.18 + 0.04
viewBox = { x: x0 − px,   y: −(z1 + pz),   w: w + 2·px,   h: h + 2·pz }
```

**"Nice" grid step.** Aim for ~8–14 gridlines on the larger axis; snap the raw step to 1 / 2 / 5 / 10 × 10ⁿ:

```
raw  = max(w, h) / 11
pow  = 10^floor(log10(raw))
n    = raw / pow
step = (n<1.5 ? 1 : n<3.5 ? 2 : n<7.5 ? 5 : 10) · pow
```

Labels are 2-dp with trailing zeros trimmed and exact zero shown as `0`; the `x = 0` and `z = 0` lines are styled as axes.

**Place a weapon image.** A weapon sits on its bone at `attach = bone.head + offset` (offset is bone-space `(x, z)`). Its image scales to `h = scale · skeletonHeight`, width `wd = h · aspect`, and is positioned so the image's normalised **grip anchor** `(ax, ay) ∈ [0,1]²` lands on the attach point, then rotated in-plane about that point:

```
(sx, sy)    = toSvg(attach.x, attach.z)
imageCorner = (sx − ax·wd,  sy − ay·h)
transform   = rotate(rotationDeg, about (sx, sy))
```

**Place the reference sprite.** Centred at `(cx, cz)`, spanning `height` in bone-space, aspect from the image:

```
x = cx − (height·aspect)/2,   y = −(cz + height/2),   width = height·aspect
```

**Zoom about the cursor.** On wheel, scale the view by `f` (≈1.12 per notch) while keeping the bone-space point under the cursor fixed:

```
x' = mx − (mx − x)·f,   y' = my − (my − y)·f,   w' = w·f,   h' = h·f
```

**Export → `attachPoint`.** The 2D offset becomes a full 3D bone-space point the rig consumes (y taken from the bone head, unchanged), rounded to `1e-4`:

```
attachPoint = [ head.x + offset.x,  head.y,  head.z + offset.z ]
```

This is the resolved point in the **Placement** schema above — what the Blender step drops the grip onto.

### Editor data model

The internal types the exploration used (the export schema above is the persisted subset):

| Type | Fields |
|------|--------|
| `Bone` | `name`, `parent`, `head:[x,y,z]`, `tail:[x,y,z]`, `deform` |
| `Skeleton` | `name`, `facing`, `bbox:{x,y,z:[min,max]}`, `bones[]` |
| `SpriteState` | `src`, `aspect` (w/h), `cx`, `cz`, `height`, `opacity`, `visible` |
| `Weapon` | `asset`, `src`, `aspect`, `bone`, `offset:[x,z]`, `anchor:[u,v]` (grip, 0–1), `rotationDeg`, `scale` |

Defaults the editor applied on load: sprite centre = bbox midpoint, sprite height = z-span × 1.18; a new weapon binds to the selected bone, else the first bone matching `/hand|wrist|bone_9$/`. Bone joints stay chain-joined — dragging a head moves the parent's tail with it.

## Where it fits the pipeline

```
A-pose body concept ─▶ TRELLIS.2 mesh ─▶ UniRig skeleton + skin ─▶ rigged GLB
                                                                       │
                                          _export_skeleton.py ◀────────┘
                                                   │ skeleton.json
                                                   ▼
        weapon image (Qwen + house LoRA) ─▶ transparent PNG ─▶ TRELLIS.2 ─▶ weapon GLB
                                                   │                              │
                                                   ▼                              │
                                          ┌──────────────────┐                    │
                                          │   sprite-motion   │  place visually   │
                                          │  (this editor)    │  on the bone       │
                                          └──────────────────┘                    │
                                                   │ placement.json               │
                                                   ▼                              ▼
                                    Blender weapon-attach (consumes attachPoint) ─▶ game-ready GLB
```

The editor is the **placement authority**; the headless Blender step is the **applier**. Same data drives all 68 characters (villains · goblins · pirates).

## Repository layout

| Path | What |
|------|------|
| [`app/sprite-motion.html`](app/sprite-motion.html) | **The editor** — self-contained offline HTML. Open it in any browser; double-right-click (or `Ctrl/⌘K`) for the command palette. |
| [`app/sprite-motion.slim.html`](app/sprite-motion.slim.html) | Same editor, ~65 KB (sample images stubbed) — the build to **attach to Claude Design** for v2 work. |
| [`pipeline/export_skeleton.py`](pipeline/export_skeleton.py) | Blender: dump a rigged GLB's armature → the skeleton JSON the editor loads (exact numbers). |
| [`pipeline/apply_placement.py`](pipeline/apply_placement.py) | Blender: consume a single-character placement, or **all placements** (whole roster, via `--manifest`) → attach each weapon GLB at its exact `attachPoint` (rotation + scale), building a non-deform `weapon_grip → weapon_tip` chain (heads at the grip + the business end, for hit-box data) → game-ready GLB. |
| [`pipeline/placement.example.json`](pipeline/placement.example.json) | Example single-character export (`--placement` for one char + `--char`). |
| [`pipeline/placements.example.json`](pipeline/placements.example.json) | Example roster export ("Export all placements"). |
| [`pipeline/manifest.example.json`](pipeline/manifest.example.json) | Template: skeleton names + weapon assets → rigged GLBs, for the roster run. |
| [`pipeline/build_manifest.py`](pipeline/build_manifest.py) | Auto-generate the roster manifest from a folder of rigged GLBs + a folder of weapon GLBs (no Blender). `--check` a placements file to catch naming gaps before the batch. |
| [`docs/claude-design-prompt.md`](docs/claude-design-prompt.md) | v1 build spec — paste into Claude Design, attach the three sample files, build the editor as standalone HTML. |
| [`docs/claude-design-prompt-v2.md`](docs/claude-design-prompt-v2.md) | v2 build spec (expand the editor) — multi-character + bulk, reusable weapon/prop library, project save/load. Attach `app/sprite-motion.slim.html` and extend. |
| [`docs/claude-design-prompt-v3.md`](docs/claude-design-prompt-v3.md) | v3 build spec (precision) — snapping, depth/Y + 2.5D preview, weapon presets, weapon-tip anchor. KB-grounded (rigging 2.5D camera + weapon_tip; combat-craft silhouette). |
| `public/samples/blackguard.skeleton.json` | Real 40-bone skeleton (the embedded sample). |
| `public/samples/blackguard.front.png` | Body sprite for the reference layer. |
| `public/samples/halberd.png` | Transparent halberd prop. |

## Using it

Open [`app/sprite-motion.html`](app/sprite-motion.html) in a browser → **Load blackguard sample** → upload the sprite + halberd from `public/samples/` → drag the weapon onto the hand bone → **Export placement JSON**. Double-right-click anywhere (or `Ctrl/⌘K`) for the command palette — type `bone_9` to jump straight to the hand joint, toggle layers, fit the view, export, etc.

## Batch the whole roster

Once the rigged GLBs exist, place weapons across all characters in the editor, **Export all placements**, then:
```bash
# 1. auto-build the manifest from your folders (and validate it against the export)
python pipeline/build_manifest.py --chars rigged/ --weapons weapons/ \
    --out manifest.json --check placements.json
# 2. rig every character at its exact attachPoints in one run
blender -b --python pipeline/apply_placement.py -- \
    --placement placements.json --manifest manifest.json --outdir out/
```

## How the editor is built (Claude Design loop)

1. Open a new project at **claude.ai/design**, attach the three `public/samples/*` files, paste [`docs/claude-design-prompt.md`](docs/claude-design-prompt.md).
2. Iterate, then **Save as standalone HTML**.
3. Bring it back here: surgical features (e.g. the command palette) are added in Claude Code, and `placement.json` is wired into the Blender weapon-attach step so the weapon lands exactly where the editor placed it.

## License

See [LICENSE](LICENSE).
