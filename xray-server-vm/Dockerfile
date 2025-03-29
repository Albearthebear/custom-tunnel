FROM alpine:3.16

WORKDIR /app

# Install dependencies
RUN apk add --no-cache ca-certificates tzdata wget unzip openssl

# Create non-root user for security
RUN addgroup -S xray && adduser -S xray -G xray

# Download and install xray
RUN mkdir -p /usr/local/share/xray && \
    wget -O /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip && \
    unzip /tmp/xray.zip -d /usr/local/share/xray && \
    rm /tmp/xray.zip && \
    chmod +x /usr/local/share/xray/xray && \
    ln -s /usr/local/share/xray/xray /usr/local/bin/xray

# Create required directories
RUN mkdir -p /var/log/xray /app/certs

# Generate self-signed certificate for initial setup
RUN openssl req -x509 -newkey rsa:4096 -keyout /app/certs/privkey.pem -out /app/certs/fullchain.pem -days 365 -nodes -subj "/CN=localhost"

# Copy config file
COPY server/config.json /app/config.json

# Set proper permissions
RUN chown -R xray:xray /app /var/log/xray

# Use non-root user
USER xray

# Expose ports for the service
EXPOSE 8000
EXPOSE 8001

# Run xray
CMD ["xray", "run", "-config", "/app/config.json"] 