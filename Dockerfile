# VMESH-only MiniPool + pinned official Linux x86_64 VargaMesh Core.
FROM python:3.13-slim-trixie AS core
WORKDIR /build
COPY scripts/install_linux_core.py scripts/install_linux_core.py
RUN python3 scripts/install_linux_core.py --dest /opt/vmesh \
    && /opt/vmesh/bin/vargameshd --version

FROM python:3.13-slim-trixie
LABEL org.opencontainers.image.source="https://github.com/ati1993de/vargamesh-minipool" \
      org.opencontainers.image.description="Self-hosted VMESH-only SOLO mining with VargaMesh Core, Bitaxe Stratum V1 and 1% developer fee" \
      org.opencontainers.image.licenses="MIT"
RUN groupadd -g 10001 vmesh && useradd -u 10001 -g 10001 -m -s /usr/sbin/nologin vmesh \
    && mkdir -p /app /data /config && chown -R vmesh:vmesh /data /config
COPY --from=core /opt/vmesh /opt/vmesh
COPY --chown=vmesh:vmesh . /app
WORKDIR /app
ENV HOME=/home/vmesh XDG_CONFIG_HOME=/config PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER vmesh
VOLUME ["/data", "/config"]
EXPOSE 3938 8686
CMD ["python3", "main.py", "--docker"]
