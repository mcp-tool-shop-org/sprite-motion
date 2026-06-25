# sprite-motion — Claude Design build prompt

> Paste everything between the rules below into a **new Claude Design project**.
> Before sending, **attach three files** from `sprite-motion/public/samples/`:
> `blackguard.skeleton.json`, `blackguard.front.png`, `halberd.png`.
> Then iterate in Claude Design; when it's right, export **Save as standalone HTML** and route it back to Claude Code for pipeline wiring.

---

Build a **single self-contained HTML file** (vanilla JavaScript + inline SVG + CSS — **no external libraries, no CDNs, fully offline**) named **sprite-motion**: a precise visual editor for placing a **skeleton and weapons/props onto a game-character sprite** in exact coordinate space.

**Why it exists (read this first):** it eliminates coordinate guessing in a 3D character-rigging pipeline. An auto-rigger gives us a skeleton as 3D numbers; we need to attach weapons to the right bone at the right spot. Doing that by eyeballing pixel positions is error-prone. This tool lets a human place the weapon visually on a grid whose coordinates **are the rig's real numbers**, then exports exact placement data a downstream Blender script consumes. **Precision is the whole point.**

## The core idea — the canvas *is* bone-space

The editor canvas is an SVG whose coordinate system is the rig's **"bone-space."** Every gridline is **labeled with its true coordinate value**. A bone whose data says `head = (0.229, 0.029)` must sit at exactly x = 0.229, z = 0.029 on the grid. No pixel math, no guessing — what the data says is where it renders. This is the single most important property; verify it visually.

## Bone-space coordinate system

The skeleton JSON is 3D coordinates from the auto-rigger:

- **x** = left/right. Range about **[−0.30, +0.30]**.
- **z** = down/up; **+z is up** (feet near z ≈ −0.5, head near z ≈ +0.5). The figure is ~1.0 unit tall, centered near the origin.
- **y** = depth (toward/away from the front camera). Range about **[−0.16, +0.16]**. The character **faces −Y**.

