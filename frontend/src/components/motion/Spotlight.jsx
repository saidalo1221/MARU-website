import { useRef } from 'react'

// A soft light that follows the cursor inside a tile. The position goes straight into CSS variables
// (no React state); the glow is a radial gradient that only fades in on hover. Children that are
// positioned (relative / absolute) paint above it.
export default function Spotlight({ children, className = '', as: Tag = 'div', color = 'rgb(255 255 255 / 0.22)' }) {
  const ref = useRef(null)
  const move = (e) => {
    const el = ref.current
    if (!el || e.pointerType === 'touch') return
    const r = el.getBoundingClientRect()
    el.style.setProperty('--sx', `${e.clientX - r.left}px`)
    el.style.setProperty('--sy', `${e.clientY - r.top}px`)
  }
  return (
    <Tag ref={ref} onPointerMove={move} className={`group/spot relative overflow-hidden ${className}`}>
      <span
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0 opacity-0 transition-opacity duration-300 group-hover/spot:opacity-100"
        style={{ background: `radial-gradient(260px circle at var(--sx, 50%) var(--sy, 50%), ${color}, transparent 70%)` }}
      />
      {children}
    </Tag>
  )
}
