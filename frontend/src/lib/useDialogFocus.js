import { useEffect } from 'react'

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

// Keeps keyboard focus inside a modal dialog and puts it back where it was when
// the dialog closes. The caller still owns Escape handling and initial focus
// (this only moves focus in if nothing inside the dialog already has it).
// Tab events are stopped at the dialog so a dialog nested in another (e.g. the
// image lightbox inside Quick View) is the only one that traps.
export default function useDialogFocus(containerRef, active = true) {
  useEffect(() => {
    const container = containerRef.current
    if (!active || !container) return undefined

    const opener = document.activeElement
    const focusables = () =>
      [...container.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null || el === document.activeElement)

    if (!container.contains(document.activeElement)) {
      const first = focusables()[0]
      if (first) first.focus()
      else {
        container.setAttribute('tabindex', '-1')
        container.focus()
      }
    }

    const onKeyDown = (e) => {
      if (e.key !== 'Tab') return
      e.stopPropagation()
      const items = focusables()
      if (items.length === 0) {
        e.preventDefault()
        return
      }
      const first = items[0]
      const last = items[items.length - 1]
      const current = document.activeElement
      if (e.shiftKey && (current === first || !container.contains(current))) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && (current === last || !container.contains(current))) {
        e.preventDefault()
        first.focus()
      }
    }
    container.addEventListener('keydown', onKeyDown)

    return () => {
      container.removeEventListener('keydown', onKeyDown)
      if (opener && typeof opener.focus === 'function' && document.contains(opener)) opener.focus()
    }
  }, [containerRef, active])
}
