import { apiRequest } from './client'

// Public mirror of /admin/exchange-rates (see app/routers/exchange_rates.py)
// — not role-gated, so every admin page can convert displayed money into the
// header's selected currency regardless of which admin role is viewing it.
export function listExchangeRates() {
  return apiRequest('/exchange-rates/')
}
