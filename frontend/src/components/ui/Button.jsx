// The one button (PRD ТЗ№2 §46): primary, secondary, tertiary and danger variants,
// each with hover, active, focus-visible (global ring), loading and disabled states.
const VARIANTS = {
  primary: 'bg-brand text-white hover:bg-brand-dark active:bg-brand-dark border border-transparent',
  secondary: 'bg-white text-brand border border-brand hover:bg-brand-light active:bg-brand-light',
  tertiary: 'bg-transparent text-brand border border-transparent hover:underline active:opacity-80',
  danger: 'bg-white text-red-600 border border-red-400 hover:bg-red-50 active:bg-red-50',
}
const SIZES = {
  md: 'px-4 py-2 text-button',
  lg: 'px-6 py-3 text-button',
  sm: 'px-3 py-1.5 text-caption',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  loadingLabel,
  disabled = false,
  type = 'button',
  className = '',
  children,
  ...props
}) {
  const inactive = disabled || loading
  return (
    <button
      type={type}
      disabled={inactive}
      aria-busy={loading || undefined}
      className={`inline-flex items-center justify-center gap-2 rounded font-medium transition-colors duration-fast ${VARIANTS[variant] || VARIANTS.primary} ${SIZES[size] || SIZES.md} ${inactive ? 'opacity-40 cursor-not-allowed' : ''} ${className}`}
      {...props}
    >
      {loading && <span aria-hidden="true" className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />}
      {loading && loadingLabel ? loadingLabel : children}
    </button>
  )
}
