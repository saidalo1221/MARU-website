import { motion, useReducedMotion, useScroll, useSpring } from 'framer-motion'

// A thin accent line under the header that fills as the page is read (feedback on position).
export default function ScrollProgress() {
  const reduce = useReducedMotion()
  const { scrollYProgress } = useScroll()
  const scaleX = useSpring(scrollYProgress, { stiffness: 140, damping: 30, mass: 0.4 })
  if (reduce) return null
  return (
    <motion.div
      aria-hidden="true"
      style={{ scaleX }}
      className="fixed inset-x-0 top-0 z-[60] h-0.5 origin-left bg-brand"
    />
  )
}
