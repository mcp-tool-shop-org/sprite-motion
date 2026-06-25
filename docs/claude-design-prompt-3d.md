# sprite-motion 3D — Claude Design build prompt (a real 3D weapon-placement viewport)

> **Fresh build, not an extension of the 2D editor.** Paste this whole prompt into a new Claude Design project. Nothing needs to be attached for Claude Design to build and self-test (the spec includes a synthetic stand-in rig). *Optionally* attach `blackguard_dec_rigged.glb` (11 MB) + `halberd_trellis.glb` (2.2 MB) to test loading a real character — but the app must work via file-picker regardless.
>
> Output: **one self-contained HTML file** (`Save as standalone HTML`). It will be brought back into Claude Code to inline three.js for true-offline and to wire the export into the Blender bridge.

---

You are building **sprite-motion 3D** — a precise, offline, single-file HTML tool for **placing a rigid weapon/prop onto an auto-rigged 3D game character at an exact bone, in true 3D**, then verifying how it reads from the 8 render directions. It replaces a 2D predecessor that could only place a flat image on a front-view grid; that approach could not express out-of-plane weapon orientation or show the oblique-angle read, which is the whole job. This tool is **WYSIWYG in 3D**: what you orient in the viewport is exactly what the headless Blender rig step applies. No coordinate guessing.

## Why this shape (grounded in the studio knowledge base — these are not arbitrary)

- The rigged asset is rendered to **8-direction 2.5D sprites** from an **orthographic camera at 30–45° elevation** (KB · rigging · *TRELLIS→Blender→8-dir render*; src: Foozle, *Render 4/8-Direction Sprites from Blender*). A weapon's full 3D orientation — not just an in-plane angle — determines whether it reads in every direction. **So the camera must be able to snap to all 8 of those exact directions.**
- **Readable silhouette is the primary channel**, and *"oblique directions (NE/NW/SE/SW) collapse depth cues — a side-slash that reads at 0° can look like a forward-push at 45°; each directional variant needs its own silhouette check"* (KB · combat-craft · *Readable silhouette*; src: Moon Studios, *Animating Ori*). **So the tool offers a desaturated silhouette mode and an 8-up contact sheet** to catch collapses while authoring.
- The weapon rides a **hand → weapon_grip → weapon_tip** rigid bone chain, and *"weapon_tip velocity can be sampled per frame for hit-box data"* (KB · rigging · *Rigid weapon bone chain*; src: Blender Manual, Armatures). glTF stores joint **heads**, so the meaningful positions are the **grip point** and the **tip (business end)**. **So the tool captures both an explicit grip point and an explicit tip point on the weapon mesh.**
- The rig is **deterministic and precise by design** (KB · rigging · *humanoid bone hierarchy*). **So bone selection is exact (pick from the real skeleton), the transform read-outs are numeric, and snapping is available.**

## Stack (keep it one self-contained HTML file)

- **Vanilla three.js** (r160+) loaded via an **import map** from jsDelivr (`three` and `three/addons/...`). Use a single pinned version in one importmap block — this file will later have three.js inlined for offline use, so keep all three.js imports through that one map.
- Modules used: `GLTFLoader`, `OrbitControls`, `TransformControls`, `SkeletonHelper`. No React, no build step, no other libraries.
- All UI is hand-rolled HTML/CSS/JS over the WebGL canvas. Dark technical theme (see Visual design).

## Layout

- **Center:** the 3D viewport — perspective/orthographic camera, ground grid, world axes, neutral 3-point lighting bright enough to read the mesh (no dark renders).
- **Top toolbar:** Load Character (GLB) · Load Weapon (GLB) · Gizmo mode (Translate / Rotate / Scale) · Snap toggle · Silhouette toggle · Camera: `Free · N · NE · E · SE · S · SW · W · NW` · 2.5D-elevation lock · Contact sheet · Export.
- **Left rail panels** (collapsible): **Characters**, **Weapons / Library**, **Inspector** (selected weapon transform), **Presets**.
- **Command palette:** open with **double-right-click** anywhere or **Ctrl/⌘-K** (single right-click stays free). Fuzzy-filter every action below. The palette is the fast path; the toolbar mirrors the common ones.

## The viewport — the core interaction

