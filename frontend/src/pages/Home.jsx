import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <section className="max-w-3xl mx-auto text-center px-4 py-16">
      <h1 className="text-3xl md:text-4xl font-bold mb-4">
        Plastic food containers, made by MARU
      </h1>
      <p className="text-gray-600 mb-8">
        Polypropylene containers from 350 ml to 1900 ml, in stock and ready to ship.
      </p>
      <Link
        to="/shop"
        className="inline-block bg-brand text-white px-6 py-3 rounded font-medium hover:bg-brand-dark"
      >
        Shop Containers
      </Link>
    </section>
  )
}
