import { Component } from 'react'
import { LocaleContext } from '../context/LocaleContext'

// Last line of defence (PRD ТЗ№2 §55): if a screen throws while rendering, show a
// plain message with a Try Again button instead of a blank page or a stack trace.
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { failed: false }
  }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  componentDidCatch(error) {
    // The console keeps the technical detail; the visitor only sees the friendly message.
    console.error('Unhandled render error', error)
  }

  render() {
    if (!this.state.failed) return this.props.children
    const t = this.context?.t || ((key) => key)
    return (
      <div role="alert" className="max-w-md mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold mb-2">{t('errors.somethingWrong')}</h1>
        <button
          type="button"
          onClick={() => {
            this.setState({ failed: false })
            window.location.reload()
          }}
          className="mt-4 bg-brand text-white px-6 py-3 rounded font-medium"
        >
          {t('errors.tryAgain')}
        </button>
      </div>
    )
  }
}

ErrorBoundary.contextType = LocaleContext
