# Live-run service. Runs pytest against patched workspaces, so it is treated
# as a code execution sandbox rather than an ordinary web app.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY service/requirements.txt service/requirements.txt
RUN pip install --no-cache-dir -r service/requirements.txt

COPY harness/ harness/
COPY packs/ packs/
COPY service/ service/
RUN pip install --no-cache-dir -e ./harness

# Never run patched code as root.
RUN useradd --create-home --shell /usr/sbin/nologin litmus \
    && chown -R litmus:litmus /app
USER litmus

ENV LITMUS_PACKS=/app/packs

EXPOSE 8000
CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]
