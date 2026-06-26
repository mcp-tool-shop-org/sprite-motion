# Rigid-armor deform fix — posing a continuous auto-rig armor shell without candy-wrapper

> **Status:** measured on rig, 2026-06-26 (blackguard, RTX 5090 / Blender 5.0.1). The deform layer that makes
> the bridge's posed key-poses read clean. Study-swarm-grounded (run `wf_26e67746`, 2026-06-26).

## The problem

UniRig emits **standard linear-blend-skinning (LBS) weights** with no corrective branch (arXiv:2504.12451).
A posed character therefore inherits LBS's **candy-wrapper collapse** at bent/twisted joints — worst on **rigid
plate armor**, which cannot fold like skin. On the blackguard the failure concentrates at the **shoulder/deltoid**,
the **torso under spine-twist**, and the **hip under a severe fold** — the three extreme combat key-poses
(anticipation / strike / hurt) melted there while low-ROM poses (idle / recovery / guard) held.

The wave-5 stack (ROM cap ≤85° + DQS bake + uniform rigidify 0.75) fixed the **elbow** (jury 0/3 → 2/3) but left
the shoulder/torso/hip failing the reliable cross-family juror and full-res inspection.

## The fix stack (`apply_placement.py --deform-fix`, on a RAW UniRig rig)

Division of labor — **rigidify the plates, smooth the seams, never smooth the breastplate:**

1. **Cross-limb-joint SEAM mask (automatic).** A vert weighted on *both* sides of a flexing **limb** joint
   (deltoid `bone_6→7` / `bone_13→14`, elbow `7→8` / `14→15`, hip `bone_0→20` / `0→24`, knee `20→21` / `24→25`)
   is a seam vert — precisely the candy-wrapper ring. Rigid plate faces and intended spikes are single-bone, so
   they score ~0 and are protected. **Breastplate** (spine-dominated verts `bone_1/2/3`) is hard-excluded.
2. **Rigidify the PLATE FACES** toward their single dominant bone (factor 0.8), **excluding the seam rings**
   (they stay soft for the corrective) and **excluding cloth** (hips `bone_0` anchor). Plates crease, not melt.
3. **Masked Corrective Smooth on the seams** — Blender's Delta-Mush-family modifier (Mancewicz et al. 2014):
   `LENGTH_WEIGHTED`, `factor 0.6`, `iterations 12`, `scale 1.08`, `use_pin_boundary`, **`rest_source=BIND`**
   bound while the armature is at REST, masked to the seam vertex-group. Un-collapses the deltoid/hip/elbow the
   rigidify can't reach, without rounding the plate edges. (`ORCO` rest-source no-ops on this rig — use `BIND`.)
4. **DQS bake** — `Armature.use_deform_preserve_volume = True` (Kavan et al. 2008). The whole stack
   (Armature → Corrective Smooth) is baked **as a unit via a depsgraph evaluation** so the corrective keeps its
   bind rest-reference.

