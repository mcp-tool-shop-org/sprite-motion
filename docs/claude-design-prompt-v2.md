# sprite-motion v2 — Claude Design build prompt (expand the editor)

> This **extends the existing editor**. Best path: open the v1 project in Claude Design (or start a new project and **attach `app/sprite-motion.html`**) and paste this prompt so it edits the working app faithfully.
> ⚠ The shipped `app/sprite-motion.html` is ~1.5 MB (the blackguard sample sprite + halberd are embedded). For attaching to Claude Design, use **`app/sprite-motion.slim.html`** (~65 KB — identical code, the two sample images stubbed to a 1×1 placeholder; just re-upload the sprite/halberd after building). Either way, the **HARD PRESERVE** list below is binding.

---

You are extending **sprite-motion**, a single self-contained HTML editor (vanilla JS + inline SVG + CSS, no external libraries, fully offline) for placing skeletons and weapons/props onto game-character sprites in exact **bone-space** (the canvas grid *is* the rig's real coordinate numbers). Add the v2 features below **without breaking anything in v1.**

## HARD PRESERVE (do not change behavior or break)

- The bone-space SVG canvas: gridlines labeled with true coordinate values; pan (drag empty space), wheel-zoom toward cursor; the crosshair coordinate readout.
- Skeleton: load from JSON / upload `.json` / paste JSON; bones drawn `head→tail`; draggable joint circles; deform vs non-deform styling; exact `(x,y,z)` readout.
- Sprite reference layer (centre + height + opacity + show/hide), registered under the skeleton.
- Weapon placement: drag on the canvas to set offset; grip-anchor picker; offset / rotation / scale; resolved **attachPoint** in the inspector.
- The **command palette** (double-right-click or `Ctrl/⌘K`), right-click reserved for it, native menu kept in text fields.
- **Export placement JSON** with the existing schema (`skeleton`, `facing`, `sprite`, `weapons[]` each with `bone`, `offset`, `rotationDeg`, `scale`, `gripAnchor`, `attachPoint`).
- The dark technical theme, monospace coordinate readouts, and overall layout.

## NEW v2 features

### 1. Multiple characters + bulk add
- Add a left **Characters** panel (collapsible; the canvas + inspector always show the *active* character).
- A **character** = `{ skeleton, sprite, weapons[] }`. The list shows each character's name + a small thumbnail (sprite if present, else a skeleton glyph). Click to make it active; rename; remove.
- **+ Add character(s):** a file picker that accepts **multiple** skeleton `.json` files at once — each becomes a character (name from the JSON `name`, else the filename). "Add blackguard sample" adds the embedded sample as a character.
- **Bulk sprite assign:** upload multiple images at once and auto-match each to a character by **filename stem** (e.g. `goblin-warchief.front.png` → character `goblin-warchief…`); unmatched images stay in a tray to assign manually. Per-character sprite calibration is independent.
- Switching characters preserves each one's view, sprite calibration, and weapon placements.

### 2. Reusable weapon / prop library
- Add a **Library** panel (a bottom strip, or a section under Characters). Shows a thumbnail for every prop in the project.
- **+ Add prop(s):** upload one or more transparent PNGs; each becomes a library item (name from filename, e.g. `halberd`, `axe`, `spear`). Each library prop stores its image + a **default grip anchor** (`[u,v]`, set once on the prop and reused).
- **Drag a library prop onto the canvas** → creates a weapon placement on the *active* character, attached to the bone under the drop (else the default hand bone `/hand|wrist|bone_9$/`), reusing the prop's grip anchor. Also support: select a prop + "Place on selected bone".
- The library is **project-wide and reusable across all characters** (build it once: halberd, axe, spear, staff… then drop onto any character). A placed weapon references its library prop; editing offset/rotation/scale/bone is per-placement.
- Removing a prop warns if any character uses it.

### 3. Project save / load (durable work)
- **Save project** → downloads `sprite-motion.project.json` — the entire project, self-contained: all characters (skeleton + sprite calibration + weapon placements) and the library (with images embedded as data URLs + grip anchors), plus the active character. Schema below.
- **Load project** → upload a `project.json` → fully restores characters, library, placements, and active character.
- **Autosave to `localStorage`** on every change so a refresh restores the session. If the project (with embedded images) exceeds ~4 MB, skip the image-heavy autosave and toast *"Project too large to autosave — use Save project"* (file save stays the durable path). On load, if a localStorage session exists, offer **Restore previous session**.

### 4. Export updated for multiple characters
- Keep **Export placement JSON** = the *active* character (existing schema, unchanged) — this is what the Blender bridge consumes per character.
- Add **Export all placements** → `{ "format":"sprite-motion.placements", "version":2, "characters":[ { "skeleton","facing","sprite","weapons":[ … ] }, … ] }` (each character's block identical to the single-character schema). For batch bridge runs across the roster.

## Project schema (`sprite-motion.project.json`)
```json
{
  "format": "sprite-motion.project",
  "version": 2,
  "activeChar": "c1",
  "library": [
    { "id": "lib1", "name": "halberd", "src": "data:image/png;base64,…", "aspect": 0.42, "gripAnchor": [0.5, 0.6] }
  ],
  "characters": [
    {
      "id": "c1",
      "name": "blackguard_dec_rigged",
      "skeleton": { "name":"…", "facing":"-Y", "bbox":{…}, "bones":[…] },
      "sprite": { "src": "data:…", "aspect": 0.74, "cx": 0, "cz": 0, "height": 1.18, "opacity": 0.8, "visible": true },
      "weapons": [
        { "id": "w1", "libId": "lib1", "bone": "bone_9", "offset": [0.018, -0.01], "rotationDeg": 0, "scale": 1.2 }
      ]
    }
  ]
}
```
On **export placement**, resolve each weapon's `libId` → the library prop's `name` as `asset`, and emit the same per-weapon fields as v1 (including the computed `attachPoint = bone.head + [offset.x, 0, offset.z]`).

## Command palette — add these commands (keep all existing)
- `Add character(s)…`, `Add blackguard sample`, `Next character`, `Previous character`, and dynamic `Switch to: <character>` per loaded character.
- `Add prop(s) to library…`, and dynamic `Place prop: <name>` (onto the active character's selected/hand bone).
- `Save project`, `Load project`, `Export all placements`, `Restore previous session`.

## Visual design
Match the existing dark technical theme exactly (same panels, borders, amber accent `#f0a830`, monospace coordinate readouts). New panels (Characters, Library) use the same surfaces and spacing. Thumbnails are small, crisp, on dark tiles. Don't restyle the canvas or inspector.

## Acceptance — v2 is right when
1. Everything in **HARD PRESERVE** still works (load sample, place weapon, command palette, export placement with a correct `attachPoint`).
2. Add two skeleton JSONs at once → two characters in the panel; switching swaps canvas + inspector and keeps each one's placements.
3. Upload two weapon PNGs → both appear in the Library; dragging one onto a character creates a placement; the same prop drops onto a *second* character independently.
4. Save project → reload the page → Restore previous session (or Load the saved file) brings back every character, the library, and all placements intact.
5. Export all placements emits one file with a block per character, each consumable by `pipeline/apply_placement.py`.

---
