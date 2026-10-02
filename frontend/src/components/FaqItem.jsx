import { useId, useState } from 'react'

// One collapsible question (accordion row), shared by the FAQ page, the home
// page and the product page.
export default function FaqItem({ question, answer }) {
  const [open, setOpen] = useState(false)
  const panelId = useId()
  return (
    <div className="mb-3 rounded-2xl border border-gray-200 bg-gray-50 px-5 py-4">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-4 text-left text-sm font-medium"
        aria-expanded={open}
        aria-controls={panelId}
      >
        {question}
        <span className="relative flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-light text-brand" aria-hidden="true">
          <span className="absolute h-0.5 w-3 rounded bg-current" />
          <span className={`absolute h-0.5 w-3 rounded bg-current transition-transform duration-base ${open ? 'rotate-0' : 'rotate-90'}`} />
        </span>
      </button>
      <div
        id={panelId}
        aria-hidden={!open}
        className={`grid transition-[grid-template-rows] duration-base ${open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}
      >
        <div className="overflow-hidden">
          <p className="text-sm text-gray-600 pt-3 whitespace-pre-wrap">{answer}</p>
        </div>
      </div>
    </div>
  )
}