1. **Load a character.** `Load Character` imports a rigged GLB (a SkinnedMesh + an armature/skeleton). Display the mesh. Frame the camera to fit. A **Skeleton** toggle overlays the bones (SkeletonHelper) with a small clickable joint marker at every bone head.
2. **Pick the socket bone.** Click a joint marker **or** pick from a searchable **bone list** (the real bone names from the skeleton, e.g. `bone_9`). The selected bone highlights; show its **name** and its **world position (x,y,z)**. This bone is the attachment socket (typically the weapon hand).
3. **Load a weapon.** `Load Weapon` imports a weapon GLB as a rigid mesh and parents it to the selected bone so it rides the hand. It appears at the bone; the user then places it.
4. **Place it in 3D (WYSIWYG).** A **TransformControls gizmo** on the weapon supports **Translate (all 3 axes)**, **Rotate (full 3-axis orientation)**, and **uniform Scale**. The transform is **relative to the bone** (the weapon is the bone's child), so orbit the camera, line the weapon up in the hand from several angles, and it stays put relative to the bone. Number fields in the Inspector mirror the gizmo (position xyz, rotation as Euler °, scale) and are directly editable.
5. **Set grip + tip points on the weapon.** Two pickable points **on the weapon mesh** (click the mesh to set; raycast to nearest surface point):
   - **Grip** — the point the hand holds (the point that should sit at the bone). Default = the weapon's local origin. Marker color A.
   - **Tip** — the striking end (a polearm's spike, a sword's point), for the downstream `weapon_tip` bone. Default = farthest mesh vertex from the grip along the dominant axis. Marker color B (distinct from grip).
   These are stored in **weapon-local space** so they survive any later transform.
6. **Snapping (toggle, default on).** With Snap on, dragging the **Translate** gizmo snaps the weapon's **grip point onto the nearest bone joint** within a small screen threshold (sets/keeps the socket bone and zeroes residual offset). Hold **Alt** to disable snap live. Show a ring on the snapped joint.

## Verifying the 8-direction read (this is what makes a placement ship)

- **Camera direction snap.** The 8 direction buttons place an **orthographic** camera around the character at the **2.5D elevation** (default **35°**, adjustable 30–45° via the elevation lock), looking at the character center — these are the real render directions. `Free` returns to orbit. This is how you check that the held weapon reads at obliques, per the silhouette rule.
- **Silhouette mode.** A toggle that flat-shades the whole scene to a single mid-grey (character + weapon) so you judge the pose/weapon read by silhouette alone — the KB's primary readability channel.
- **Contact sheet.** A button that renders all **8 directions into a 3×3 thumbnail grid** (center cell blank or free-cam) in a panel, each labeled with its direction. This is the at-a-glance "does it collapse anywhere?" check, and it is the exact artifact the studio's render-QA jury consumes downstream. Offer **Download contact sheet (PNG)**.

## Carry-over UX (from the 2D tool — keep these)

- **Characters panel:** load multiple characters; each remembers its loaded GLB (by name) and its placed weapons; switch between them; the export can be one character or the whole roster (see schema).
- **Weapons / Library panel:** a reusable list of loaded weapon assets (by name) so the same weapon can be dropped on many characters without re-importing.
- **Presets:** save a weapon's reusable hold — `boneRole` (e.g. "hand") + its `boneLocal` transform + `gripLocal`/`tipLocal` — as a **named preset** ("two-hand polearm", "one-hand sword guard"); apply a preset to the selected (or freshly dropped) weapon in one click (it re-resolves `rootTransform` against the new character's bone). Presets are character-independent and live in the project. Save / rename / delete; a couple of sensible built-ins are fine.
- **Project save / load + autosave:** the whole project (characters, placements, library, presets, camera prefs) serializes to JSON and restores via `localStorage` autosave + explicit Save/Load `.json`.

## Coordinate space (read before wiring export)

