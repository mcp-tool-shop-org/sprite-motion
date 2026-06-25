// Bone-space (x right, z up) -> SVG user space. SVG y grows downward, so +z must render up:
// svg = (x, -z). The SVG viewBox is therefore expressed in these flipped coords.
export interface View { x: number; y: number; w: number; h: number }

export const toSvg = (x: number, z: number): [number, number] => [x, -z]
export const fromSvg = (sx: number, sy: number): [number, number] => [sx, -sy]

export function fitView(bbox: { x: [number, number]; z: [number, number] }, pad = 0.18): View {
  const [x0, x1] = bbox.x
  const [z0, z1] = bbox.z
  const w = x1 - x0
  const h = z1 - z0
  const px = w * pad + 0.04
  const pz = h * pad + 0.04
  // svg-y = -z: top edge corresponds to z = z1 (+pad), height spans down to z = z0 (-pad)
  return { x: x0 - px, y: -(z1 + pz), w: w + 2 * px, h: h + 2 * pz }
}

// "nice" grid step so a view shows ~8-14 lines on its larger axis
export function gridStep(view: View): number {
  const span = Math.max(view.w, view.h)
  const raw = span / 11
  const pow = Math.pow(10, Math.floor(Math.log10(raw)))
  const n = raw / pow
  const nice = n < 1.5 ? 1 : n < 3.5 ? 2 : n < 7.5 ? 5 : 10
  return nice * pow
}

export const fmt = (n: number) => (Math.abs(n) < 1e-9 ? '0' : n.toFixed(2).replace(/\.?0+$/, ''))
