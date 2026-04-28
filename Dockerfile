FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir build && python -m build

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    cifs-utils \
    nfs-common \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash backupuser
RUN echo "backupuser ALL=(ALL) NOPASSWD: /usr/bin/mount, /usr/bin/umount" >> /etc/sudoers

WORKDIR /app

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

RUN mkdir -p /config /var/log/backup_tool && chown backupuser:backupuser /config /var/log/backup_tool

VOLUME ["/config", "/var/log/backup_tool"]

USER backupuser

ENTRYPOINT ["backup_tool"]
CMD ["--help"]
