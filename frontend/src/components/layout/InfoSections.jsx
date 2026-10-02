// Admin-editable text sections as soft panels: title on the left, text on the right (stacked on phones).
// sections: [{ id, title, body }]
export default function InfoSections({ sections, className = '' }) {
  if (!sections?.length) return null
  return (
    <div className={`space-y-4 ${className}`}>
      {sections.map((s) => (
        <section key={s.id} className="grid gap-3 rounded-3xl border border-gray-200 bg-gray-50 p-6 md:grid-cols-[1fr_2fr] md:gap-10 md:p-8">
          <h2 className="text-lg font-semibold">{s.title}</h2>
          <p className="whitespace-pre-wrap text-gray-600">{s.body}</p>
        </section>
      ))}
    </div>
  )
}
