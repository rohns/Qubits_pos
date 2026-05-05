# Qubits POS System v2

A complete Point of Sale system built for cyber cafés with Django REST Framework + React.

---

## What's New in v2

✅ **Security hardened** — All endpoints require authentication, expenses/sales track users  
✅ **End-of-day reports** — Print daily summary for cash reconciliation  
✅ **Sale cancellation** — Staff can void mistaken transactions  
✅ **Product management** — Add/edit services from the frontend (no Django Admin needed)  
✅ **Date range filters** — View reports for any time period  
✅ **Smart M-PESA polling** — Exponential backoff reduces server load  
✅ **Light/Dark mode** — Theme toggle with localStorage persistence  
✅ **Keyboard shortcuts** — Esc, F1, Ctrl+Enter for common actions  
✅ **Category grouping** — Services organized into collapsible sections  
✅ **Better receipts** — Formatted receipt numbers (QBS-XKM84721) instead of database IDs  

[See full changelog](CHANGELOG.md) for all 19 improvements.

---

## Quick Start

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit and set SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_services
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and login.

---

## Features

- **Fast checkout** — Click services, supports M-PESA & cash
- **Smart polling** — Exponential backoff for M-PESA status checks
- **Reports** — 6 charts with date range filters + EOD summary
- **Product management** — Staff can add/edit services in-app
- **Expense tracking** — Record and visualize operating costs
- **Void sales** — Cancel mistaken transactions by receipt number
- **Multi-user roles** — Cashier, Admin, Super Admin
- **Keyboard shortcuts** — Esc (clear), F1 (search), Ctrl+Enter (pay)
- **Light/Dark mode** — Theme toggle in header
- **Mobile responsive** — Sticky cart on small screens

---

## User Roles

| Role | Can Do |
|------|--------|
| Super Admin | Everything (Django Admin access) |
| Admin | Products tab, void sales, all reports |
| Cashier | Cashier, Reports, Expenses tabs only |

Create users via Django Admin or `python manage.py createsuperuser`.

---

## API Endpoints

All require authentication except `/auth/login/`.

**Auth:** `/api/auth/login/`, `/api/auth/refresh/`, `/api/auth/me/`  
**Products:** `/api/products/` (GET/POST/PATCH)  
**Sales:** `/api/sales/`, `/api/sales/{id}/cancel/` (staff only)  
**Payments:** `/api/payments/cash/`, `/api/payments/stk-push/`, `/api/payments/status/{id}/`  
**Reports:** `/api/reports/daily-sales/`, `/api/reports/eod-summary/?date=...`, etc.  
**Expenses:** `/api/expenses/` (GET/POST)

All report endpoints support `?from_date=` and `?to_date=` query params.

---

## M-PESA Setup

1. Get credentials from [developer.safaricom.co.ke](https://developer.safaricom.co.ke)
2. Add to `backend/.env`:
   ```
   MPESA_CONSUMER_KEY=...
   MPESA_CONSUMER_SECRET=...
   MPESA_SHORTCODE=174379
   MPESA_PASSKEY=...
   MPESA_CALLBACK_URL=https://your-domain.com/api/payments/mpesa-callback/
   ```

For testing without M-PESA, use Cash payments.

---

## Deployment

See separate deployment guide for Railway + Vercel.

**Production checklist:**
- Set `DEBUG=False`
- Generate strong `SECRET_KEY`
- Use PostgreSQL
- Set `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
- Run migrations and seed services on production

---

## Troubleshooting

**Services not loading:** Backend not running or no products → run `seed_services`  
**Login fails:** Check credentials, run `createsuperuser` if needed  
**CORS errors:** Check `CORS_ALLOWED_ORIGINS` includes frontend URL  
**M-PESA fails:** Use Cash for testing, check credentials for production  

---

## Tech Stack

**Backend:** Django 5, DRF, SimpleJWT, PostgreSQL  
**Frontend:** React 18, Vite, Recharts, React Toastify  
**Payments:** M-PESA Daraja API  

---

**Full documentation:** [CHANGELOG.md](CHANGELOG.md) · **License:** Proprietary
