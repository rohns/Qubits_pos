# Qubits POS Deployment Guide

This project is configured for:

- Backend: Railway, Django, Gunicorn, PostgreSQL
- Frontend: Vercel, React/Vite

## 1. Push the project to GitHub

Upload the full project folder to GitHub. Keep both `backend` and `frontend` folders in the same repository.

## 2. Deploy the Django backend on Railway

Create a new Railway project from GitHub and select this repository.

Use these Railway settings:

```text
Root Directory: backend
Start Command: bash start.sh
```

Add a PostgreSQL database in Railway. Railway will create `DATABASE_URL` automatically.

Add these Railway variables:

```env
SECRET_KEY=your-long-random-secret-key
DEBUG=False
ALLOWED_HOSTS=.railway.app,.up.railway.app,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
CORS_ALLOWED_ORIGIN_REGEXES=^https://.*\.vercel\.app$
CSRF_TRUSTED_ORIGINS=https://*.railway.app,https://*.up.railway.app,https://*.vercel.app
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=use-a-strong-password
MPESA_ENV=sandbox
MPESA_CONSUMER_KEY=your-key
MPESA_CONSUMER_SECRET=your-secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your-passkey
MPESA_CALLBACK_URL=https://your-backend-name.up.railway.app/api/payments/mpesa-callback/
```

The backend `start.sh` file automatically runs:

```bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_services
python manage.py create_admin_from_env
```

Therefore, you do not need to run migrations manually unless you want to.

## 3. Deploy the React frontend on Vercel

Create a new Vercel project from the same GitHub repository.

Use these Vercel settings:

```text
Root Directory: frontend
Framework Preset: Vite
Build Command: npm run build
Output Directory: dist
```

Add this Vercel environment variable:

```env
VITE_API_BASE_URL=https://your-backend-name.up.railway.app/api
```

Redeploy the frontend after adding the environment variable.

## 4. Update Railway CORS after Vercel deployment

After Vercel gives you the final frontend URL, update Railway:

```env
CORS_ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
```

You may also include local development URLs:

```env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://your-vercel-app.vercel.app
```

Redeploy Railway after changing variables.

## 5. Test production

Open:

```text
https://your-backend-name.up.railway.app/admin/
```

Login using the superuser variables you configured.

Then open your Vercel frontend and test:

1. Login
2. Services list
3. Cash payment
4. M-Pesa payment
5. Expenses
6. Reports

## 6. Important notes

If you see `Bad Request (400)`, check `ALLOWED_HOSTS`.

If frontend login fails, check `VITE_API_BASE_URL` in Vercel.

If the browser blocks requests, check `CORS_ALLOWED_ORIGINS` in Railway.

If database tables are missing, confirm that Railway PostgreSQL is attached and that `DATABASE_URL` exists.

## Report and Payment Module Fix Notes

This version includes additional fixes for report and payment deployment issues:

1. Reports now use the shared authenticated API client instead of hardcoded localhost URLs.
2. Report endpoints return safer daily expense and profit data for Railway PostgreSQL.
3. Cash payments are wrapped in a database transaction to avoid partial updates.
4. M-PESA phone numbers are normalized to Safaricom STK format.
5. M-PESA API errors now return clear messages to the frontend instead of generic failures.
6. Receipt state is preserved after successful cash or M-PESA payments.

After uploading this version, run these commands in the Railway backend shell:

```bash
python manage.py migrate
python manage.py seed_services
python manage.py collectstatic --noinput
```

Then redeploy both Railway and Vercel.
