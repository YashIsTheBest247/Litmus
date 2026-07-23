# Live-run service. Runs pytest and Node's test runner against patched
# workspaces, so it is treated as a code execution sandbox rather than an
# ordinary web app.
FROM python:3.12-slim

# The Node binary for JavaScript packs. node:20-bookworm-slim shares this image's
# Debian bookworm base, so the statically-resolvable binary runs as-is - we only
# need `node --test`, not npm. This is what lets JS packs run in the container.
COPY --from=node:20-bookworm-slim /usr/local/bin/node /usr/local/bin/node

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY service/requirements.txt service/requirements.txt
RUN pip install --no-cache-dir -r service/requirements.txt

COPY harness/ harness/
COPY packs/ packs/
COPY service/ service/
# The published report, so /report and the PDF work in the container. web/ is
# otherwise excluded by .dockerignore; the single data file is un-ignored there.
COPY web/data/report.json /app/report.json
RUN pip install --no-cache-dir -e ./harness

# Never run patched code as root.
RUN useradd --create-home --shell /usr/sbin/nologin litmus \
    && chown -R litmus:litmus /app
USER litmus

ENV LITMUS_PACKS=/app/packs \
    LITMUS_REPORT=/app/report.json

EXPOSE 8000
CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]