The editor is the **front view**: horizontal screen axis = **x**, vertical screen axis = **z** (with **+z drawn upward** — note SVG's y grows downward, so render z as **−z** in SVG user units). The **y / depth** value is displayed numerically and carried through export, but is not positioned in the 2D view.

## Layout — a dark technical editor (think Blender / Spine 2D / After Effects)

Three regions:
1. **Top toolbar** — load/paste skeleton, upload sprite, add weapon/prop, view toggles, **Export JSON**, "Load blackguard sample".
2. **Center canvas** — the bone-space SVG with the labeled grid, the sprite, the skeleton, and the weapons. Pan (drag empty space) and zoom (mouse wheel toward cursor). A live **crosshair coordinate readout** (monospace, e.g. `x 0.187   z 0.041`) follows the cursor.
3. **Right inspector** — properties of the selected bone or weapon, with **editable numeric fields** showing exact coordinates.

## Layer 1 — Sprite (reference image, behind everything)

- Upload a PNG/JPG via a file input (and accept the attached `blackguard.front.png` as the sample).
- Place it in bone-space by **center (cx, cz) + height** (width derived from the image aspect ratio). Default it centered on the skeleton's bounding box with height ≈ 1.18× the skeleton height, so it roughly registers immediately; let the user fine-tune cx/cz/height + **opacity** + **show/hide** in the inspector. (The sprite is a visual aid; the skeleton numbers are ground truth — the user nudges the sprite to register it under the skeleton.)

## Layer 2 — Skeleton

**Loading:** support all three — (a) **"Load blackguard sample"** button that loads the embedded/attached `blackguard.skeleton.json`; (b) **upload a `.json`**; (c) **paste JSON** into a textarea. On load, frame the view to the skeleton's bbox.

**Schema** (this is the format — preserve it exactly on export):
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
Each bone has a `head` and `tail` (3D), a `parent` name (or null), and a `deform` flag.

**Render:** draw each bone as a **line from head→tail** (project (x,z)); draw a **filled circle "joint" at each head**. Joints and lines should be a **constant on-screen size** regardless of zoom (use `vector-effect="non-scaling-stroke"` for lines; scale circle radius with the viewBox width). Style **non-deform** bones differently (dashed / dimmer) — they're sockets, not skin bones.

**Interaction:** click a joint to **select** it (highlight + show in inspector). **Drag a joint** to move that bone's `head`; keep the chain visually joined by moving the **parent's `tail`** to the same point. While hovering/selected, show the joint's exact `(x, y, z)` in the inspector and a small floating label. (Bone editing is secondary to weapon placement, but it must be precise.)

## Layer 3 — Weapons / props (the main job)

- **Add a weapon:** upload a transparent PNG (accept the attached `halberd.png` sample) — it becomes a draggable prop.
- Each weapon has:
  - **`bone`** — the bone it's attached to (default to a hand bone: pick the bone whose name matches `/hand|wrist|bone_9$/`, else the first bone). Editable via a dropdown in the inspector.
  - **`gripAnchor` [u, v]** — a normalized point **inside the image** (0..1, top-left origin) that represents *where the hand grips the weapon* (e.g., on the halberd's haft). Default `[0.5, 0.6]`. Let the user set it by **clicking on the weapon image** in a small inspector thumbnail (show a marker). This is what gets placed at the bone.
  - **`offset` [x, z]** — bone-space offset from the bone's `head` to the grip anchor. Set by **dragging the weapon** on the canvas.
  - **`rotationDeg`** — in-plane rotation (about the depth axis), via a slider/number and an on-canvas rotate handle.
  - **`scale`** — size as a multiple of the figure's height (default ~1.2 for a polearm), via slider/number.
- **Render:** draw the weapon image so its **gripAnchor sits exactly at `bone.head + offset`** (in bone-space), sized by `scale × figureHeight` (width by aspect), rotated by `rotationDeg` about the grip anchor. Show a small marker at the grip anchor. Selected weapon shows a bounding box + rotate/scale handles.
- **Dragging** the weapon updates `offset` only (grab-relative, so it doesn't jump to the cursor). Multiple weapons/props allowed.

## Inspector (right panel)

- **Nothing selected:** show skeleton name, bone count, sprite controls (cx, cz, height, opacity, visible).
- **Bone selected:** name, parent, exact `head` and `tail` as editable numeric fields (4 decimals), `deform` flag.
- **Weapon selected:** attached-bone dropdown, `offset` x/z fields, `rotationDeg` slider+field, `scale` slider+field, grip-anchor thumbnail picker, a **Remove** button, and a read-only **resolved attach point** `(x, y, z) = bone.head + offset` (this is what the rigger uses).

Coordinate fields use a **monospace** font and accept typed values (two-way: edit the number → the canvas updates).

## Export

A toolbar **Export JSON** button downloads `sprite-motion.placement.json`:
```json
{
  "skeleton": "blackguard_dec_rigged",
  "facing": "-Y",
  "sprite": { "cx": 0.0, "cz": 0.0, "height": 1.18 },
  "weapons": [
    {
      "asset": "halberd",
      "bone": "bone_9",
      "offset": [0.018, -0.004],
      "gripAnchor": [0.5, 0.6],
      "rotationDeg": 0,
      "scale": 1.2,
      "attachPoint": [0.2472, 0.009, 0.0251]
    }
  ]
}
```
`attachPoint` = `bone.head + [offset.x, 0, offset.z]` (the bone's y carried through) — the exact bone-space point the 3D rig drops the weapon's grip onto. Round all numbers to 4 decimals. Also offer **Export skeleton JSON** (re-emits the skeleton in the input schema, including any joint edits).

## Visual design spec

- Dark technical theme: background `#16161a`, panels `#1f1f25`, panel borders `#2e2e36`.
- Grid lines `#2b2b33`; **origin axes (x=0, z=0) brighter** `#4a4a58`; grid labels `#7a7a88` monospace ~11px.
- Bones: deform = `#7fd4e6` (cyan), non-deform = `#b98bf0` dashed (violet). Joints: filled `#cfd6dd`, **selected = `#f0a830` (amber)** with a ring.
- Weapons: subtle drop shadow; grip-anchor marker amber; selection box amber dashed.
- Accent/active controls amber `#f0a830`. Buttons flat, dark, with hover states. Coordinate readouts always **monospace**.
- Crisp, dense, professional — this is a precision tool, not a marketing page. No rounded-cartoon styling, no gradients-for-flair.

## Acceptance — it's right when

1. Load the blackguard sample → the 40-bone skeleton appears, framed, and `bone_9`'s joint reads `head ≈ (0.229, 0.009, 0.029)` in the inspector and sits where the grid says.
2. Gridlines are labeled with real coordinate values; panning/zooming keeps labels and bone positions exact.
3. Upload `blackguard.front.png` → it registers under the skeleton; opacity adjustable.
4. Add `halberd.png` → it attaches to a hand bone; dragging sets the offset; the inspector's resolved **attachPoint** updates live; rotation/scale work.
5. Export JSON produces the schema above with 4-decimal numbers and a correct `attachPoint`.
6. Everything is in one offline HTML file with the blackguard sample embedded.

---
