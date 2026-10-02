import { Link } from 'react-router-dom'

// Home hero: centred copy over a slowly scrolling strip of product photos.
// Layout follows the 21st.dev "animated marquee hero" (design.md); animation is plain CSS
// (see .maru-marquee / .maru-fade-up in index.css) so no animation library is needed.
// `images` are [{ src, alt }]; with none the hero is just the copy.
export default function MarqueeHero({ tagline, title, description, primaryCta, secondaryCta, images = [] }) {
  // Repeat a short list so one half of the track is always wider than the screen.
  const base = images.length > 0 ? Array.from({ length: Math.ceil(8 / images.length) }, () => images).flat() : []
  const track = [...base, ...base]

  return (
    <section className="relative overflow-hidden bg-brand-light">
      <div
        className={`relative z-10 max-w-3xl mx-auto px-4 text-center flex flex-col items-center ${
          base.length ? 'pt-14 pb-56 md:pt-20 md:pb-72' : 'py-16 md:py-24'
        }`}
      >
        <p
          className="maru-fade-up mb-5 inline-block rounded-full border border-brand/20 bg-white/70 px-4 py-1.5 text-sm font-medium text-gray-600"
          style={{ '--maru-delay': '0ms' }}
        >
          {tagline}
        </p>
        <h1
          className="maru-fade-up text-4xl md:text-6xl font-bold tracking-tight text-gray-900"
          style={{ '--maru-delay': '100ms' }}
        >
          {title}
        </h1>
        <p
          className="maru-fade-up mt-6 max-w-xl text-lg text-gray-600"
          style={{ '--maru-delay': '250ms' }}
        >
          {description}
        </p>
        <div
          className="maru-fade-up mt-8 flex flex-wrap justify-center gap-3"
          style={{ '--maru-delay': '400ms' }}
        >
          <Link
            to="/shop"
            className="inline-block rounded-full bg-brand px-8 py-3 font-semibold text-white shadow-lg transition hover:bg-brand-dark hover:scale-105 active:scale-95"
          >
            {primaryCta}
          </Link>
          <Link
            to="/wholesale"
            className="inline-block rounded-full border border-brand bg-white/60 px-8 py-3 font-semibold text-brand transition hover:bg-white"
          >
            {secondaryCta}
          </Link>
        </div>
      </div>

      {base.length > 0 && (
        <div
          aria-hidden="true"
          className="absolute bottom-0 left-0 w-full h-52 md:h-72 [mask-image:linear-gradient(to_bottom,transparent,black_20%,black_80%,transparent)]"
        >
          <div className="maru-marquee flex w-max gap-4">
            {track.map((img, i) => (
              <div
                key={i}
                className="h-44 md:h-60 aspect-[3/4] flex-shrink-0"
                style={{ transform: `rotate(${i % 2 === 0 ? -2 : 4}deg)` }}
              >
                <img
                  src={img.src}
                  alt=""
                  loading={i < 4 ? 'eager' : 'lazy'}
                  className="h-full w-full rounded-2xl bg-white object-contain p-3 shadow-md"
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
