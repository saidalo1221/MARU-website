import { motion, useReducedMotion } from 'framer-motion'

// Headline whose words slide up out of a mask one after another when it scrolls into view.
// The accessible name stays the full sentence; the animated words are hidden from screen readers.
const word = { hidden: { y: '115%' }, show: { y: 0, transition: { duration: 0.65, ease: [0.22, 1, 0.36, 1] } } }

export default function WordReveal({ text, className = '' }) {
  const reduce = useReducedMotion()
  const words = String(text).split(' ')
  if (reduce) return <span className={className}>{text}</span>
  return (
    <motion.span
      aria-label={text}
      className={className}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.8 }}
      transition={{ staggerChildren: 0.07 }}
    >
      {words.map((w, i) => (
        <span key={i} aria-hidden="true" className="inline-block overflow-hidden py-[0.12em] -my-[0.12em] align-bottom">
          <motion.span className="inline-block" variants={word}>{w}</motion.span>
          {i < words.length - 1 ? ' ' : ''}
        </span>
      ))}
    </motion.span>
  )
}
