# sprite-motion 3D — Claude Design build prompt v2 (the skeleton POSER)

> **Extends the working build.** Attach `app/sprite-motion-3d.html` (the current 3D viewport, ~68 KB) and paste this prompt so Claude Design edits it. The **HARD PRESERVE** list is binding. three.js stays loaded via the same single importmap (r160, jsDelivr).
>
> Output: one self-contained HTML file (`Save as standalone HTML`) → back to Claude Code for offline-inlining + the Blender bridge.

---

You are turning **sprite-motion 3D** from a weapon-placement tool into a **per-character skeleton poser**. The real job: every character (humanoid OR monster — no fixed skeleton) is auto-rigged by UniRig into a *unique* skeleton; the artist loads that rigged GLB and **poses it** — rotating the joints/hinges, lifting an arm, closing the fingers around a grip — switching between a **skeleton view** (to see and grab the hinges) and a **mesh/sprite view** (to see how the pose reads). Weapon placement stays, but it is now *one feature of posing*. This is the foundation for **motion**: pose the rig into keyframes and you add animation to any 3D asset, not just static sprites. This iteration is **single-pose authoring** (one pose); a keyframe timeline comes later — architect for it, don't build it yet.

**The load-bearing fact:** the loaded character is a `SkinnedMesh` bound to a `Skeleton`. **Rotating a bone deforms the mesh automatically** via GPU skinning — so "posing" is literally just changing bone rotations. No retopo, no manual weights, no extra skinning code. Never assume a bone hierarchy or bone names; drive everything off the skeleton that's actually in the GLB.

## HARD PRESERVE (do not break)
The 3D viewport (orbit, lighting, grid); **Load Character / Load Weapon** (GLB file pickers); the searchable **bone list** + clickable joint markers + bone selection; **weapon attach** (parent-to-bone, the TransformControls gizmo, grip/tip pickers, snapping) and its **v4 export** (`rootTransform`, `attachPoint`, `tipPoint`, `boneLocal`, `gripLocal`, `tipLocal`, `space:"gltf-y-up"`); **Characters / Weapons-Library / Inspector / Presets** panels; the **command palette** (double-right-click / Ctrl-⌘-K); **8-direction camera + 2.5D elevation + silhouette + contact sheet**; **project save/load + autosave**; the dark technical theme with the amber accent.

## NEW v2 features

