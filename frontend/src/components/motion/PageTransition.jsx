import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { motion, useReducedMotion } from 'framer-motion'

// Page change: the new page fades in and rises into place (about 0.45 s). The old page is replaced right away,
// so the page is never empty and the footer cannot jump (an exit animation that waits for the old page to
// leave leaves a gap that collapses the page height). Account tabs and admin pages share one key and swap
// without it; the first load and reduced motion skip it too.
const sectionKey = (pathname) => (pathname.startsWith('/account') ? '/account' : pathname.startsWith('/admin') ? '/admin' : pathname)

export default function PageTransition({ children }) {
  const { pathname } = useLocation()
  const reduce = useReducedMotion()
  const first = useRef(true)
  const isFirst = first.current

  useEffect(() => {
    first.current = false
    window.scrollTo(0, 0)
  }, [pathname])

  if (reduce) return children
  return (
    <motion.div
      key={sectionKey(pathname)}
      initial={isFirst ? false : { opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  )
}
