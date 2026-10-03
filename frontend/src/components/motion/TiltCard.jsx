import { useRef } from 'react'
import { motion, useMotionValue, useReducedMotion, useSpring, useTransform } from 'framer-motion'

// 3D tilt toward the cursor, with a small lift. Used on product cards (hierarchy: this card is the one in focus).
export default function TiltCard({ children, max = 6, className = '' }) {
  const ref = useRef(null)
  const reduce = useReducedMotion()
  const px = useMotionValue(0.5)
  const py = useMotionValue(0.5)
  const rotateY = useSpring(useTransform(px, [0, 1], [-max, max]), { stiffness: 200, damping: 20 })
  const rotateX = useSpring(useTransform(py, [0, 1], [max, -max]), { stiffness: 200, damping: 20 })

  const move = (e) => {
    if (reduce || !ref.current || e.pointerType === 'touch') return
    const r = ref.current.getBoundingClientRect()
    px.set((e.clientX - r.left) / r.width)
    py.set((e.clientY - r.top) / r.height)
  }
  const leave = () => {
    px.set(0.5)
    py.set(0.5)
  }

  return (
    <motion.div
      ref={ref}
      onPointerMove={move}
      onPointerLeave={leave}
      style={reduce ? undefined : { rotateX, rotateY, transformPerspective: 900 }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
