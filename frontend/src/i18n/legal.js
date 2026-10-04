// Default text for /privacy and /terms, used until an admin writes their own
// sections for those pages (Admin > Support Pages Content). Kept out of
// translations.js because it is long-form copy, not UI strings.
//
// This is a DRAFT based on what the software actually does (see START_HERE.md):
// it must be reviewed by a lawyer, and the operator's legal name, registration
// details and governing law still need to be added before launch. Contact
// details are pulled from Site Settings at render time.

export const LEGAL = {
  en: {
    updated: 'Last updated: 30 September 2026',
    contactTitle: 'Contact',
    privacy: {
      title: 'Privacy Policy',
      intro: 'This policy explains what personal data MARU collects through this website, why, who receives it, and how you can control it.',
      sections: [
        { title: 'Who we are', body: 'MARU operates this website and online shop ("we", "us"). Our contact details are at the bottom of this page.' },
        {
          title: 'What we collect',
          body:
            'Account: email address, password (stored only as a one-way hash), name, phone number and customer type.\n' +
            'Orders and delivery: name, phone, email, delivery address, company details for business orders, the items ordered and the payment method chosen. We never see or store your card number; payments are handled by the payment provider.\n' +
            'Things you save or send us: saved addresses, wishlist, reviews, items saved in your cart, quote requests, newsletter sign-up and "notify me" requests (email address).\n' +
            'Security and operation: a device identifier that lets us recognise a browser you have already verified at login, your IP address (used to limit abuse), and server logs that include a request number for troubleshooting.\n' +
            'Only if you agree: usage statistics (pages viewed, searches, cart and checkout steps), the campaign or referrer that brought you here, and your country detected from your IP address.',
        },
        {
          title: 'Why we use it',
          body:
            'To process and deliver your orders, run your account and answer your requests (performing our contract with you).\n' +
            'To keep accounting and other records the law requires.\n' +
            'To protect the shop against fraud and abuse and keep it working (our legitimate interest).\n' +
            'To send the newsletter and to use optional statistics and location detection (only with your consent, which you can withdraw at any time).',
        },
        {
          title: 'Who receives your data',
          body:
            'Payment providers (for example Payme, Click, Stripe, PayPal) to take your payment.\n' +
            'Delivery companies, to deliver your order (name, phone and address).\n' +
            'Our customer-management (CRM) and email services, to handle orders and send you messages.\n' +
            'Our hosting provider, which stores the website data.\n' +
            'A third-party IP geolocation service (ipapi.co), only if you allow location detection.\n' +
            'OpenStreetMap, whose servers see your IP address when you use the map to pick an address.\n' +
            'We do not sell your personal data.',
        },
        {
          title: 'Cookies and similar storage',
          body:
            'Essential: your login session, cart, language, currency and theme, the device identifier used for login verification, and your privacy choice. These are needed for the shop to work.\n' +
            'Optional (only with consent): campaign/referrer details and usage statistics.\n' +
            'Use "Cookie settings" in the page footer to change your choice at any time; withdrawing consent deletes the stored campaign details.',
        },
        {
          title: 'How long we keep it',
          body:
            'Order records are kept as required for accounting and legal purposes, even after your account is erased. Account data is kept until you erase your account. Newsletter sign-ups are kept so that we can honour your choice (if you unsubscribe, the address stays on file marked as unsubscribed), and "notify me" requests are kept until you erase your account or ask us to delete them. Technical logs are kept only as long as needed for security and troubleshooting.',
        },
        {
          title: 'Your rights',
          body:
            'You can download a copy of your data and erase your account yourself under Account > Privacy. Erasing deletes your profile, saved addresses, wishlist, reviews and saved data and closes your login; completed orders are kept for our records, and you cannot erase the account while an order is still in progress.\n' +
            'You can also ask us to correct your data, to stop using it, or to give you more information, and you can complain to the data-protection authority in your country. Contact us using the details below.',
        },
        {
          title: 'Security',
          body: 'Passwords are stored hashed, staff access requires a second verification step, and we limit repeated login and request attempts. No system is perfectly secure, so please keep your password private.',
        },
        { title: 'Children', body: 'This website is not intended for children, and we do not knowingly collect their data.' },
        { title: 'Changes', body: 'We will update this page when our practices change. The date above shows the latest version.' },
      ],
    },
    terms: {
      title: 'Terms of Service',
      intro: 'These terms apply to your use of this website and to orders placed through it. By using the website or placing an order you agree to them.',
      sections: [
        { title: 'Your account', body: 'Give accurate information, keep your password private, and tell us if you think your account was misused. We may suspend accounts used for abuse or fraud.' },
        { title: 'Products and prices', body: 'Prices are shown in the currency you select; conversions between currencies are indicative and the order total is shown at checkout. Stock is limited and is held for you for a short time while you complete an order. If we find a pricing or description error we may correct it or cancel the affected order and refund what you paid.' },
        { title: 'Orders', body: 'Placing an order is an offer to buy. We accept it when we confirm it to you. We may decline or cancel an order, for example if an item is unavailable, payment is not completed in time, or we suspect fraud. Unpaid orders are cancelled automatically when their stock reservation expires.' },
        { title: 'Payment', body: 'Payment is handled by the payment providers shown at checkout. We do not receive or store your card details. Amounts refunded go back through the same provider where it supports refunds.' },
        { title: 'Delivery', body: 'Delivery options, costs and estimated times are shown on the Delivery page, the product page and at checkout. Times are estimates, not guarantees. Tracking information is on your order page and on the Track Order page.' },
        { title: 'Returns and refunds', body: 'Returns and refunds are described on the Returns page, which forms part of these terms.' },
        { title: 'Business customers', body: 'Quotes are valid until the date stated in them. A quote you accept becomes an order at the quoted price. Wholesale and distributor terms are agreed with you individually.' },
        { title: 'Reviews', body: 'Reviews may be left by customers who bought the product and are checked before they are shown. Do not post unlawful, abusive or misleading content. You allow us to display the review on the website.' },
        { title: 'Acceptable use', body: 'Do not misuse the website: no attempts to break or bypass its security, no automated scraping or overloading, and no use that breaks the law.' },
        { title: 'Our content', body: 'The website, its text, images and branding belong to MARU or its licensors. You may not copy them for commercial use without our permission.' },
        { title: 'Liability', body: 'To the extent the law allows, we are not liable for indirect or consequential losses. Nothing in these terms limits liability that cannot be limited by law, or your legal rights as a consumer.' },
        { title: 'Privacy', body: 'How we handle personal data is explained in the Privacy Policy.' },
        { title: 'Changes', body: 'We may update these terms; the version on this page when you place an order applies to that order.' },
      ],
    },
  },

  ru: {
    updated: 'Последнее обновление: 30 сентября 2026',
    contactTitle: 'Контакты',
    privacy: {
      title: 'Политика конфиденциальности',
      intro: 'Эта политика объясняет, какие персональные данные MARU собирает на этом сайте, зачем, кому они передаются и как вы можете ими управлять.',
      sections: [
        { title: 'Кто мы', body: 'MARU управляет этим сайтом и интернет-магазином («мы»). Наши контактные данные указаны в конце страницы.' },
        {
          title: 'Что мы собираем',
          body:
            'Аккаунт: адрес email, пароль (хранится только в виде необратимого хеша), имя, телефон и тип клиента.\n' +
            'Заказы и доставка: имя, телефон, email, адрес доставки, данные компании для бизнес-заказов, заказанные товары и выбранный способ оплаты. Номер вашей карты мы не видим и не храним: платежи обрабатывает платёжный провайдер.\n' +
            'То, что вы сохраняете или отправляете нам: сохранённые адреса, избранное, отзывы, отложенные товары в корзине, запросы цены, подписка на рассылку и запросы «сообщить о поступлении» (адрес email).\n' +
            'Безопасность и работа сайта: идентификатор устройства, по которому мы узнаём браузер, уже подтверждённый при входе, ваш IP-адрес (для защиты от злоупотреблений) и журналы сервера с номером запроса для диагностики.\n' +
            'Только с вашего согласия: статистика использования (просмотренные страницы, поиск, шаги корзины и оформления), кампания или источник перехода на сайт и ваша страна, определённая по IP-адресу.',
        },
        {
          title: 'Зачем мы это используем',
          body:
            'Чтобы обрабатывать и доставлять заказы, вести ваш аккаунт и отвечать на запросы (исполнение договора с вами).\n' +
            'Чтобы вести учёт и другие записи, которых требует закон.\n' +
            'Чтобы защищать магазин от мошенничества и злоупотреблений и поддерживать его работу (наш законный интерес).\n' +
            'Чтобы отправлять рассылку, использовать необязательную статистику и определение местоположения (только с вашего согласия, которое можно отозвать в любой момент).',
        },
        {
          title: 'Кто получает ваши данные',
          body:
            'Платёжные провайдеры (например, Payme, Click, Stripe, PayPal) — чтобы принять оплату.\n' +
            'Службы доставки — чтобы доставить заказ (имя, телефон и адрес).\n' +
            'Наши сервисы управления клиентами (CRM) и электронной почты — для обработки заказов и отправки сообщений.\n' +
            'Наш хостинг-провайдер, где хранятся данные сайта.\n' +
            'Сторонний сервис определения местоположения по IP (ipapi.co) — только если вы разрешили определение местоположения.\n' +
            'OpenStreetMap: его серверы видят ваш IP-адрес, когда вы выбираете адрес на карте.\n' +
            'Мы не продаём ваши персональные данные.',
        },
        {
          title: 'Cookie и аналогичное хранилище',
          body:
            'Необходимые: сессия входа, корзина, язык, валюта и тема, идентификатор устройства для проверки входа и ваш выбор по конфиденциальности. Они нужны для работы магазина.\n' +
            'Необязательные (только с согласия): данные о кампании/источнике перехода и статистика использования.\n' +
            'Ссылка «Настройки cookie» внизу страницы позволяет изменить выбор в любой момент; при отзыве согласия сохранённые данные о кампании удаляются.',
        },
        {
          title: 'Как долго мы храним данные',
          body:
            'Записи о заказах хранятся столько, сколько требуется для бухгалтерского и правового учёта, даже после удаления аккаунта. Данные аккаунта хранятся, пока вы его не удалите. Подписки на рассылку сохраняются, чтобы мы могли соблюдать ваш выбор (после отписки адрес остаётся в базе с пометкой «отписан»), а запросы «сообщить о поступлении» хранятся, пока вы не удалите аккаунт или не попросите нас их удалить. Технические журналы хранятся только столько, сколько нужно для безопасности и диагностики.',
        },
        {
          title: 'Ваши права',
          body:
            'Вы можете сами скачать копию своих данных и удалить аккаунт в разделе «Аккаунт» > «Конфиденциальность». При удалении стираются профиль, сохранённые адреса, избранное, отзывы и сохранённые данные, а вход закрывается; завершённые заказы сохраняются в наших записях. Удалить аккаунт нельзя, пока есть заказ в процессе выполнения.\n' +
            'Вы также можете попросить нас исправить данные, прекратить их использование или дать больше информации, а также подать жалобу в орган по защите данных вашей страны. Свяжитесь с нами по контактам ниже.',
        },
        { title: 'Безопасность', body: 'Пароли хранятся в виде хеша, для доступа персонала требуется второй этап проверки, а повторные попытки входа и запросов ограничиваются. Ни одна система не защищена идеально, поэтому не сообщайте пароль другим.' },
        { title: 'Дети', body: 'Сайт не предназначен для детей, и мы сознательно не собираем их данные.' },
        { title: 'Изменения', body: 'Мы обновим эту страницу при изменении наших практик. Дата выше показывает последнюю версию.' },
      ],
    },
    terms: {
      title: 'Условия использования',
      intro: 'Эти условия применяются к использованию сайта и к заказам, оформленным через него. Пользуясь сайтом или оформляя заказ, вы соглашаетесь с ними.',
      sections: [
        { title: 'Ваш аккаунт', body: 'Указывайте точные данные, храните пароль в тайне и сообщайте нам, если считаете, что аккаунтом воспользовались без вашего ведома. Мы можем приостановить аккаунты, используемые для злоупотреблений или мошенничества.' },
        { title: 'Товары и цены', body: 'Цены показаны в выбранной вами валюте; пересчёт между валютами является ориентировочным, а итоговая сумма заказа показывается при оформлении. Остатки ограничены и резервируются за вами на короткое время, пока вы оформляете заказ. Если мы обнаружим ошибку в цене или описании, мы можем исправить её либо отменить затронутый заказ и вернуть оплаченные деньги.' },
        { title: 'Заказы', body: 'Оформление заказа — это предложение купить товар. Мы принимаем его, когда подтверждаем вам заказ. Мы можем отклонить или отменить заказ, например, если товара нет в наличии, оплата не завершена вовремя или мы подозреваем мошенничество. Неоплаченные заказы отменяются автоматически, когда истекает резерв товара.' },
        { title: 'Оплата', body: 'Оплату обрабатывают платёжные провайдеры, указанные при оформлении. Мы не получаем и не храним данные вашей карты. Возвращённые суммы идут через того же провайдера, если он поддерживает возвраты.' },
        { title: 'Доставка', body: 'Способы, стоимость и ориентировочные сроки доставки указаны на странице «Доставка», на странице товара и при оформлении. Сроки являются оценкой, а не гарантией. Информация об отслеживании находится на странице заказа и на странице «Отследить заказ».' },
        { title: 'Возвраты и возмещения', body: 'Возвраты и возмещения описаны на странице «Возврат», которая является частью этих условий.' },
        { title: 'Бизнес-клиенты', body: 'Предложения действуют до указанной в них даты. Принятое вами предложение становится заказом по указанной цене. Условия для оптовых покупателей и дистрибьюторов согласуются с вами индивидуально.' },
        { title: 'Отзывы', body: 'Отзывы могут оставлять покупатели, купившие товар; перед публикацией они проверяются. Не публикуйте незаконный, оскорбительный или вводящий в заблуждение контент. Вы разрешаете нам показывать отзыв на сайте.' },
        { title: 'Допустимое использование', body: 'Не злоупотребляйте сайтом: не пытайтесь взломать или обойти его защиту, не применяйте автоматический сбор данных и не перегружайте его, не используйте сайт в противоправных целях.' },
        { title: 'Наш контент', body: 'Сайт, его тексты, изображения и фирменный стиль принадлежат MARU или его лицензиарам. Без нашего разрешения их нельзя копировать в коммерческих целях.' },
        { title: 'Ответственность', body: 'В той мере, в какой это допускает закон, мы не отвечаем за косвенные и сопутствующие убытки. Ничто в этих условиях не ограничивает ответственность, которую нельзя ограничить по закону, и ваши права потребителя.' },
        { title: 'Конфиденциальность', body: 'Как мы обрабатываем персональные данные, объясняется в Политике конфиденциальности.' },
        { title: 'Изменения', body: 'Мы можем обновлять эти условия; к заказу применяется версия, действовавшая на этой странице на момент его оформления.' },
      ],
    },
  },

  uz: {
    updated: 'Oxirgi yangilanish: 2026-yil 30-sentabr',
    contactTitle: 'Aloqa',
    privacy: {
      title: 'Maxfiylik siyosati',
      intro: 'Ushbu siyosat MARU ushbu veb-saytda qanday shaxsiy ma‘lumotlarni, nima uchun yig‘ishini, ular kimga berilishini va ularni qanday boshqarishingiz mumkinligini tushuntiradi.',
      sections: [
        { title: 'Biz kimmiz', body: 'MARU ushbu veb-sayt va onlayn do‘konni yuritadi («biz»). Aloqa ma‘lumotlarimiz sahifaning pastida ko‘rsatilgan.' },
        {
          title: 'Nimalarni yig‘amiz',
          body:
            'Akkaunt: email manzil, parol (faqat qaytarib bo‘lmas xesh ko‘rinishida saqlanadi), ism, telefon va mijoz turi.\n' +
            'Buyurtmalar va yetkazib berish: ism, telefon, email, yetkazib berish manzili, biznes buyurtmalar uchun kompaniya ma‘lumotlari, buyurtma qilingan mahsulotlar va tanlangan to‘lov usuli. Karta raqamingizni biz ko‘rmaymiz va saqlamaymiz: to‘lovlarni to‘lov provayderi amalga oshiradi.\n' +
            'Siz saqlagan yoki yuborgan ma‘lumotlar: saqlangan manzillar, sevimlilar, sharhlar, savatda keyinroqqa saqlangan mahsulotlar, narx so‘rovlari, yangiliklarga obuna va «paydo bo‘lganda xabar bering» so‘rovlari (email manzil).\n' +
            'Xavfsizlik va ishlash: kirishda tasdiqlangan brauzerni taniydigan qurilma identifikatori, IP manzilingiz (suiiste‘molga qarshi) va nosozliklarni topish uchun so‘rov raqamini o‘z ichiga olgan server jurnallari.\n' +
            'Faqat roziligingiz bilan: foydalanish statistikasi (ko‘rilgan sahifalar, qidiruvlar, savat va rasmiylashtirish bosqichlari), sizni saytga olib kelgan kampaniya yoki manba hamda IP manzilingiz bo‘yicha aniqlangan davlat.',
        },
        {
          title: 'Nima uchun foydalanamiz',
          body:
            'Buyurtmalaringizni qayta ishlash va yetkazib berish, akkauntingizni yuritish va so‘rovlaringizga javob berish uchun (siz bilan shartnomani bajarish).\n' +
            'Qonun talab qiladigan hisob va boshqa yozuvlarni yuritish uchun.\n' +
            'Do‘konni firibgarlik va suiiste‘moldan himoya qilish va ishlashini ta‘minlash uchun (qonuniy manfaatimiz).\n' +
            'Yangiliklarni yuborish hamda ixtiyoriy statistika va joylashuvni aniqlashdan foydalanish uchun (faqat roziligingiz bilan; rozilikni istalgan vaqt qaytarib olishingiz mumkin).',
        },
        {
          title: 'Ma‘lumotlaringizni kim oladi',
          body:
            'To‘lov provayderlari (masalan, Payme, Click, Stripe, PayPal) — to‘lovni qabul qilish uchun.\n' +
            'Yetkazib berish kompaniyalari — buyurtmani yetkazish uchun (ism, telefon va manzil).\n' +
            'Mijozlar bilan ishlash (CRM) va elektron pochta xizmatlarimiz — buyurtmalarni qayta ishlash va xabarlar yuborish uchun.\n' +
            'Veb-sayt ma‘lumotlarini saqlaydigan xosting provayderimiz.\n' +
            'IP bo‘yicha joylashuvni aniqlaydigan uchinchi tomon xizmati (ipapi.co) — faqat joylashuvni aniqlashga ruxsat bersangiz.\n' +
            'OpenStreetMap: xaritada manzil tanlaganingizda uning serverlari IP manzilingizni ko‘radi.\n' +
            'Shaxsiy ma‘lumotlaringizni sotmaymiz.',
        },
        {
          title: 'Cookie va shunga o‘xshash saqlash',
          body:
            'Zarur: kirish sessiyasi, savat, til, valyuta va mavzu, kirishni tekshirish uchun qurilma identifikatori hamda maxfiylik tanlovingiz. Ular do‘kon ishlashi uchun kerak.\n' +
            'Ixtiyoriy (faqat rozilik bilan): kampaniya/manba ma‘lumotlari va foydalanish statistikasi.\n' +
            'Sahifa pastidagi «Cookie sozlamalari» havolasi orqali tanlovingizni istalgan vaqt o‘zgartirishingiz mumkin; rozilik qaytarib olinsa, saqlangan kampaniya ma‘lumotlari o‘chiriladi.',
        },
        {
          title: 'Ma‘lumotlar qancha saqlanadi',
          body:
            'Buyurtma yozuvlari buxgalteriya va huquqiy maqsadlar talab qilgan muddat davomida, akkaunt o‘chirilgandan keyin ham saqlanadi. Akkaunt ma‘lumotlari uni o‘chirguningizcha saqlanadi. Yangiliklarga obunalar tanlovingizni hurmat qilishimiz uchun saqlanadi (obunadan chiqsangiz, manzil «obunadan chiqqan» belgisi bilan qoladi), «paydo bo‘lganda xabar bering» so‘rovlari esa akkauntni o‘chirguningizcha yoki o‘chirishni so‘rashingizgacha saqlanadi. Texnik jurnallar faqat xavfsizlik va nosozliklarni topish uchun zarur muddat saqlanadi.',
        },
        {
          title: 'Sizning huquqlaringiz',
          body:
            '«Akkaunt» > «Maxfiylik» bo‘limida ma‘lumotlaringiz nusxasini yuklab olishingiz va akkauntni o‘zingiz o‘chirishingiz mumkin. O‘chirishda profil, saqlangan manzillar, sevimlilar, sharhlar va saqlangan ma‘lumotlar o‘chiriladi, kirish yopiladi; yakunlangan buyurtmalar yozuvlarimizda saqlanadi. Bajarilayotgan buyurtma bo‘lsa, akkauntni o‘chirib bo‘lmaydi.\n' +
            'Shuningdek, ma‘lumotlarni tuzatishni, ulardan foydalanishni to‘xtatishni yoki ko‘proq ma‘lumot berishni so‘rashingiz hamda o‘z mamlakatingizdagi ma‘lumotlarni himoya qilish organiga shikoyat qilishingiz mumkin. Quyidagi aloqa ma‘lumotlari orqali biz bilan bog‘laning.',
        },
        { title: 'Xavfsizlik', body: 'Parollar xesh ko‘rinishida saqlanadi, xodimlar kirishi uchun ikkinchi tekshiruv bosqichi talab qilinadi, takroriy kirish va so‘rov urinishlari cheklanadi. Hech bir tizim mutlaq xavfsiz emas, shuning uchun parolingizni sir saqlang.' },
        { title: 'Bolalar', body: 'Ushbu sayt bolalar uchun mo‘ljallanmagan va biz ularning ma‘lumotlarini bila turib yig‘maymiz.' },
        { title: 'O‘zgarishlar', body: 'Amaliyotimiz o‘zgarganda ushbu sahifani yangilaymiz. Yuqoridagi sana oxirgi versiyani ko‘rsatadi.' },
      ],
    },
    terms: {
      title: 'Foydalanish shartlari',
      intro: 'Ushbu shartlar saytdan foydalanishga va u orqali berilgan buyurtmalarga tegishli. Saytdan foydalanib yoki buyurtma berib, siz ularga rozilik bildirasiz.',
      sections: [
        { title: 'Akkauntingiz', body: 'To‘g‘ri ma‘lumot kiriting, parolni sir saqlang va akkauntingizdan g‘ayriqonuniy foydalanilgan deb hisoblasangiz, bizga xabar bering. Suiiste‘mol yoki firibgarlik uchun ishlatilgan akkauntlarni to‘xtatib qo‘yishimiz mumkin.' },
        { title: 'Mahsulotlar va narxlar', body: 'Narxlar siz tanlagan valyutada ko‘rsatiladi; valyutalar o‘rtasidagi hisob-kitob taxminiy, buyurtma jami esa rasmiylashtirishda ko‘rsatiladi. Zaxira cheklangan va buyurtmani rasmiylashtirayotganingizda qisqa muddatga siz uchun band qilinadi. Narx yoki tavsifda xato topsak, uni tuzatishimiz yoki tegishli buyurtmani bekor qilib, to‘langan mablag‘ni qaytarishimiz mumkin.' },
        { title: 'Buyurtmalar', body: 'Buyurtma berish — xarid qilish taklifi. Uni buyurtmani tasdiqlaganimizda qabul qilamiz. Masalan, mahsulot mavjud bo‘lmasa, to‘lov o‘z vaqtida yakunlanmasa yoki firibgarlikdan gumon qilsak, buyurtmani rad etishimiz yoki bekor qilishimiz mumkin. To‘lanmagan buyurtmalar zaxira muddati tugaganda avtomatik bekor qilinadi.' },
        { title: 'To‘lov', body: 'To‘lovni rasmiylashtirishda ko‘rsatilgan to‘lov provayderlari amalga oshiradi. Karta ma‘lumotlaringizni biz olmaymiz va saqlamaymiz. Qaytarilgan summalar, provayder qaytarishni qo‘llab-quvvatlasa, o‘sha provayder orqali qaytadi.' },
        { title: 'Yetkazib berish', body: 'Yetkazib berish usullari, narxi va taxminiy muddatlari «Yetkazib berish» sahifasida, mahsulot sahifasida va rasmiylashtirishda ko‘rsatiladi. Muddatlar taxminiy bo‘lib, kafolat emas. Kuzatuv ma‘lumotlari buyurtma sahifasida va «Buyurtmani kuzatish» sahifasida.' },
        { title: 'Qaytarish va pulni qaytarish', body: 'Qaytarish va pulni qaytarish «Qaytarish» sahifasida tavsiflangan va u ushbu shartlarning bir qismidir.' },
        { title: 'Biznes mijozlar', body: 'Takliflar unda ko‘rsatilgan sanagacha amal qiladi. Siz qabul qilgan taklif ko‘rsatilgan narxdagi buyurtmaga aylanadi. Ulgurji xaridorlar va distribyutorlar shartlari siz bilan alohida kelishiladi.' },
        { title: 'Sharhlar', body: 'Sharhlarni mahsulotni sotib olgan mijozlar qoldirishi mumkin; ular ko‘rsatilishidan oldin tekshiriladi. Noqonuniy, haqoratli yoki chalg‘ituvchi kontent joylamang. Sharhni saytda ko‘rsatishimizga ruxsat berasiz.' },
        { title: 'Ruxsat etilgan foydalanish', body: 'Saytdan suiiste‘mol qilmang: uning xavfsizligini buzishga yoki aylanib o‘tishga urinmang, avtomatik ma‘lumot yig‘maslik va uni ortiqcha yuklamaslik, qonunga zid maqsadlarda foydalanmang.' },
        { title: 'Bizning kontent', body: 'Sayt, uning matnlari, rasmlari va brendi MARU yoki uning litsenziarlariga tegishli. Ularni ruxsatimizsiz tijoriy maqsadda nusxalash mumkin emas.' },
        { title: 'Javobgarlik', body: 'Qonun ruxsat bergan darajada, biz bilvosita va oqibatli zararlar uchun javobgar emasmiz. Ushbu shartlardagi hech narsa qonun bo‘yicha cheklab bo‘lmaydigan javobgarlikni va iste‘molchi sifatidagi huquqlaringizni cheklamaydi.' },
        { title: 'Maxfiylik', body: 'Shaxsiy ma‘lumotlar bilan qanday ishlashimiz Maxfiylik siyosatida tushuntirilgan.' },
        { title: 'O‘zgarishlar', body: 'Ushbu shartlarni yangilashimiz mumkin; buyurtmaga uni bergan paytda ushbu sahifadagi versiya qo‘llanadi.' },
      ],
    },
  },
}
