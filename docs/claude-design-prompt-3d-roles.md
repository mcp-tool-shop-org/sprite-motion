# sprite-motion 3D — Claude Design build prompt v3 (role-tagging + canonical pose library)

> **Extends the poser.** Attach `app/sprite-motion-3d.html` and paste this prompt. The **HARD PRESERVE** list is binding. three.js stays loaded via the same importmap. Output: one self-contained HTML → back to Claude Code.

---

You are extending **sprite-motion 3D** (the per-character skeleton poser) into a **role-tagging + canonical-pose-library** tool. The goal: tag each *unique* UniRig skeleton's generic bones (`bone_N`) with canonical **roles** (`hips`, `upperArm.R`, `hand.R`…), then author reusable **poses in role space** that apply across characters with *different* skeletons. This is how the studio's combat key-poses (idle, guard, wind-up, strike, recovery, hurt) get authored ONCE and reused across all 68 characters.

This is grounded in the studio's research (`docs/posing-system-design.md`): auto-riggers emit no semantic labels so a role-map is required (F1/F2); production tools bind reusable poses via a canonical-profile + per-character name-map (Godot BoneMap, Unreal IK-Rig, Unity HumanPose — F12); poses store as per-name local rotations relative to a reference rest with a blend factor (F11); cross-rig transfer uses bind-pose-relative rotation (F4).

## HARD PRESERVE (do not break)
The 3D viewport; **FK posing** (gizmo + arrow-key rotation, double-click-select, the on-top amber highlight of the selected bone); **Skeleton / Mesh / Ghost** views + concept-reference overlay; **8-direction camera + silhouette + contact sheet**; **weapon attach** and its **v4 export** (`rootTransform`/`attachPoint`/`tipPoint`/`boneLocal`); the **pose export** (`poseForChar` — per-bone local Δ + root-relative world); the bind/rest capture (`c.rest`); **Characters / Weapons / Inspector / Presets** panels; the **command palette**; **project save/load + autosave**; the dark theme + amber accent.

## The contract (already defined — match these field names)
- **`roleProfile`** — 27 canonical roles: `hips, spine, spine2?, chest, neck, head, shoulder.{L,R}?, upperArm.{L,R}, foreArm.{L,R}, hand.{L,R}, upperLeg.{L,R}, lowerLeg.{L,R}, foot.{L,R}, toe.{L,R}?, tail?, wing.{L,R}?, fin.{L,R}?` (`?` = optional). The **required** humanoid roles are exactly the editor's demo-rig bone names.
- **`roleMap`** (per character) — `{ format:"sprite-motion.roleMap", version:1, skeleton, space:"gltf-y-up", confirmed:bool, map:{ role: boneName }, extra:{ "fingers.R":[...], ... } }`.
- **`pose`** (canonical) — `{ format:"sprite-motion.pose", version:1, name, blend, space:"role-local-delta", roles:{ role: [x,y,z,w] } }` where each quaternion is the bone's **local rotation relative to its rest** (`restQ⁻¹ · poseQ`).

## NEW v3 features

### 1. Roles panel
A collapsible **ROLES** panel listing the canonical roles grouped (Spine, Arms, Legs, Exotic), each row showing its mapped bone name or "—". A header shows `confirmed: yes/no` and a count of unmapped **required** roles (warn in amber if > 0).

### 2. Auto-propose the role map (on character load)
When a character GLB loads, auto-propose a `roleMap` from skeleton structure (no labels exist — F1):
- the root bone (no bone-parent) → **hips**;
- the chain ascending from hips along +up → **spine → (spine2) → chest → neck → head** (chest = the bone the arms branch from);
- the two symmetric branches off the chest, split by **x-sign** → right/left **arm** chains; assign by depth from chest: `(shoulder) → upperArm → foreArm → hand`;
- the two branches off hips descending → right/left **leg** chains: `upperLeg → lowerLeg → foot → (toe)`;
- everything else (fingers, tails) → **`extra`** (grouped by the chain they hang off).

Set `confirmed:false`. Render the proposal in the Roles panel. (This is the editor's heuristic; an LLM/MCP pass refines exotics later — out of scope here.)

### 3. Confirm / override roles (the human pass)
- Click a **role** row → its mapped bone highlights (reuse the on-top amber highlight); the row enters "assign" mode.
- In assign mode, **click a joint** in the viewport (or pick from a bone dropdown) → that bone is assigned to the role. A "clear" ✕ unassigns. Reassigning a bone already used by another role moves it (a role maps to one bone; warn on conflict).
- Selecting a bone shows its assigned role in the readout.
- **"Confirm roles"** sets `confirmed:true`. **Export roleMap** downloads the `sprite-motion.roleMap` JSON.

### 4. Canonical pose library
A collapsible **POSES** panel (requires a confirmed roleMap; disable with a hint otherwise).
- **Save current pose** → capture the current bone rotations as **role-keyed local Δ-quats**: for each mapped role, `delta = rest[bone].q⁻¹ · bone.quaternion`; store under the role. Name it (free text, or pick a combat-craft preset: `idle-ready / guard / anticipation / strike / recovery / hurt`). Poses live in the project.
- **Apply pose** → for each role in the pose, look up the active character's bone via its `roleMap`, set `bone.quaternion = rest[bone].q · delta`. A **blend slider [0,1]** slerps from the current (or rest) pose to the target pose. (Editor uses role-keyed local-delta apply — correct for similar-rest UniRig humanoids; the headless bridge applies the full bind-pose-relative transfer + IK for production, F4/F5.)
- **Cross-character demo** must work: load + tag a second humanoid GLB, **Apply** the same saved pose → it poses on the different skeleton via roles.
- Save / rename / delete poses; **Export pose library** downloads an array of `sprite-motion.pose` objects.

### 5. Exports + project
- Export **roleMap** (active character) and **pose library** (all poses) as separate JSON downloads, matching the contract.
- **Project save/load + autosave** must round-trip the per-character roleMaps + the pose library (alongside the existing characters/weapons/poses).

## Visual design
Match the dark theme + amber accent. The Roles panel uses the same row style as the bone list; a mapped role row shows its bone in mono; unmapped-required rows tint amber. No new accent colors.

## Acceptance — v3 is right when
1. Load the blackguard GLB → roles **auto-propose** (hips, spine…head, both arms to hand.R/.L, both legs); the Roles panel shows them; unmapped-required count shown.
2. Click **`hand.R`** → the right-hand joint highlights; reassign by clicking another joint; **Confirm roles** → **Export roleMap** emits the contract JSON with `confirmed:true`.
3. Pose with arrows, **Save** as `guard` → stored role-keyed; **Reset pose**; **Apply `guard`** → the pose returns; the **blend slider** interpolates.
4. Load a **second** humanoid GLB, auto-tag + confirm, **Apply `guard`** → it poses correctly on the different skeleton.
5. **Export roleMap + pose library** match the contract; weapon attach + v4 export still work; **Save/Load project** round-trips roles + poses.

---
```
Back in Claude Code: the roleMap + pose library feed (1) the headless bridge — apply_placement.py gains pose-application via the bind-pose-relative transfer (F4) + an IK pass for grips (F5), before weapon attach; and (2) sprite-motion-mcp — load/propose-roles/apply-pose/attach/export/render/jury, detail then batch_roster. Then motion (a keyframe timeline over named poses) layers on.
```
