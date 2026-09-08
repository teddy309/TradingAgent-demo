ARG HERMES_BASE_IMAGE=nousresearch/hermes-agent:latest
FROM ${HERMES_BASE_IMAGE}

USER root

RUN apt-get -o Acquire::Retries=3 update \
    && DEBIAN_FRONTEND=noninteractive apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
        dbus-x11 \
        chromium \
        fonts-dejavu-core \
        fonts-noto-cjk \
        fonts-noto-color-emoji \
        netcat-openbsd \
        novnc \
        tigervnc-standalone-server \
        tigervnc-tools \
        xdg-utils \
        websockify \
        x11-utils \
        xfce4 \
        xfce4-terminal \
    && ln -sf /usr/share/novnc/vnc.html /usr/share/novnc/index.html \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --chmod=0755 infra/sandbox/docker/cont-init.d/10-novnc-setup \
    /etc/cont-init.d/10-novnc-setup
COPY --chmod=0755 infra/sandbox/docker/s6-rc.d/xvnc/run \
    /etc/s6-overlay/s6-rc.d/xvnc/run
COPY infra/sandbox/docker/s6-rc.d/xvnc/type \
    /etc/s6-overlay/s6-rc.d/xvnc/type
COPY --chmod=0755 infra/sandbox/docker/s6-rc.d/xfce/run \
    /etc/s6-overlay/s6-rc.d/xfce/run
COPY infra/sandbox/docker/s6-rc.d/xfce/type \
    /etc/s6-overlay/s6-rc.d/xfce/type
COPY infra/sandbox/docker/s6-rc.d/xfce/dependencies.d/xvnc \
    /etc/s6-overlay/s6-rc.d/xfce/dependencies.d/xvnc
COPY --chmod=0755 infra/sandbox/docker/s6-rc.d/novnc/run \
    /etc/s6-overlay/s6-rc.d/novnc/run
COPY infra/sandbox/docker/s6-rc.d/novnc/type \
    /etc/s6-overlay/s6-rc.d/novnc/type
COPY infra/sandbox/docker/s6-rc.d/novnc/dependencies.d/xvnc \
    /etc/s6-overlay/s6-rc.d/novnc/dependencies.d/xvnc
COPY infra/sandbox/docker/s6-rc.d/user/contents.d/xvnc \
    /etc/s6-overlay/s6-rc.d/user/contents.d/xvnc
COPY infra/sandbox/docker/s6-rc.d/user/contents.d/xfce \
    /etc/s6-overlay/s6-rc.d/user/contents.d/xfce
COPY infra/sandbox/docker/s6-rc.d/user/contents.d/novnc \
    /etc/s6-overlay/s6-rc.d/user/contents.d/novnc

EXPOSE 6080 9119