### 1. FK bone posing (the core new capability)
- **Select any bone to pose it** — click its joint marker in the viewport, or pick from the bone list. (This is the same selection you already have for sockets; now a selected bone is also *poseable*.)
- On bone-select, **attach the Rotate gizmo at the bone's head (its pivot)**. Rotating updates that bone's **local quaternion**; the `SkinnedMesh` deforms and every child bone + any weapon attached downstream follows (true forward kinematics). The **root bone** additionally allows **Translate** (to reposition/ground the whole figure).
- The Inspector shows the selected bone's name + its **local rotation as editable Euler degrees** (and a numeric readout), mirroring the gizmo.
- **Reset:** capture the GLB's bind/rest pose on load so reset is exact. Provide **"Reset bone"** (selected bone → rest) and **"Reset pose"** (all bones → rest). Both in the toolbar + palette.
- Closing a hand around a weapon is this same mechanic applied to finger bones **if the skeleton has them**; if UniRig only produced a single hand bone, you pose what exists (don't fabricate bones).
- Posing must work in **both** Skeleton and Mesh views (you watch the mesh bend as you rotate).

### 2. View system — Skeleton ↔ Mesh, plus a concept reference
- A **view toggle** (toolbar + palette + hotkey):
  - **Skeleton** — mesh hidden or ghosted to ~15% opacity so the bones + joint markers read clearly ("see the hinges").
  - **Mesh** — the posed mesh fully shaded ("what the final pose looks like"). Joint markers stay clickable so you can keep posing.
  - **Ghost** — mesh ~40% + skeleton overlaid (a middle mode: pose while seeing both).
- **Concept reference overlay:** a **"Load reference"** action takes a PNG (the character's concept art) and shows it as an **opacity-adjustable image plane** behind the character, front-aligned, with a show/hide toggle + opacity slider. This is the reference you pose against. (Front view lines it up with how the concept was authored.)
- The existing **8-direction camera, silhouette mode, and contact sheet** now preview the **posed** mesh — so the contact sheet is literally the 8-direction sprite preview of the pose. Keep the **Download contact sheet (PNG)**.

### 3. Gizmo — make it solid and obvious (fixes "I can't spin or resize")
- Modes **Move / Rotate / Scale** with an unmistakable active state **and hotkeys** (`1`/`2`/`3`, and also accept `G`/`R`/`S`). Show the current mode.
- A selected **bone** → **Rotate** is the default mode (posing); Translate allowed on the root bone; no scale on bones.
- A selected **weapon** → full **Move / Rotate / Scale** (as today).
- Keep the gizmo↔orbit separation rock-solid (orbit disabled while a gizmo handle is being dragged — the `dragging-changed` handler). Keep the gizmo handles large enough to grab; don't shrink them. Clicking empty space deselects and returns to orbit.

### 4. Weapon attach — unchanged behavior, now on the posed skeleton
Everything weapon-related stays exactly as built (attach to a bone, transform, grip/tip, snap, presets, library, the v4 export). Because a weapon is a child of its bone, **posing the arm/hand moves the weapon with it** — so you can pose the grip closed around a held weapon. Do not change the weapon export field names.

### 5. Export + project — add the pose
Add a **`pose`** block to the placement export, alongside `weapons`. Per bone that differs from rest, record both its **local rotation** (for exact editor round-trip) and its **armature-root-relative world transform** in three.js Y-up (so the Blender bridge can reproduce the pose convention-independently):
```json
"pose": {
  "space": "gltf-y-up",
  "bones": {
    "bone_5":  { "q": [0.0, 0.0, 0.131, 0.991],
                 "world": { "p": [0.18, 1.30, 0.02], "q": [0.0, 0.0, 0.131, 0.991] } },
    "bone_12": { "q": [0.07, 0.0, 0.0, 0.997],
                 "world": { "p": [0.21, 1.05, 0.00], "q": [0.05, 0.0, 0.10, 0.993] } }
  }
}
```
- `q` — the bone's **local** rotation quaternion `[x,y,z,w]` relative to its rest pose (used to restore the pose in the editor).
- `world.p` / `world.q` — the bone's **posed transform relative to the character root** (three.js Y-up; `charRoot.matrixWorld⁻¹ · bone.matrixWorld` decomposed). This is the bridge-robust form.
- Bones left at rest may be omitted. Include this `pose` block in both `Export JSON` (single) and `Export all placements` (roster, per character).
- **Project save/load + autosave must round-trip the pose** — reloading a project restores the exact bone rotations (apply the saved local `q` per bone). Weapons then sit correctly because they ride the posed bones.

### 6. Static now — architect for motion next
Keep the pose as a clean state object (bone-name → local rotation) so a later layer can hold **several named poses + a timeline** and interpolate between them into motion (idle / walk / attack). **Do not build the timeline now** — just don't structure the pose state in a way that blocks it.

## Visual design
Match the existing dark theme + amber accent exactly. Joint markers: a calm default, amber when selected/poseable. The Rotate gizmo for bones can reuse the standard three.js rings. The concept-reference plane sits behind everything at low opacity. No new accent colors, no gradients.

## Acceptance — v2 is right when
1. Load a rigged GLB → **Skeleton** view → click an arm or finger joint → the **Rotate gizmo** appears at that joint → rotating it **bends the mesh** with the bone (skinning), and child bones/weapons follow. **Reset pose** restores the rest pose exactly.
2. **View toggle** flips Skeleton / Mesh / Ghost; **Load reference** shows the concept PNG behind the character at adjustable opacity.
3. Gizmo: `1`/`2`/`3` (and `G`/`R`/`S`) switch Move/Rotate/Scale; **Rotate and Scale actually work** for both a selected bone (rotate) and a selected weapon (all three).
4. Attach a weapon, then pose the arm → the weapon **rides the hand**. Close finger bones (if present) → the grip tightens around it.
5. **8-direction contact sheet** renders the **posed** character from all 8 directions and downloads as PNG.
6. **Export JSON** emits the preserved weapon `rootTransform`/`attachPoint`/`tipPoint` **plus** the new `pose` block; **Save/Load project** round-trips the pose and the weapons exactly.

---
```
Back in Claude Code: inline three.js for true-offline, and (later, for final high-quality renders) the Blender bridge applies the pose via per-bone world transforms (pose_bone.matrix) then attaches weapons. For now the editor's own contact-sheet render is the pose preview.
```