The **torso/breastplate** is deliberately left to rigidify-as-bands (NOT smoothed): Corrective Smooth *melts*
the rigid breastplate under twist (measured: strike rigidify-only PASSES, +CS-on-torso FAILS). Spine-twist is a
rotational artifact (Kavan's swing-twist domain) surface relaxation can't fix — see the honest ceiling below.

## Measured result (cross-family vision jury, refute-by-default, 2-of-3 consensus, rest-anchored)

All **6 key-poses** (idle / recovery / guard / anticipation / strike / hurt) pass the consensus gate. The
reliable discriminating juror **minimax-m3 passed 29/30 cells** across 5 authored poses × {front, side} × 3 runs
(`_posejury_multi.py`, K=3). Baseline-for-comparison: minimax *consistently* failed strike's shoulder and
hurt's hip was an outright consensus FAIL. The armor candy-wrapper (shoulder/hip/elbow) is **solved**; limb plate
detail (greaves/gauntlets/pauldrons) stays crisp (LENGTH_WEIGHTED preserves edge length).

## Honest ceiling (do not overclaim)

A single continuous auto-rig armor shell **cannot fold perfectly at a sharp joint** — DQS removes volume-loss
*within* a shell but cannot un-share an edge (Kavan 2008); Corrective Smooth trades a melt for a soft seam and
only cosmetically eases twist. The residual is the **soft CAPE under the most extreme twist** (anticipation side:
the swinging cape — cloth, not armor; kimi flags it 2/3, minimax passes 3/3). That is the documented
**repaint-in-post / cloth** case, not an armor-deform item. The true structural fix beyond this is procedural
plate **segmentation** (weight-gradient bisect + rigid single-bone bind + Solidify overlap collar — the only
lever that un-shares the edge; see the study-swarm synthesis) or upstream hand-modeled segmented plates.

## Run

```bash
# on a RAW UniRig rig (NOT a pre-rigidified one — --deform-fix does the rigidify):
blender -b --python pipeline/apply_placement.py -- \
  --char <raw_rigged>.glb --placement <pose>.json --out <posed>.glb --deform-fix
# tunables (proven defaults shown): --df-rigidify 0.8 --df-smooth 0.6 --df-smooth-iter 12 \
#   --df-smooth-scale 1.08 --df-rest-source BIND --df-seam-lo 0.18
```

Default (no `--deform-fix`) keeps the prior behavior byte-identical (DQS bake only; expects a pre-processed rig).

## Standards compliance (the six workflow standards)

- **EXTERNAL_VERIFIER (3):** the cross-family cloud vision jury (`_rigqa.py` / `_posejury*.py`, non-Claude
  families, render-only, refute-by-default) is the gate; no model verifies its own output. Multi-run pass-rates
  recorded. The deform recipe was *only* accepted on jury evidence, never self-certified.
- **PIN_PER_STEP (3):** every deform knob is an explicit arg with pinned defaults; Blender 5.0.1 + the rig GLB +
  the pose JSON make a bake byte-for-byte replayable. The experiment harness `_posebake.py` mirrors the bridge.
- **ANDON_AUTHORITY (2):** a jury FAIL halts promotion (this recipe was iterated, not shipped, until the reliable
  juror cleared all poses); the canary's solo flag is advisory.
- **DECOMPOSE_BY_SECRETS (2):** the deform stack is gated (`--deform-fix`, default off) and self-contained in
  `deform_fix()`, separate from the stable weapon/editor-pose paths.
- **UNCERTAINTY_GATED_HUMANS (2):** the honest-ceiling cloth/cape case is surfaced for human (repaint) review
  rather than force-passed; the residual is named, not hidden.
- **NAMED_COMPENSATORS (n/a):** no irreversible external action — bakes write local GLBs (delete to undo).

## Sources

- Mancewicz, Derksen, Rijpkema, Wilson — *Delta Mush: Smoothing Deformations While Preserving Detail* (DigiPro 2014, DOI 10.1145/2633374.2633376) — post-skin Laplacian + rest-delta removes skinning artifacts while keeping detail; Blender's Corrective Smooth implements this.
- Kavan, Collins, Žára, O'Sullivan — *Geometric Skinning with Approximate Dual Quaternion Blending* (2008, DOI 10.1145/1409625.1409627) — DQS removes the LBS candy-wrapper within a shell but cannot un-share an edge.
- Zhang et al. (VAST AI) — *One Model to Rig Them All: UniRig* (arXiv:2504.12451, SIGGRAPH 2025) — UniRig applies standard LBS weights, so posed outputs inherit LBS artifacts.
- Le, Deng — *Smooth Skinning Decomposition with Rigid Bones* (SIGGRAPH Asia 2012) — basis for binding an armor plate 100% to one bone (rigidify / segmentation).
- Blender Foundation — *Corrective Smooth Modifier* (manual + bpy API): `smooth_type`, `rest_source` (ORCO/BIND), `factor`, `iterations`, `scale`, `use_pin_boundary`, `vertex_group`; bind via `bpy.ops.object.correctivesmooth_bind`.
