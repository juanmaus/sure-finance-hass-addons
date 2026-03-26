ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.18
FROM $BUILD_FROM

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev

# Install runtime dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-setuptools \
    py3-wheel \
    py3-cryptography \
    py3-openssl

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Remove build dependencies
RUN apk del .build-deps

# Copy application files
COPY . /app/

# Copy rootfs (s6-overlay service definitions)
# Note: Build servers may use different contexts; copy from /app if needed
RUN if [ -d /app/rootfs ]; then \
      cp -r /app/rootfs/* /; \
    elif [ -d /app/sure-finance/rootfs ]; then \
      cp -r /app/sure-finance/rootfs/* /; \
    else \
      echo "rootfs not found in build context" && ls -la /app && exit 1; \
    fi

# Ensure proper permissions
RUN \
  if ls /etc/services.d/*/run >/dev/null 2>&1; then chmod a+x /etc/services.d/*/run; fi; \
  if ls /etc/services.d/*/finish >/dev/null 2>&1; then chmod a+x /etc/services.d/*/finish; fi

COPY run.sh /
RUN chmod a+x /run.sh

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_REF
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="Sure Finance" \
    io.hass.description="Sure Finance add-on for Home Assistant" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="Your Name <your.email@example.com>"

# Expose web interface port
EXPOSE 8099

# Set s6-overlay as the init system
ENTRYPOINT ["/run.sh"]