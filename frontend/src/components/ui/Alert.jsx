// An inline message (PRD §58 Alert): info, success, warning or error. Errors are
// announced at once (role="alert"); the others politely (role="status").
const STYLES = {
  info: 'border-gray-200 bg-brand-light text-gray-800',
  success: 'border-green-300 bg-green-50 text-green-800',
  warning: 'border-yellow-300 bg-yellow-50 text-yellow-900',
  error: 'border-red-300 bg-red-50 text-red-800',
}

export default function Alert({ variant = 'info', className = '', children }) {
  return (
    <div
      role={variant === 'error' ? 'alert' : 'status'}
      className={`rounded-2xl border px-4 py-3 text-sm ${STYLES[variant] || STYLES.info} ${className}`}
    >
      {children}
    </div>
  )
}
