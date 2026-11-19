# 서빙 이미지 — ONNX 런타임만 넣는다(scikit-learn 없음). 빌드 문맥은 저장소 루트.
FROM python:3.12.16-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-default-groups --no-install-project
COPY paperclf/ paperclf/
COPY api/app.py api/guard.py api/prediction_log.py api/__init__.py api/
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} MODEL_IMPL=onnx MODEL_DIR=/models/current PATH=/app/.venv/bin:$PATH
RUN useradd --system --uid 10001 app
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/health')"
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080"]
