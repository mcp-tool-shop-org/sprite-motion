import { create } from 'zustand'
import type { Skeleton, Weapon, SpriteState, Selection, ToggleKey, Vec3 } from './types'
import { fitView, type View } from './lib/projection'

let wid = 0
const round = (n: number) => Math.round(n * 1e4) / 1e4

interface State {
  skeleton: Skeleton | null
  sprite: SpriteState
  weapons: Weapon[]
  selection: Selection
  view: View
  showGrid: boolean
  showSprite: boolean
  showLabels: boolean
  showBones: boolean
  loadSkeleton: (s: Skeleton) => void
  setSprite: (src: string, aspect: number) => void
  updateSprite: (p: Partial<SpriteState>) => void
  addWeapon: (asset: string, src: string, aspect: number) => void
  updateWeapon: (id: string, p: Partial<Weapon>) => void
  removeWeapon: (id: string) => void
  moveBoneHead: (name: string, x: number, z: number) => void
  select: (kind: Selection['kind'], id: string | null) => void
  setView: (v: View) => void
  toggle: (k: ToggleKey) => void
  exportPlacement: () => object
}

const defaultSprite: SpriteState = { src: null, aspect: 0.74, cx: 0, cz: 0, height: 1.3, opacity: 0.8, visible: true }

export const useStore = create<State>((set, get) => ({
  skeleton: null,
  sprite: { ...defaultSprite },
  weapons: [],
  selection: { kind: null, id: null },
  view: { x: -0.5, y: -0.7, w: 1.0, h: 1.4 },
  showGrid: true,
  showSprite: true,
  showLabels: true,
  showBones: true,

  loadSkeleton: (s) =>
    set({
      skeleton: s,
      selection: { kind: null, id: null },
      weapons: [],
      view: fitView({ x: s.bbox.x, z: s.bbox.z }),
      sprite: {
        ...get().sprite,
        cx: (s.bbox.x[0] + s.bbox.x[1]) / 2,
        cz: (s.bbox.z[0] + s.bbox.z[1]) / 2,
        height: (s.bbox.z[1] - s.bbox.z[0]) * 1.18,
      },
    }),

  setSprite: (src, aspect) => set({ sprite: { ...get().sprite, src, aspect, visible: true } }),
  updateSprite: (p) => set({ sprite: { ...get().sprite, ...p } }),

  addWeapon: (asset, src, aspect) => {
    const sk = get().skeleton
    const sel = get().selection
    const bone =
      (sel.kind === 'bone' && sel.id) ||
      sk?.bones.find((b) => /hand|wrist|bone_9$/.test(b.name))?.name ||
      sk?.bones[0]?.name ||
      'bone_0'
    const id = `w${++wid}`
    const w: Weapon = { id, asset, src, aspect, bone, offset: [0, 0], anchor: [0.5, 0.5], rotationDeg: 0, scale: 1.0 }
    set({ weapons: [...get().weapons, w], selection: { kind: 'weapon', id } })
  },
  updateWeapon: (id, p) => set({ weapons: get().weapons.map((w) => (w.id === id ? { ...w, ...p } : w)) }),
  removeWeapon: (id) =>
    set({
      weapons: get().weapons.filter((w) => w.id !== id),
      selection: get().selection.id === id ? { kind: null, id: null } : get().selection,
    }),

  moveBoneHead: (name, x, z) =>
    set((state) => {
      if (!state.skeleton) return {}
      const bones = state.skeleton.bones.map((b) => ({ ...b, head: [...b.head] as Vec3, tail: [...b.tail] as Vec3 }))
      const b = bones.find((bb) => bb.name === name)
      if (!b) return {}
      const y = b.head[1]
      b.head = [x, y, z]
      if (b.parent) {
        const p = bones.find((bb) => bb.name === b.parent)
        if (p) p.tail = [x, y, z] // keep the chain joined
      }
      return { skeleton: { ...state.skeleton, bones } }
    }),

  select: (kind, id) => set({ selection: { kind, id } }),
  setView: (v) => set({ view: v }),
  toggle: (k) => set({ [k]: !get()[k] } as Partial<State>),

  exportPlacement: () => {
    const { skeleton, sprite, weapons } = get()
    const attach = (w: Weapon): Vec3 | null => {
      const b = skeleton?.bones.find((bb) => bb.name === w.bone)
      if (!b) return null
      return [round(b.head[0] + w.offset[0]), round(b.head[1]), round(b.head[2] + w.offset[1])]
    }
    return {
      skeleton: skeleton?.name ?? null,
      facing: skeleton?.facing ?? '-Y',
      sprite: sprite.src ? { cx: round(sprite.cx), cz: round(sprite.cz), height: round(sprite.height) } : null,
      weapons: weapons.map((w) => ({
        asset: w.asset,
        bone: w.bone,
        offset: w.offset.map(round),
        rotationDeg: round(w.rotationDeg),
        scale: round(w.scale),
        attachPoint: attach(w), // resolved bone-space point the 3D rig drops the grip onto
      })),
    }
  },
}))
