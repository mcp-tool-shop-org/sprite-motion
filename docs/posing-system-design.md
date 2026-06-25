# Sprite-Motion Posing System — research-grounded design

> **Status:** contract design, study-swarm-grounded (2026-06-25). The phase BEFORE motion.
> Built via the research-grounded-advisor protocol: 5 parallel research agents → synthesis → **family-different citation gate** → architecture. Every load-bearing choice traces to a verified finding by number (Fn).

## Step-4 citation gate — receipt

- **Verifier path:** `roleos verify-citations` runner not on PATH (prism 1.6.0 installed, ollama up) → used the protocol's **documented manual fallback**: retrieval oracle (mechanism-diverse) + two decorrelated non-Claude LLM families, reasoning-stripped.
- **Stage 1 — existence/attribution (retrieval oracle, WebFetch):** 16/16 load-bearing citations resolve with correct authors + year. **0 fabricated, 0 misattributed.** (arXiv:2605.27055's title was paraphrased by the source agent — real title "Semantic-Aware Motion Encoding for Topology-Agnostic Character Animation", Zhang/Cui/Liu/Wang 2026 ICML — authors/year/topic correct.)
- **Stage 2 — groundedness (DeepSeek-v3.1-671b + gpt-oss-120b):** consensus-SUPPORTED on F3,F4(impl),F5,F6,F12 (the spine); F2/F8 confirmed via title + full-abstract re-fetch; F10,F15,F16 **downgraded to their supported core** (the over-reaching quantitative specifics were dropped, not cited as load-bearing). No FABRICATED/MISATTRIBUTED → no ANDON halt.

## Research grounding (the empirical floor)

### A — Bone-role labeling (UniRig `bone_N` → roles)
1. **Every auto-rigger outputs coordinate-indexed skeletons with NO semantic labels — labeling is a known downstream gap, not an edge case.** Zhang et al. 2025 (arXiv:2504.12451, UniRig); Liu et al. 2025 (arXiv:2502.09615, RigAnything); Xu et al. 2020 (arXiv:2005.00559, RigNet). → A role-mapping step is architecturally required; no auto-rigger hands us roles.
2. **SOTA topology-agnostic animation systems use semantic TEXT labels of joints as the correspondence substrate — LLM-assigned role names are a published, benchmarked mechanism.** Gat et al. 2025 (arXiv:2502.17327, AnyTop — "Any Topology"); Zhang et al. 2026 (arXiv:2605.27055, ICML). → Auto-propose roles geometrically + an LLM-assisted labeling pass for ambiguous/exotic skeletons is grounded, not improvised.

### B — Pose retargeting math (canonical pose → unique skeleton)
3. **Classic spacetime retargeting assumes matching hierarchy + differing proportions; rest-orientation differences are NOT handled and cause drift.** Gleicher 1998 (DOI:10.1145/280814.280820). → Naive copy breaks on differing rest poses; bind-pose normalization is mandatory.
4. **The bind-pose-relative rotation-transfer formula (delta in a normalized rest frame) is the proven, low-overhead method:** `trgLocal = invBindTrgParent · bindSrcParent · srcLocal · invBindSrc · bindTrg`. upf-gti/retargeting-threejs 2022 (Apache-2.0, three.js). → Store canonical poses as local rotations relative to a canonical reference rest; the bridge applies this per bone. Commercial-safe + same stack as our editor.
5. **An intermediate canonical skeleton + IK absorbs rest-orientation AND proportion mismatch by pinning end-effectors.** Monzani et al. 2000 (DOI:10.1111/1467-8659.00393). → Add an IK pass after rotation transfer for end-effector-critical poses (weapon grip, foot plant).
6. **Deep skeleton-aware retargeting works ONLY across homeomorphic skeletons; "drastically different T-poses" (rest orientation) is its documented failure mode.** Aberman et al. 2020 (arXiv:2005.05732). → Don't rely on humanoid-only deep methods for exotics; bind-pose normalization (F4) is the floor.
7. **Residual retargeting corrects a naive copy with skeleton + shape modules — robust given a reasonable initial transfer.** Zhang et al. 2023 (arXiv:2303.08658, R2ET). → The delta-formula (F4) is the "reasonable initial copy"; residual/IK refinement layers on top.

### C — Non-humanoid / exotic species (15 of 68)
8. **Training-FREE cross-topology transfer using one/a few examples + a SPARSE bone-correspondence set; works cross-species.** Chen et al. 2025 (arXiv:2508.13139, Motion2Motion, SIGGRAPH Asia). → Per exotic species: a handful of role correspondences + a few authored examples transfers poses — no pretraining, no large dataset.
9. **Skeleton-free / part-based methods generalize only to STRUCTURALLY-ANALOGOUS parts; appendages with no source analog (tail, wing, fin) have no correspondence.** Liao et al. 2022 (arXiv:2208.00790); Hu et al. 2023 (arXiv:2306.08006). → Map the shared humanoid-analog roles; hand-author the non-shared appendages per species.
10. **Contact-aware retargeting targets diverse morphologies (supported core); multi-contact poses are a known hard case.** Cheynel et al. 2025 (arXiv:2502.21207, ReConForM). → Flag multi-contact creature stances for human review rather than full-auto.

### D — Pose-library data model
11. **Production pose libraries store poses as SPARSE per-bone-NAME local-space rotations, applied by name-match, with a [0,1] blend factor as a first-class primitive.** Blender Pose Library v2 (code.blender.org/2021/05/pose-library-v2-0/); Maya Studio Library (namespace-strip name match, github.com/krathjen/studiolibrary). → Pose = role-keyed local quaternions; blend factor built-in for partial application.
12. **The proven cross-rig binding architecture is a canonical PROFILE (named role slots + reference pose) + a per-character MAP from role → actual bone name.** Godot SkeletonProfile + BoneMap (docs.godotengine.org 4.4); Unreal IK Rig retarget chains; Unity HumanPose muscle space. → Our `roleProfile` + per-character `roleMap` is the copy-this-directly pattern. Unreal's "rotation 0,0,0 = reference pose" confirms storing deltas relative to rest.
13. **Higher-level option: store poses as named IK chains (end-effector goals) solved per-character at bind time — decouples pose intent from bone topology.** Bereznyak/Ubisoft GDC 2016 (IK Rig, shipped). → For grip/contact-critical key-poses, an IK-goal representation is more rig-robust than raw rotations (pairs with F5).

### E — Agentic MCP pipeline + bulk verification
14. **Agent-driven 3D pipelines split PLANNING from EXECUTION and use validation/simulation-in-the-loop, not one-shot codegen.** Sun et al. 2023 (arXiv:2310.12945, 3D-GPT); Yang et al. 2024 (arXiv:2402.09052, L3GO). → MCP: a planner that sequences the roster + per-character executor tools + a "validate geometry before export" tool.
15. **A render→VLM-feedback loop + a separate Critic (with a human gate) is the established robustness pattern; the Critic must be a BLOCKING gate that can trigger a retry, not a logger.** Hu et al. 2024 (arXiv:2403.01248, SceneCraft); Gao & Juluri 2026 (arXiv:2601.05016, Planner-Actor-Critic). → Our cross-family vision jury (`_rigqa.py`) is the Critic, wired as a blocking gate with a retry budget.
16. **VLM visual-QA needs EXPLICIT defect categories + a bug-free REFERENCE image to be reliable; pipelines need validation gates with idempotent partition state.** Taesiri et al. 2024 (arXiv:2312.05291, GlitchBench); Macklon & Bezemer 2025 (arXiv:2501.09236 — web-canvas domain, principle transfers); Shankar et al. 2023 (arXiv:2303.06094). → Jury prompt carries an explicit defect taxonomy + a per-character reference render; bulk run tracks per-character pass/fail state for idempotent re-runs.

## Architecture (each choice → finding)

**1. Canonical role profile + per-character role map is the durable spine.** A `roleProfile` defines named role slots + a canonical reference rest pose; each character carries a `roleMap` = {role → boneName}. This is the binding mechanism for every pose. (F12, F11)

**2. Role map is auto-proposed, then confirmed.** Geometry/hierarchy heuristics propose roles (Godot keyword-style); an **LLM-assisted labeling pass** resolves ambiguous/exotic skeletons; the human confirms/overrides in the editor. Justified because no auto-rigger emits roles (F1) and semantic text labels are the SOTA correspondence substrate (F2).

**3. Canonical poses are role-keyed local quaternions relative to the profile's reference rest; applied via bind-pose-relative transfer.** Per mapped role, the bridge applies the upf-gti delta formula (F4) so differing rest orientations are absorbed (F3, F6). A `[0,1]` blend factor is first-class (F11).

**4. End-effector-critical poses get an IK pass after rotation transfer.** Weapon grip and foot-plant are end-effector constraints; IK pins them across proportion differences (F5, F13). The existing weapon-attach (`rootTransform`/grip) is the grip end-effector.

**5. Exotic species: partial role map + sparse correspondence + per-species hand-authoring.** Map the shared humanoid-analog roles; canonical poses apply there (F8). Tails/wings/fins with no analog are hand-authored per species (F9); multi-contact stances are flagged for human review (F10). No pretraining (F8).

**6. The MCP pipeline is planner/executor split + validate-before-export + a BLOCKING jury Critic + idempotent bulk gates.** Planner sequences the roster, executors do per-character Blender work, a geometry-validate tool runs before export (F14); the cross-family jury is a blocking Critic with a retry budget (F15); its prompt carries an explicit defect taxonomy + per-character reference render, and the bulk run tracks per-character pass/fail partition state for idempotent re-runs (F16).

## The contract (durable, front-end + MCP agnostic)

```jsonc
// roleProfile.json — the canonical role set (a SkeletonProfile-equivalent). Authored once.
{
  "format": "sprite-motion.roleProfile", "version": 1,
  "roles": [
    { "role": "hips", "parent": null, "required": true },
    { "role": "spine", "parent": "hips", "required": true },
    { "role": "chest", "parent": "spine" }, { "role": "neck", "parent": "chest" }, { "role": "head", "parent": "neck" },
    { "role": "shoulder.R", "parent": "chest" }, { "role": "upperArm.R", "parent": "shoulder.R" },
    { "role": "foreArm.R", "parent": "upperArm.R" }, { "role": "hand.R", "parent": "foreArm.R" },
    // …L mirror, upperLeg/lowerLeg/foot .L/.R…
    { "role": "tail", "parent": "hips", "optional": true }, { "role": "wing.R", "parent": "chest", "optional": true }
  ]
}

// roleMap (per character) — the per-character binding. Auto-proposed, human-confirmed.
{
  "format": "sprite-motion.roleMap", "version": 1,
  "skeleton": "blackguard_dec_rigged", "space": "gltf-y-up",
  "map": { "hips": "bone_0", "spine": "bone_1", "hand.R": "bone_9", /* … */ },
  "unmapped": ["bone_34", "bone_35"]   // species extras (cape/etc.) — hand-posed
}

// pose (canonical, reusable) — role-space, relative to the profile reference rest.
{
  "format": "sprite-motion.pose", "version": 1,
  "name": "attack-windup", "blend": 1.0,
  "roles": { "spine": [x,y,z,w], "upperArm.R": [x,y,z,w], "foreArm.R": [x,y,z,w] },   // local Δ-quats vs reference rest
  "ikGoals": { "hand.R": { "space": "role", "target": [x,y,z] } }                      // optional, for grip/contact
}
```

The bridge flow: `roleMap` + `pose` → per-role bind-pose-relative transfer (F4) → optional IK (F5) → weapon attach (existing v4) → posed GLB → 8-dir render → jury Critic (F15/F16).

## Standards compliance (for the MCP-pipeline phase)

Scored against the six workflow standards (the MCP bulk pipeline is a workflow):
- **EXTERNAL_VERIFIER (3):** the cross-family vision jury (`_rigqa.py`, different model family, render-only) is the blocking Critic — grounded F15. No model verifies its own render.
- **ANDON_AUTHORITY (2→3):** jury fail halts that character's export; geometry-validate halts before export (F14). Target: per-character andon with a named retry budget.
- **NAMED_COMPENSATORS (no skip):** bulk writes posed GLBs + (later) pushes an asset repo — compensators table required before the bulk run (delete posed GLB / revert release). Owner: director-gated.
- **PIN_PER_STEP (1→2):** pin the Blender version + jury model roster + pose/roleProfile hashes per bulk run.
- **DECOMPOSE_BY_SECRETS (2):** roleProfile (stable) vs roleMap/pose (volatile) vs per-character extras (most volatile) are separate modules.
- **UNCERTAINTY_GATED_HUMANS (2):** role-map confirm + multi-contact/exotic poses gate on the human (F10); jury CANNOT_CONFIRM surfaces contrastively.

## Phasing (the Director chose contract-first)

1. **Contract** (this doc + the three schema files) — the durable spine.
2. **Editor authoring** (Claude Design): role-tagging (auto-propose + confirm) + canonical-pose author/apply, on the v4 build.
3. **Headless pose+weapon bridge** (Claude Code): `apply_placement.py` applies a roleMap+pose via F4/F5 before weapon attach.
4. **`sprite-motion-mcp`** (Claude Code, new repo in `mcp-tool-shop-org`): load/propose-roles/apply-pose/attach/export/render/jury tools; detail → `batch_roster`. Then motion (keyframe timeline) layers on.

---
*Architecture grounded in: Gleicher 1998 · Monzani et al. 2000 · Aberman et al. 2020 (2005.05732) · upf-gti retargeting-threejs · R2ET (2303.08658) · Motion2Motion (2508.13139) · AnyTop (2502.17327) · Godot SkeletonProfile/BoneMap · Blender Pose Library v2 · Bereznyak/Ubisoft GDC 2016 · 3D-GPT (2310.12945) · SceneCraft (2403.01248) · Planner-Actor-Critic (2601.05016) · GlitchBench (2312.05291) · Moving Fast With Broken Data (2303.06094). Citation gate: retrieval oracle + DeepSeek-671B + gpt-oss-120B, family-different, reasoning-stripped.*
