import { useState } from 'react'

// One collapsible question (accordion row), shared by the FAQ page, the home
// page and the product page.
export default function FaqItem({ question, answer }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mb-3 rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-4 text-left text-sm font-medium"
        aria-expanded={open}
      >
        {question}
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-light text-brand" aria-hidden="true">{open ? '−' : '+'}</span>
      </button>
      {open && <p className="text-sm text-gray-600 mt-3 whitespace-pre-wrap">{answer}</p>}
    </div>
  )
}
