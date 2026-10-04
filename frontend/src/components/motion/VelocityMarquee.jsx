import { useRef } from 'react'
import { motion, useAnimationFrame, useMotionValue, useReducedMotion, useScroll, useSpring, useTransform, useVelocity } from 'framer-motion'

// A band of large text that drifts on its own and speeds up (and can reverse) with the page's scroll speed.
// `base` is the drift in percent of one text copy per second; a negative number moves left.
// `outline` draws the letters as an outline instead of solid. Static under reduced motion.
const wrap = (min, max, v) => {
  const range = max - min
  return ((((v - min) % range) + range) % range) + min
}

export default function VelocityMarquee({ items, base = -3, outline = false, className = '' }) {
  const reduce = useReducedMotion()
  const x = useMotionValue(0)
  const { scrollY } = useScroll()
  const velocity = useSpring(useVelocity(scrollY), { damping: 50, stiffness: 400 })
  const boost = useTransform(velocity, [0, 1000], [0, 5], { clamp: false })
  const direction = useRef(base < 0 ? -1 : 1)
  const offset = useTransform(x, (v) => `${wrap(-50, 0, v)}%`)

  useAnimationFrame((_t, delta) => {
    if (reduce) return
    const b = boost.get()
    if (b < -0.05) direction.current = base < 0 ? 1 : -1 // scrolling up reverses the band
    else if (b > 0.05) direction.current = base < 0 ? -1 : 1
    const step = Math.abs(base) * (delta / 1000) * (1 + Math.abs(b))
    x.set(x.get() + direction.current * step)
  })

  // Each half has to be wider than the screen, so the items repeat inside it.
  const half = (key) => (
    <span key={key} className="flex shrink-0 items-center">
      {[...items, ...items, ...items].map((text, i) => (
        <span key={i} className="flex items-center">
          <span className={outline ? '[-webkit-text-fill-color:transparent] [-webkit-text-stroke:1.5px_currentColor]' : ''}>{text}</span>
          <span aria-hidden="true" className="mx-6 inline-block h-3 w-3 shrink-0 rounded-full bg-brand md:mx-10 md:h-4 md:w-4" />
        </span>
      ))}
    </span>
  )

  return (
    <div aria-hidden="true" className={`overflow-hidden whitespace-nowrap ${className}`}>
      <motion.div style={{ x: offset }} className="flex w-max">
        {half('a')}
        {half('b')}
      </motion.div>
    </div>
  )
}
