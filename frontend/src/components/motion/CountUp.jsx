import { useEffect, useRef, useState } from 'react'
import { animate, useInView, useReducedMotion } from 'framer-motion'

// Counts from 0 to `to` the first time it scrolls into view (state change: the figure "arrives").
export default function CountUp({ to, duration = 1.2, className = '' }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '0px 0px -10% 0px' })
  const reduce = useReducedMotion()
  const [value, setValue] = useState(reduce ? to : 0)

  useEffect(() => {
    if (!inView || reduce) return undefined
    const controls = animate(0, to, { duration, ease: [0.16, 1, 0.3, 1], onUpdate: (v) => setValue(Math.round(v)) })
    return () => controls.stop()
  }, [inView, reduce, to, duration])

  return <span ref={ref} className={className}>{value}</span>
}
