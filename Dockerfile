# Backend image (FastAPI). Python 3.9 matches the production server.
# The storefront (frontend/) is a static Vite build served by the reverse proxy.
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/maru

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Admin uploads live on local disk (app/static/uploads). Mount a persistent
# volume here or they vanish on redeploy.
RUN useradd --system --no-create-home maru \
    && mkdir -p app/static/uploads \
    && chown -R maru app/static
USER maru
VOLUME ["/srv/maru/app/static/uploads"]

EXPOSE 8000

# Behind a reverse proxy, also set FORWARDED_ALLOW_IPS=<proxy ip> so rate
# limits see real client IPs (uvicorn honours proxy headers from that address).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
