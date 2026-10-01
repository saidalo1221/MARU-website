import { useState } from 'react'

// One collapsible question (accordion row), shared by the FAQ page, the home
// page and the product page.
export default function FaqItem({ question, answer }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-gray-200 py-3">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full justify-between items-center text-left text-sm font-medium"
        aria-expanded={open}
      >
        {question}
        <span className="text-gray-500" aria-hidden="true">{open ? '−' : '+'}</span>
      </button>
      {open && <p className="text-sm text-gray-600 mt-2 whitespace-pre-wrap">{answer}</p>}
    </div>
  )
}
