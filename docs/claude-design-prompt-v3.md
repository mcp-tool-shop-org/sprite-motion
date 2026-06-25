# sprite-motion v3 — Claude Design build prompt (precision: snapping · depth/Y · presets · weapon-tip)

> Extends v2. **Attach `app/sprite-motion.slim.html`** (≈94 KB) and paste this prompt so Claude Design edits the working app. The **HARD PRESERVE** list is binding.

---

You are extending **sprite-motion** (a self-contained offline HTML editor — vanilla JS + inline SVG + CSS, no external libraries). v3 adds **precision + reuse** features. Do not break anything in v1/v2.

## Why these features (grounded in the studio's sprite-motion knowledge base)

These aren't arbitrary — each is what makes a placement survive the real render pipeline:
- The rigged asset is rendered to **8-direction 2.5D sprites** from an **orthographic camera at 30–45° elevation** (KB · rigging · *TRELLIS→Blender→8-dir render*; src: Foozle, *Render 4/8-Direction Sprites from Blender*). So a weapon's **depth (Y)** changes how it reads per direction.
- **Readable silhouette** is the primary channel, and *"oblique directions (NE/NW/SE/SW) collapse depth cues — each directional variant needs its own silhouette check"* (KB · combat-craft · *Readable silhouette*; src: Moon Studios, *Animating Ori*). Depth control + a 2.5D preview let you author placements that don't collapse at obliques.
- The weapon rides a **hand→weapon_grip→weapon_tip** chain, and *"weapon_tip velocity can be sampled per frame for hit-box data"* (KB · rigging · *Rigid weapon bone chain*; src: Blender Manual, Armatures). So capturing the **tip** (the business end), not just the grip, is what later gives combat its hitboxes.
- The rig is **deterministic and precise** by design (KB · rigging · *humanoid bone hierarchy*), which is exactly why **snapping** to grid increments and to bones belongs in the authoring tool.

## HARD PRESERVE (do not change behavior or break)
The bone-space canvas + labeled grid; pan/zoom/crosshair; skeleton load/drag with exact `(x,y,z)` readout; sprite layer; weapon placement (drag offset, grip-anchor picker, rotation, scale, resolved `attachPoint`); the **command palette** (double-right-click / `Ctrl/⌘K`, right-click reserved); **Characters** panel (multi + bulk); **Library** (reusable props); **project save/load + autosave**; **Export JSON** (active) and **Export all placements** (roster); the dark technical theme.

## NEW v3 features

### 1. Snapping (toggle, default on)
- A **Snap** toggle (toolbar + palette + hotkey `S`). When on, dragging a **joint** or a **weapon** snaps to:
  - the **grid increment** (the currently displayed gridStep — e.g. 0.05/0.1), and
  - **nearby bone heads/tails** within a small screen threshold (~10 px) — snapping a weapon's grip onto a bone joint sets its bone + zeroes the in-plane offset.
- Show a small snap indicator (a ring on the snapped target). Holding **Alt** temporarily disables snap while dragging. A settable grid increment field (default = auto gridStep).

### 2. Depth / Y control + 2.5D preview
- Give every weapon a **depth (Y)** value — its position toward (−Y, front) / away (+Y) from the front camera. Add a `depthY` slider + numeric field in the weapon inspector (range about −0.15…+0.15). The resolved **attachPoint** becomes `[bone.head.x + offset.x, bone.head.y + depthY, bone.head.z + offset.z]` (so Y is now author-controlled, not just inherited from the bone).
- Add a **2.5D preview** toggle (toolbar + palette) that tilts the canvas to the game camera (~35° elevation, orthographic-style) so you can see how the weapon's depth reads — the front view stays the default for precise placement; the preview is for checking the oblique read. In the preview, render the weapon offset by its `depthY` so depth is visible. (Front view = authoring; 2.5D = verification, per the silhouette rule.)

### 3. Weapon presets (save once, reuse)
- A weapon's full transform — `bone` (by role, e.g. the hand), `offset`, `depthY`, `rotationDeg`, `scale`, `gripAnchor`, `tipAnchor` — can be **saved as a named preset** (e.g. "two-hand polearm low", "one-hand sword guard"). Presets live in the project (a `presets[]` array) and appear in a small **Presets** menu.
- **Apply a preset** to the selected weapon (or to a freshly dropped prop) to set its transform in one click. Presets are character-independent (reuse the same hold across the roster). Save / rename / delete presets; a couple of sensible built-ins are fine.

### 4. Weapon tip anchor (the business end)
- Alongside the grip anchor, let the user set a **tip anchor** `[u,v]` on the weapon image (the point that is the weapon's striking end — a polearm's spike, a sword's point) via the same click-on-thumbnail picker (a second, differently-colored marker). Default to the top-centre of the image (`[0.5, 0.04]`).
- Export it as `tipAnchor` per weapon. The Blender bridge uses it to place the **weapon_tip** bone at the real tip (for hitbox/velocity data downstream); if absent it falls back to the weapon's top.

## Schema additions (extend, don't rename existing fields)
Per weapon (in placement / placements / project): add **`depthY`** (number) and **`tipAnchor`** (`[u,v]`). `attachPoint` now includes the author-controlled Y. Project gains a top-level **`presets`** array:
```json
"presets": [
  { "name": "two-hand polearm low", "boneRole": "hand",
    "offset": [0.018, -0.01], "depthY": 0.0, "rotationDeg": 0, "scale": 1.2,
    "gripAnchor": [0.5, 0.6], "tipAnchor": [0.5, 0.04] }
]
```
Example exported weapon block:
```json
{ "asset":"halberd", "bone":"bone_9", "offset":[0.018,-0.01], "depthY":0.0,
  "gripAnchor":[0.5,0.6], "tipAnchor":[0.5,0.04], "rotationDeg":0, "scale":1.2,
  "attachPoint":[0.2472,0.009,0.0191] }
```

## Command palette — add (keep all existing)
`Toggle snapping`, `Toggle 2.5D preview`, `Set depth/Y…`, `Save weapon preset…`, dynamic `Apply preset: <name>`, `Set tip anchor`.

## Visual design
Match the existing dark theme exactly. The 2.5D preview is a transform of the same canvas (no new colors). Snap indicator + tip-anchor marker use the amber accent (tip marker a distinct hue from the grip marker). Don't restyle existing panels.

## Acceptance — v3 is right when
1. All HARD PRESERVE behavior still works (load sample, place weapon, palette, characters, library, save/load, export with a correct `attachPoint`).
2. With Snap on, dragging a weapon near a joint snaps its grip onto that bone; Alt disables snap live.
3. Changing a weapon's depth/Y updates `attachPoint.y`; the 2.5D preview visibly shifts the weapon in depth.
4. Save a weapon's transform as a preset, drop the same prop on a second character, Apply preset → identical hold.
5. Set a tip anchor; export shows `depthY` + `tipAnchor`; the placement still round-trips through save/load.

---
