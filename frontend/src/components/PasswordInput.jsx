import { useState } from 'react'

// Drop-in replacement for <input type="password">: same props, adds a
// show/hide toggle. `className` styles the input; the wrapper is always
// `relative` so the toggle button can be positioned inside it.
export default function PasswordInput({ className = '', toggleLabel = 'Show password', ...props }) {
  const [visible, setVisible] = useState(false)

  return (
    <div className="relative">
      <input
        {...props}
        type={visible ? 'text' : 'password'}
        className={`${className} pr-10`}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={toggleLabel}
        tabIndex={-1}
        className="absolute right-0 top-0 h-full px-3 text-gray-400 hover:text-gray-600 text-xs font-medium"
      >
        {visible ? '🙈' : '👁'}
      </button>
    </div>
  )
}
