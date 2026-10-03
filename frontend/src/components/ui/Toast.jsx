import { createContext, useCallback, useContext, useMemo, useState } from 'react'

// Short-lived messages (PRD §58 Toast). Wrap the app in <ToastProvider> and call
// useToast()(message, 'success' | 'error'). Rendered in a polite live region.
const ToastContext = createContext(() => {})

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const show = useCallback((message, variant = 'success') => {
    const id = `${Date.now()}-${Math.random()}`
    setToasts((list) => [...list, { id, message, variant }])
    setTimeout(() => setToasts((list) => list.filter((x) => x.id !== id)), 4000)
  }, [])

  const value = useMemo(() => show, [show])
  return (
    <ToastContext.Provider value={value}>
      {children}
      <div aria-live="polite" className="fixed bottom-4 right-4 z-[70] flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`rounded border px-4 py-2 text-sm shadow-md ${toast.variant === 'error' ? 'border-red-300 bg-red-50 text-red-800' : 'border-green-300 bg-green-50 text-green-800'}`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}
