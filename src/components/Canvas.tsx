import { useRef, useEffect } from 'react'
import { useStore } from '../store'
import { toSvg, gridStep, fmt } from '../lib/projection'
import type { View } from '../lib/projection'

type Drag =
  | { kind: 'bone'; id: string; startCursor: [number, number]; startVal: [number, number] }
  | { kind: 'weapon'; id: string; startCursor: [number, number]; startVal: [number, number] }
  | { kind: 'pan'; startClient: [number, number]; startView: View }

export default function Canvas() {
  const svgRef = useRef<SVGSVGElement | null>(null)
  const drag = useRef<Drag | null>(null)

  const skeleton = useStore((s) => s.skeleton)
  const sprite = useStore((s) => s.sprite)
  const weapons = useStore((s) => s.weapons)
  const selection = useStore((s) => s.selection)
  const view = useStore((s) => s.view)
  const showGrid = useStore((s) => s.showGrid)
  const showSprite = useStore((s) => s.showSprite)
  const showLabels = useStore((s) => s.showLabels)
  const showBones = useStore((s) => s.showBones)

  const clientToSvg = (cx: number, cy: number): [number, number] => {
    const svg = svgRef.current!
    const pt = svg.createSVGPoint()
    pt.x = cx
    pt.y = cy
    const p = pt.matrixTransform(svg.getScreenCTM()!.inverse())
    return [p.x, p.y]
  }
  const cursorBone = (cx: number, cy: number): [number, number] => {
    const [sx, sy] = clientToSvg(cx, cy)
    return [sx, -sy]
  }

  const onWheel = (e: React.WheelEvent) => {
    const [mx, my] = clientToSvg(e.clientX, e.clientY)
    const f = e.deltaY > 0 ? 1.12 : 1 / 1.12
    const nw = view.w * f
    const nh = view.h * f
    useStore.getState().setView({
      x: mx - (mx - view.x) * (nw / view.w),
      y: my - (my - view.y) * (nh / view.h),
      w: nw,
      h: nh,
    })
  }

  const startBone = (e: React.PointerEvent, name: string, head: [number, number]) => {
    e.stopPropagation()
    useStore.getState().select('bone', name)
    drag.current = { kind: 'bone', id: name, startCursor: cursorBone(e.clientX, e.clientY), startVal: head }
  }
  const startWeapon = (e: React.PointerEvent, id: string, offset: [number, number]) => {
    e.stopPropagation()
    useStore.getState().select('weapon', id)
    drag.current = { kind: 'weapon', id, startCursor: cursorBone(e.clientX, e.clientY), startVal: offset }
  }
  const startPan = (e: React.PointerEvent) => {
    useStore.getState().select(null, null)
    drag.current = { kind: 'pan', startClient: [e.clientX, e.clientY], startView: view }
  }

  useEffect(() => {
    const move = (e: PointerEvent) => {
      const d = drag.current
      if (!d) return
      const st = useStore.getState()
      if (d.kind === 'pan') {
        const rect = svgRef.current!.getBoundingClientRect()
        const per = d.startView.w / rect.width
        st.setView({
          x: d.startView.x - (e.clientX - d.startClient[0]) * per,
          y: d.startView.y - (e.clientY - d.startClient[1]) * per,
          w: d.startView.w,
          h: d.startView.h,
        })
        return
      }
      const [bx, bz] = cursorBone(e.clientX, e.clientY)
      const dx = bx - d.startCursor[0]
      const dz = bz - d.startCursor[1]
      if (d.kind === 'bone') st.moveBoneHead(d.id, d.startVal[0] + dx, d.startVal[1] + dz)
      else st.updateWeapon(d.id, { offset: [d.startVal[0] + dx, d.startVal[1] + dz] })
    }
    const up = () => (drag.current = null)
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up)
    return () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', up)
    }
  }, [])

  const r = view.w * 0.009 // joint radius (scales with zoom -> ~constant on screen)
  const skelH = skeleton ? skeleton.bbox.z[1] - skeleton.bbox.z[0] : 1

  // grid
  const step = gridStep(view)
  const zTop = -view.y
  const zBot = -(view.y + view.h)
  const xLines: number[] = []
  for (let k = Math.ceil(view.x / step); k * step <= view.x + view.w; k++) xLines.push(k * step)
  const zLines: number[] = []
  for (let k = Math.ceil(zBot / step); k * step <= zTop; k++) zLines.push(k * step)

  return (
    <svg
      ref={svgRef}
      className="canvas"
      viewBox={`${view.x} ${view.y} ${view.w} ${view.h}`}
      preserveAspectRatio="xMidYMid meet"
      onWheel={onWheel}
      onPointerDown={startPan}
    >
      {/* grid */}
      {showGrid && (
        <g className="grid">
          {xLines.map((x) => (
            <line key={`x${x}`} x1={x} y1={-zTop} x2={x} y2={-zBot} className={Math.abs(x) < 1e-9 ? 'axis' : ''} vectorEffect="non-scaling-stroke" />
          ))}
          {zLines.map((z) => (
            <line key={`z${z}`} x1={view.x} y1={-z} x2={view.x + view.w} y2={-z} className={Math.abs(z) < 1e-9 ? 'axis' : ''} vectorEffect="non-scaling-stroke" />
          ))}
          {showLabels &&
            xLines.map((x) => (
              <text key={`xl${x}`} x={x} y={-zBot} dy={-view.h * 0.012} className="gridlabel" textAnchor="middle">{fmt(x)}</text>
            ))}
          {showLabels &&
            zLines.map((z) => (
              <text key={`zl${z}`} x={view.x} y={-z} dx={view.w * 0.008} dy={-view.h * 0.004} className="gridlabel">{fmt(z)}</text>
            ))}
        </g>
      )}

      {/* sprite reference */}
      {showSprite && sprite.src && (
        <image
          href={sprite.src}
          x={sprite.cx - (sprite.height * sprite.aspect) / 2}
          y={-(sprite.cz + sprite.height / 2)}
          width={sprite.height * sprite.aspect}
          height={sprite.height}
          opacity={sprite.opacity}
          style={{ pointerEvents: 'none' }}
          preserveAspectRatio="xMidYMid meet"
        />
      )}

      {/* weapons */}
      {weapons.map((w) => {
        const b = skeleton?.bones.find((bb) => bb.name === w.bone)
        if (!b) return null
        const ax = b.head[0] + w.offset[0]
        const az = b.head[2] + w.offset[1]
        const [sx, sy] = toSvg(ax, az)
        const h = w.scale * skelH
        const wd = h * w.aspect
        const ix = sx - w.anchor[0] * wd
        const iy = sy - w.anchor[1] * h
        const sel = selection.kind === 'weapon' && selection.id === w.id
        return (
          <g key={w.id} transform={`rotate(${w.rotationDeg} ${sx} ${sy})`}>
            <image href={w.src} x={ix} y={iy} width={wd} height={h} preserveAspectRatio="xMidYMid meet"
              style={{ cursor: 'grab' }} onPointerDown={(e) => startWeapon(e, w.id, w.offset)} />
            {sel && <rect x={ix} y={iy} width={wd} height={h} className="wsel" vectorEffect="non-scaling-stroke" fill="none" />}
            <circle cx={sx} cy={sy} r={r * 0.7} className="anchor" vectorEffect="non-scaling-stroke" />
          </g>
        )
      })}

      {/* skeleton */}
      {showBones && skeleton && (
        <g className="skeleton">
          {skeleton.bones.map((b) => {
            const [hx, hy] = toSvg(b.head[0], b.head[2])
            const [tx, ty] = toSvg(b.tail[0], b.tail[2])
            return <line key={`l${b.name}`} x1={hx} y1={hy} x2={tx} y2={ty} className={b.deform ? 'bone' : 'bone nondeform'} vectorEffect="non-scaling-stroke" />
          })}
          {skeleton.bones.map((b) => {
            const [hx, hy] = toSvg(b.head[0], b.head[2])
            const sel = selection.kind === 'bone' && selection.id === b.name
            return (
              <circle key={`j${b.name}`} cx={hx} cy={hy} r={sel ? r * 1.5 : r} className={`joint${sel ? ' sel' : ''}`}
                vectorEffect="non-scaling-stroke" style={{ cursor: 'grab' }}
                onPointerDown={(e) => startBone(e, b.name, [b.head[0], b.head[2]])} />
            )
          })}
        </g>
      )}
    </svg>
  )
}
