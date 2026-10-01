// Site navigation shared by the header menus, the mobile menu and the footer
// (PRD ТЗ№2 §4 information architecture). Each builder takes the `t` function.

export const VOLUMES_ML = [350, 470, 800, 1000, 1900]

export function shopGroups(t) {
  return [
    {
      items: [
        { to: '/shop', label: t('header.allProducts') },
        { to: '/shop?sort=newest', label: t('header.newFeatured') },
        { to: '/#sets', label: t('header.sets') },
      ],
    },
    {
      heading: t('header.containers'),
      items: VOLUMES_ML.map((ml) => ({ to: `/shop?capacity=${ml}`, label: t('catalog.ml', { n: ml }) })),
    },
  ]
}

export function businessGroups(t) {
  return [
    {
      items: [
        { to: '/wholesale', label: t('footer.wholesale') },
        { to: '/b2b', label: t('footer.b2b') },
        { to: '/quote', label: t('footer.requestQuote') },
        { to: '/distributor', label: t('footer.distributor') },
      ],
    },
  ]
}

export function aboutGroups(t) {
  return [
    {
      items: [
        { to: '/about', label: t('header.company') },
        { to: '/manufacturing', label: t('footer.manufacturing') },
        { to: '/quality', label: t('footer.quality') },
      ],
    },
  ]
}

export function supportGroups(t) {
  return [
    {
      items: [
        { to: '/delivery', label: t('footer.delivery') },
        { to: '/payment', label: t('footer.payment') },
        { to: '/returns', label: t('footer.returns') },
        { to: '/faq', label: t('footer.faq') },
        { to: '/contact', label: t('footer.contact') },
        { to: '/track', label: t('footer.trackOrder') },
      ],
    },
  ]
}
