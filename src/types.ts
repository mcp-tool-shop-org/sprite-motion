// Bone-space is 3D (x = screen-right, z = up, y = depth toward -Y front camera).
// The 2D editor works in the (x, z) front projection; y is shown numerically + carried through export.
export type Vec3 = [number, number, number]

export interface Bone {
  name: string
  parent: string | null
  head: Vec3
  tail: Vec3
  deform: boolean
}

export interface Skeleton {
  name: string
  facing: string
  bbox: { x: [number, number]; y: [number, number]; z: [number, number] }
  bones: Bone[]
}

// A reference sprite placed behind the skeleton, in bone-space (centre + height; aspect from the image).
export interface SpriteState {
  src: string | null
  aspect: number      // natural width / height
  cx: number          // bone-space x of centre
  cz: number          // bone-space z of centre
  height: number      // bone-space height the sprite spans
  opacity: number
  visible: boolean
}

// A prop placed on a bone. offset/rotation/scale are the transform the 3D rig pipeline applies.
export interface Weapon {
  id: string
  asset: string
  src: string
  aspect: number
  bone: string
  offset: [number, number]   // bone-space (x, z) from the bone head to the weapon anchor
  anchor: [number, number]   // normalised anchor point inside the image (0..1) = the grip
  rotationDeg: number        // in-plane (about depth axis)
  scale: number              // multiple of the skeleton height
}

export interface Selection { kind: 'bone' | 'weapon' | null; id: string | null }
export type ToggleKey = 'showGrid' | 'showSprite' | 'showLabels' | 'showBones'