The 3D editor works in **three.js native space — Y-up, right-handed**, loaded straight from the GLB. **Load every character at the world origin** and express all exported numbers **relative to the character root** (so they don't depend on where the camera or character sits in the scene). The Blender bridge converts Y-up → Z-up itself — your job is only to emit correct three.js-space numbers. (The old 2D editor authored in Blender Z-up; that mismatch is why this format is versioned `4` and tagged `"space": "gltf-y-up"`.)

## Export schema (the durable contract — match these field names exactly)

Per weapon, two views of the same placement: **`rootTransform`** (resolved to the character root — the bridge contract, WYSIWYG) and **`boneLocal`** (relative to the socket bone — for preset reuse). Grip/tip points appear both in character-root space (`attachPoint`/`tipPoint` → the bone chain) and weapon-local space (`gripLocal`/`tipLocal` → presets).

**Single character** (`Export JSON`):
```json
{
  "format": "sprite-motion.placement",
  "version": 4,
  "skeleton": "blackguard_dec_rigged",
  "facing": "-Y",
  "space": "gltf-y-up",
  "weapons": [
    {
      "asset": "halberd",
      "bone": "bone_9",
      "rootTransform": {
        "position":   [0.247, 0.019, -0.009],
        "quaternion": [0.0, 0.0, 0.0, 1.0],
        "scale":      1.2
      },
      "attachPoint": [0.247, 0.019, -0.009],
      "tipPoint":    [0.247, 0.94, -0.009],
      "boneLocal": {
        "position":   [0.018, 0.004, -0.010],
        "quaternion": [0.0, 0.0, 0.0, 1.0],
        "scale":      1.2
      },
      "gripLocal": [0.0, 0.0, 0.0],
      "tipLocal":  [0.0, 0.92, 0.0]
    }
  ]
}
```
- **`rootTransform`** — the weapon's transform **relative to the character root** (compute `charRoot.matrixWorld⁻¹ · weapon.matrixWorld`, then decompose). `quaternion` is `[x,y,z,w]`; `scale` is one uniform number. **This is what the bridge applies — WYSIWYG.**
- **`attachPoint`** / **`tipPoint`** — the grip and tip points **resolved to character-root space** (apply the weapon's world matrix to `gripLocal` / `tipLocal`). They become the `weapon_grip` / `weapon_tip` bone heads.
- **`boneLocal`** — the same placement expressed **relative to the socket bone** (the weapon is the bone's child, so this is just its local transform). Used to reuse a "hold" as a preset across characters.
- **`gripLocal`** / **`tipLocal`** — the grip and tip points in **weapon-local space** (`[x,y,z]`).

**Whole roster** (`Export all placements`):
```json
{ "format": "sprite-motion.placements", "version": 4, "space": "gltf-y-up",
  "characters": [ { "skeleton": "...", "facing": "-Y", "weapons": [ /* blocks as above */ ] } ] }
```

Keep these names stable; the Blender bridge keys on them. Do **not** invent alternative field names.

## Self-test rig (so this builds and verifies inside Claude Design with no attachment)

When **no** character GLB is loaded, provide a **"Load demo rig"** action (toolbar + palette) that builds a **synthetic skeleton in code**: a small humanoid bone hierarchy (root → spine → shoulders → arms → a clearly-named right-hand bone, e.g. `hand.R`) using `THREE.Bone`/`THREE.Skeleton`, drawn with the same joint markers, plus a simple **box mesh as a stand-in weapon** (with grip at one end, tip at the other). Everything in this spec — bone pick, parent-to-bone, gizmo transform, grip/tip pick, snap, the 8 camera directions, silhouette, contact sheet, export — must be fully exercisable on the demo rig. This is how you confirm the tool works in the canvas; real GLBs then load through the same code paths via the file pickers.

## Visual design

Dark technical theme: near-black viewport, thin grey grid, desaturated UI chrome, a single **amber** accent for selection/active states. Grip marker amber; tip marker a distinct hue (e.g. cyan). Monospace numeric read-outs. Panels are compact, collapsible, and unobtrusive — the viewport is the star. Don't add gradients or decorative color.

## Acceptance — this build is right when

1. **Load demo rig** → click the `hand.R` joint → **Load weapon** (or the demo box) parents it to the hand; the gizmo translates/rotates/scales it relative to the bone and it stays in the hand while you orbit.
2. Setting **grip** and **tip** on the weapon places the two distinct markers; both persist through further gizmo edits.
3. The **8 camera buttons** snap an orthographic camera to the 2.5D directions; **silhouette** mode flattens to grey; **contact sheet** renders a labeled 3×3 and downloads as PNG.
4. **Snap** on: dragging the weapon near a joint snaps its grip onto that joint; **Alt** disables snap live.
5. **Save a preset**, drop the weapon on a second character, **apply preset** → identical hold.
6. **Export JSON** emits the exact schema above — `rootTransform` (real `quaternion` + `scale`), `attachPoint`, `tipPoint`, and `boneLocal`, all relative to the character root; **Export all placements** emits the roster wrapper; **Save/Load project** round-trips everything.
7. Loading a **real rigged GLB** via the file picker shows the mesh + its real bone names, and the same flow produces a correct export.

---
```
Build → Save as standalone HTML → back to Claude Code: three.js gets inlined for true-offline. The bridge (pipeline/apply_placement.py) already consumes this v4 schema — `rootTransform` + `attachPoint`/`tipPoint`, converting three.js Y-up → Blender Z-up — replacing the in-plane rotationDeg auto-orientation. Then the first real placement is rendered 8 ways and run through the cross-family render-QA jury before it's called done.
```
