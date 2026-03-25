ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and required packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-setuptools \
    py3-wheel \
    py3-cryptography \
    py3-openssl \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app/

# Copy rootfs (s6-overlay service definitions)
COPY rootfs /

# Expose web interface port
EXPOSE 8099

# Set s6-overlay as the init system
ENTRYPOINT ["/init"]