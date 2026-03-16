#!/bin/bash
# Voca_Drill VPS 배포 스크립트
# 실행: ssh dev@46.250.251.82 'bash -s' < deploy/deploy.sh

set -e

APP_DIR="/opt/apps/voca-drill"
DATA_DIR="/opt/data/voca-drill"
ENV_FILE="/opt/envs/voca-drill.env"

echo "=== Voca_Drill Deploy ==="

# 1. 디렉토리 준비
sudo mkdir -p "$DATA_DIR"
sudo chown dev:dev "$DATA_DIR"

# 2. 환경변수 파일 (없으면 생성)
if [ ! -f "$ENV_FILE" ]; then
    echo "VOCA_DB_PATH=/app/data/voca_drill.db" | sudo tee "$ENV_FILE"
    sudo chmod 600 "$ENV_FILE"
    sudo chown dev:dev "$ENV_FILE"
    echo "  [NEW] $ENV_FILE 생성됨 - 필요하면 추가 변수 설정"
fi

# 3. 코드 가져오기
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull
else
    sudo git clone https://github.com/bapuri-commits/Voca_Drill.git "$APP_DIR"
    sudo chown -R dev:dev "$APP_DIR"
    cd "$APP_DIR"
fi

# 4. Docker 빌드 + 실행
docker compose down 2>/dev/null || true
docker compose up -d --build

# 5. nginx 설정 (최초 1회)
NGINX_CONF="/etc/nginx/sites-available/voca"
if [ ! -f "$NGINX_CONF" ]; then
    sudo cp deploy/nginx-voca.conf "$NGINX_CONF"
    sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/voca
    sudo nginx -t && sudo systemctl reload nginx
    echo "  [NEW] nginx 설정 추가됨"
fi

# 6. 확인
echo ""
echo "=== Status ==="
docker ps --filter "name=voca-drill" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "URL: https://voca.syworkspace.cloud"
echo "=== Done ==="
