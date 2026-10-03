# WhatsApp message templates

WhatsApp only lets a business start a conversation with a pre-approved **template**. Create these three in
Meta Business Manager → WhatsApp Manager → Message templates, **category: Utility**, each in all three
languages (`ru`, `uz`, `en` — the language codes must match exactly). The names must be exactly as below;
approval usually takes minutes to a day. Until a template is approved, Meta refuses sends for it (the job
log shows "template not approved" and the message is not retried).

The `{{1}}`, `{{2}}`... placeholders are filled by `app/services/integrations/whatsapp.py`. Provide an example
value for each when Meta asks (e.g. Ali / MR-2026-0001 / 120.00 USD).

## `maru_order_created`  — {{1}} first name, {{2}} order number, {{3}} total with currency

- **ru**: `Здравствуйте, {{1}}! Мы получили ваш заказ {{2}} на сумму {{3}}. Сообщим, когда статус изменится. MARU`
- **uz**: `Assalomu alaykum, {{1}}! {{2}} buyurtmangiz qabul qilindi, summasi {{3}}. Holati o'zgarganda xabar beramiz. MARU`
- **en**: `Hello {{1}}! We received your order {{2}} for {{3}}. We will tell you when its status changes. MARU`

## `maru_order_status` — {{1}} first name, {{2}} order number, {{3}} new status

- **ru**: `{{1}}, статус вашего заказа {{2}} изменился: {{3}}. MARU`
- **uz**: `{{1}}, {{2}} buyurtmangiz holati o'zgardi: {{3}}. MARU`
- **en**: `{{1}}, the status of your order {{2}} changed: {{3}}. MARU`

## `maru_shipment_update` — {{1}} first name, {{2}} order number, {{3}} shipment status, {{4}} tracking number

- **ru**: `{{1}}, доставка заказа {{2}}: {{3}}. Номер отслеживания: {{4}}. MARU`
- **uz**: `{{1}}, {{2}} buyurtma yetkazib berilishi: {{3}}. Kuzatuv raqami: {{4}}. MARU`
- **en**: `{{1}}, delivery of order {{2}}: {{3}}. Tracking number: {{4}}. MARU`

## What you need to put in `.env`

```
WHATSAPP_TOKEN=<permanent system-user access token with whatsapp_business_messaging>
WHATSAPP_PHONE_NUMBER_ID=<the Phone number ID shown in WhatsApp Manager → API setup (not the phone number itself)>
```

Set up in Meta: a WhatsApp Business Account with a registered sending number, a System User (Business
Settings → Users → System users) with the WhatsApp assets assigned, and a token generated for it with the
`whatsapp_business_messaging` permission. The temporary 24-hour token on the API setup page is only for trying
it out.

## Rules the code follows

- Messages go only to customers who ticked the WhatsApp box at checkout (`orders.whatsapp_opt_in`); the box
  is shown only when WhatsApp is configured.
- The language is the site language the customer was using at checkout (`orders.language`).
- A phone number without a country code (e.g. `90 123 45 67`) is skipped, not guessed.
- With `JOBS_ASYNC=true` sends are queued and retried; a 4xx answer from Meta (e.g. template not approved) is
  not retried.
