# sprite-motion

**A precise visual editor for placing skeletons and weapons/props onto game-character sprites in exact coordinate space.**

sprite-motion exists to **eliminate coordinate guessing** in the studio's 3D character-rigging pipeline. An auto-rigger gives us a character skeleton as raw 3D numbers; we then need to attach weapons (a halberd, an axe, a staff) to the right bone at the right spot. Doing that by eyeballing pixel positions in a headless renderer is slow and error-prone — it was the wall the pipeline kept hitting. This tool puts the placement in a browser where **the canvas grid *is* the rig's real coordinate space**, so you drag a weapon onto the hand, read the exact numbers, and export placement data the Blender rig step applies verbatim.

> Status: **editor v1 is in the repo** — [`app/sprite-motion.html`](app/sprite-motion.html), a self-contained offline build (made with **Claude Design** from [`docs/claude-design-prompt.md`](docs/claude-design-prompt.md)): load a skeleton, register the reference sprite, place weapons/props, jump to any bone via the **command palette** (double right-click or `Ctrl/⌘K`), and export placement JSON. The **Blender bridge** ([`pipeline/apply_placement.py`](pipeline/apply_placement.py)) consumes that placement and attaches the weapon GLB at the exact `attachPoint` — so the full loop (**export skeleton → place in the editor → apply**) is closed and the weapon lands precisely where you put it. A partial React exploration in `src/` is kept as reference for the coordinate math.

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
| [`pipeline/apply_placement.py`](pipeline/apply_placement.py) | Blender: consume `placement.json` + weapon GLB(s) → attach each at its exact `attachPoint` (rotation + scale) → game-ready GLB. |
| [`pipeline/placement.example.json`](pipeline/placement.example.json) | Example editor output (and the bridge's test input). |
| [`docs/claude-design-prompt.md`](docs/claude-design-prompt.md) | v1 build spec — paste into Claude Design, attach the three sample files, build the editor as standalone HTML. |
| [`docs/claude-design-prompt-v2.md`](docs/claude-design-prompt-v2.md) | v2 build spec (expand the editor) — multi-character + bulk, reusable weapon/prop library, project save/load. Attach `app/sprite-motion.slim.html` and extend. |
| `public/samples/blackguard.skeleton.json` | Real 40-bone skeleton (the embedded sample). |
| `public/samples/blackguard.front.png` | Body sprite for the reference layer. |
| `public/samples/halberd.png` | Transparent halberd prop. |
| `src/` | **Reference only** — an early React/SVG exploration that captures the bone-space projection (`src/lib/projection.ts`), the data types (`src/types.ts`), the store, and a draggable canvas. The canonical editor is the Claude Design HTML; this documents the math/interactions. |

## Using it

Open [`app/sprite-motion.html`](app/sprite-motion.html) in a browser → **Load blackguard sample** → upload the sprite + halberd from `public/samples/` → drag the weapon onto the hand bone → **Export placement JSON**. Double-right-click anywhere (or `Ctrl/⌘K`) for the command palette — type `bone_9` to jump straight to the hand joint, toggle layers, fit the view, export, etc.

## How the editor is built (Claude Design loop)

1. Open a new project at **claude.ai/design**, attach the three `public/samples/*` files, paste [`docs/claude-design-prompt.md`](docs/claude-design-prompt.md).
2. Iterate, then **Save as standalone HTML**.
3. Bring it back here: surgical features (e.g. the command palette) are added in Claude Code, and `placement.json` is wired into the Blender weapon-attach step so the weapon lands exactly where the editor placed it.

## License

See [LICENSE](LICENSE).
