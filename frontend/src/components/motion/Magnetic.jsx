import { useRef } from 'react'
import { motion, useMotionValue, useReducedMotion, useSpring } from 'framer-motion'

// Pulls its child a little toward the cursor (invites the click on the main call to action).
// Pointer position goes into motion values, so React never re-renders while the mouse moves.
export default function Magnetic({ children, strength = 0.25, className = '' }) {
  const ref = useRef(null)
  const reduce = useReducedMotion()
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const sx = useSpring(x, { stiffness: 220, damping: 16, mass: 0.4 })
  const sy = useSpring(y, { stiffness: 220, damping: 16, mass: 0.4 })

  const move = (e) => {
    if (reduce || !ref.current) return
    const r = ref.current.getBoundingClientRect()
    x.set((e.clientX - (r.left + r.width / 2)) * strength)
    y.set((e.clientY - (r.top + r.height / 2)) * strength)
  }
  const leave = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.div ref={ref} onMouseMove={move} onMouseLeave={leave} style={{ x: sx, y: sy }} className={`inline-block ${className}`}>
      {children}
    </motion.div>
  )
}
