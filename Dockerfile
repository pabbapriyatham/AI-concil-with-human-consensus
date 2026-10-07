FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_BASE=""
RUN npm run build -- --base=/ui/

FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ".[research]"
COPY --from=frontend /build/dist /app/frontend/dist
ENV FRONTEND_DIST_PATH=/app/frontend/dist
EXPOSE 8001
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
