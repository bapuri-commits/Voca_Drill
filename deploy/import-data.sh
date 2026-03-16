#!/bin/bash
# VPS에서 추출된 단어 데이터를 DB에 import
# 실행: ssh dev@46.250.251.82 'bash /opt/apps/voca-drill/deploy/import-data.sh'

set -e

APP_DIR="/opt/apps/voca-drill"
DATA_DIR="/opt/data/voca-drill"

cd "$APP_DIR"

echo "=== Data Import ==="

# Day 01-30 단어 import
for f in data/extracted/day_*.json; do
    if [ -f "$f" ]; then
        echo "  importing $f..."
        docker compose exec voca-drill python -m voca_drill.cli wordbank import "$f" --type toefl
    fi
done

# Review TEST import
for f in data/extracted/review_test_*.json; do
    if [ -f "$f" ]; then
        echo "  importing $f..."
        docker compose exec voca-drill python -c "
from voca_drill.data.database import init_db, get_session
from voca_drill.services.wordbank import WordBank
from voca_drill.config import load_config
cfg = load_config()
init_db(cfg['db']['path'])
wb = WordBank(get_session(cfg['db']['path']))
result = wb.import_test_json('$f')
print(f'  imported: {result}')
"
    fi
done

echo ""
echo "=== Import Complete ==="
docker compose exec voca-drill python -m voca_drill.cli wordbank chapters
