import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import App from './App.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { CartProvider } from './context/CartContext.jsx'
import { LocaleProvider } from './context/LocaleContext.jsx'
import { ThemeProvider } from './context/ThemeContext.jsx'
import { ToastProvider } from './components/ui/Toast.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import '@fontsource-variable/manrope' // self-hosted; the cyrillic and latin-ext files cover ru and uz
import './index.css'
import { captureAttribution, clearAttribution } from './lib/attribution'
import { hasConsent, subscribeConsent } from './lib/consent'

captureAttribution()
// Start capturing when analytics is accepted; forget what was stored when it is withdrawn.
subscribeConsent(() => (hasConsent('analytics') ? captureAttribution() : clearAttribution()))

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <HelmetProvider>
        <BrowserRouter>
          <LocaleProvider>
            <AuthProvider>
              <CartProvider>
                <ToastProvider>
                  <ErrorBoundary>
                    <App />
                  </ErrorBoundary>
                </ToastProvider>
              </CartProvider>
            </AuthProvider>
          </LocaleProvider>
        </BrowserRouter>
      </HelmetProvider>
    </ThemeProvider>
  </React.StrictMode>
)
