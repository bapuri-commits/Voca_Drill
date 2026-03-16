# Stage 1: React 빌드
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python 런타임
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY voca_drill/ voca_drill/
COPY config.yaml .
COPY --from=frontend /build/dist frontend/dist

EXPOSE 8500

CMD ["uvicorn", "voca_drill.api:app", "--host", "0.0.0.0", "--port", "8500"]
