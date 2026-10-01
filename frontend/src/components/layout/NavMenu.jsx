import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

// A header dropdown: a button that reveals groups of links. Opens on click or
// keyboard (no hover, so it also works on touch screens), closes on Escape, on picking an item, and when focus leaves it, so
// it works with a keyboard and a screen reader (aria-expanded disclosure).
//
// groups: [{ heading?: string, items: [{ to, label } | { label, onClick }] }]
export default function NavMenu({ label, groups, align = 'left' }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setOpen(false)
        rootRef.current?.querySelector('button')?.focus()
      }
    }
    // Clicking anywhere outside (including another menu's button) closes this one.
    const onPointer = (e) => {
      if (!rootRef.current?.contains(e.target)) setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onPointer)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onPointer)
    }
  }, [open])

  const close = () => setOpen(false)

  return (
    <div
      ref={rootRef}
      className="relative"
      onBlur={(e) => {
        if (!rootRef.current?.contains(e.relatedTarget)) close()
      }}
    >
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 py-1"
      >
        {label}
        <span aria-hidden="true" className="text-[10px]">▾</span>
      </button>
      {open && (
        <div
          className={`absolute top-full z-50 min-w-[13rem] rounded-lg border border-gray-200 bg-white py-2 shadow-lg ${align === 'right' ? 'right-0' : 'left-0'}`}
        >
          {groups.map((group, gi) => (
            <div key={gi} className={gi > 0 ? 'mt-1 border-t border-gray-100 pt-1' : ''}>
              {group.heading && (
                <p className="px-4 pb-1 pt-1 text-xs font-semibold uppercase tracking-wide text-gray-500">{group.heading}</p>
              )}
              <ul>
                {group.items.map((item) => (
                  <li key={item.to || item.label}>
                    {item.to ? (
                      <Link to={item.to} onClick={close} className="block px-4 py-1.5 text-sm font-normal hover:bg-gray-50">
                        {item.label}
                      </Link>
                    ) : (
                      <button
                        type="button"
                        onClick={() => {
                          close()
                          item.onClick()
                        }}
                        className="block w-full px-4 py-1.5 text-left text-sm font-normal hover:bg-gray-50"
                      >
                        {item.label}
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
