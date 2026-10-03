import { useId } from 'react'

// A labelled input with helper, error and success text and a disabled state
// (PRD §47). The label, helper and error are wired to the control for screen readers.
export default function FormField({ label, helper, error, success, className = '', as: Control = 'input', ...props }) {
  const id = useId()
  const describedBy = [helper && `${id}-help`, error && `${id}-error`, success && `${id}-ok`].filter(Boolean).join(' ') || undefined
  const border = error ? 'border-red-500' : success ? 'border-green-600' : 'border-gray-300'
  return (
    <div className={className}>
      <label htmlFor={id} className="block text-label text-gray-500 mb-1">{label}</label>
      <Control
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`w-full rounded-2xl border bg-white px-4 py-2.5 text-sm text-gray-900 disabled:bg-gray-100 disabled:text-gray-500 ${border}`}
        {...props}
      />
      {helper && <p id={`${id}-help`} className="mt-1 text-caption text-gray-500">{helper}</p>}
      {error && <p id={`${id}-error`} role="alert" className="mt-1 text-caption text-red-600">{error}</p>}
      {success && <p id={`${id}-ok`} className="mt-1 text-caption text-green-700">{success}</p>}
    </div>
  )
}
