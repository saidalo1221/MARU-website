import os
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(r'C:\Users\user\Desktop\best one yet')
OUT = Path(r'C:\Users\user\Desktop\maru-upload')
OUT.mkdir(exist_ok=True)
API = 'https://api.maruplast.uz/api/v1'

# ---- storefront
env = dict(os.environ, VITE_API_BASE_URL=API)
subprocess.run('npm run build', cwd=ROOT / 'frontend', env=env, shell=True, check=True, capture_output=True)
dist = ROOT / 'frontend' / 'dist'
HTACCESS = """# MARU storefront on Apache/LiteSpeed: https, single-page-app fallback, caching
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteCond %{HTTP:X-Forwarded-Proto} !https
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^ index.html [L]

<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType application/javascript "access plus 1 year"
  ExpiresByType font/woff2 "access plus 1 year"
</IfModule>
<FilesMatch "^(index\\.html|sw\\.js)$">
  Header set Cache-Control "no-cache"
</FilesMatch>
"""
with zipfile.ZipFile(OUT / 'storefront.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for p in dist.rglob('*'):
        if p.is_file():
            z.write(p, p.relative_to(dist).as_posix())
    z.writestr('.htaccess', HTACCESS)

# ---- backend
TEMPLATE = """# Copy this to a file named .env in the application folder and fill every value in. Never share it.
ENVIRONMENT=production
SECRET_KEY=PASTE_A_LONG_RANDOM_STRING_HERE
DATABASE_URL=mysql+pymysql://DBUSER:DBPASSWORD@localhost:3306/DBNAME
FRONTEND_URL=https://maruplast.uz
BACKEND_URL=https://api.maruplast.uz
CORS_ORIGINS=https://maruplast.uz,https://www.maruplast.uz
REDIS_URL=
JOBS_ASYNC=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_USE_TLS=true
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_CHAT_ID=
TELEGRAM_ALERT_LANG=ru
"""
skip_dirs = {'__pycache__'}
with zipfile.ZipFile(OUT / 'backend.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for p in (ROOT / 'app').rglob('*'):
        rel = p.relative_to(ROOT).as_posix()
        if p.is_dir() or skip_dirs & set(p.parts) or rel.endswith('.pyc'):
            continue
        if rel.startswith('app/static/uploads/'):
            continue  # demo photos stay behind
        z.write(p, rel)
    z.writestr('app/static/uploads/.keep', '')
    for f in ('requirements.txt', 'requirements-passenger.txt', 'passenger_wsgi.py'):
        z.write(ROOT / f, f)
    for f in ('create_admin.py', 'launch_preflight.py', 'remove_demo_data.py'):
        z.write(ROOT / 'scripts' / f, 'scripts/' + f)
    z.writestr('env-template.txt', TEMPLATE)

for f in sorted(OUT.iterdir()):
    print(f.name, round(f.stat().st_size / 1e6, 2), 'MB')
