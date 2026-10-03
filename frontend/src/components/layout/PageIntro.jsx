// Centered title + one-line intro shared by the company, business and support pages.
export default function PageIntro({ title, subtitle, className = '' }) {
  return (
    <header className={`mb-10 text-center md:mb-12 ${className}`}>
      <h1 className="mb-3 text-3xl font-semibold tracking-tight md:text-5xl">{title}</h1>
      {subtitle && <p className="mx-auto max-w-xl text-gray-600">{subtitle}</p>}
    </header>
  )
}
