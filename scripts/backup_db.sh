#!/usr/bin/env bash
# Nightly MariaDB + uploads backup. Run from cron, e.g.:
#   15 2 * * *  /srv/maru/scripts/backup_db.sh >> /var/log/maru-backup.log 2>&1
#
# Reads credentials from the `[client]` section of ~/.maru-backup.cnf
# (chmod 600) so the password never appears in the process list:
#   [client]
#   user=maruplast
#   password=...
#   host=localhost
#
# Not run against the real server yet - test a backup AND a restore on
# staging first (see OPS_RUNBOOK.md).
set -euo pipefail

DB_NAME="${DB_NAME:-maruplast}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/maru}"
UPLOADS_DIR="${UPLOADS_DIR:-/srv/maru/app/static/uploads}"
KEEP_DAYS="${KEEP_DAYS:-14}"
CNF="${CNF:-$HOME/.maru-backup.cnf}"

stamp="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
umask 077

# --single-transaction: consistent InnoDB snapshot without locking the shop.
mysqldump --defaults-extra-file="$CNF" --single-transaction --routines --default-character-set=utf8mb4 \
  "$DB_NAME" | gzip > "$BACKUP_DIR/db-$stamp.sql.gz"

# Fail loudly on an empty/truncated dump instead of keeping a useless file.
gzip -t "$BACKUP_DIR/db-$stamp.sql.gz"

if [ -d "$UPLOADS_DIR" ]; then
  tar -czf "$BACKUP_DIR/uploads-$stamp.tar.gz" -C "$UPLOADS_DIR" .
fi

find "$BACKUP_DIR" -type f \( -name 'db-*.sql.gz' -o -name 'uploads-*.tar.gz' \) -mtime +"$KEEP_DAYS" -delete
echo "backup ok: $BACKUP_DIR/db-$stamp.sql.gz"
