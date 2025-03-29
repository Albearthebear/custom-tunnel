#!/bin/sh
# Alpine Linux VM setup script for Custom Tunnel with optimized gaming performance

# Update system packages
apk update
apk upgrade

# Install Docker and Docker Compose
apk add --no-cache docker docker-compose certbot openssl curl

# Configure system for lower latency
cat > /etc/sysctl.d/99-network-tuning.conf << EOF
# Increase the maximum memory buffer sizes
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# Increase the default receive/transmit buffer sizes
net.core.rmem_default = 1048576
net.core.wmem_default = 1048576

# Increase the TCP buffer sizes
net.ipv4.tcp_rmem = 4096 1048576 16777216
net.ipv4.tcp_wmem = 4096 1048576 16777216

# Enable TCP Fast Open
net.ipv4.tcp_fastopen = 3

# Enable BBR congestion control algorithm
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# Decrease latency
net.ipv4.tcp_low_latency = 1
EOF

# Apply system changes
sysctl -p /etc/sysctl.d/99-network-tuning.conf

# Create tunnel directory
mkdir -p /opt/custom-tunnel
cd /opt/custom-tunnel

# Create certs directory
mkdir -p /opt/custom-tunnel/certs

# Generate strong DH parameters (for perfect forward secrecy)
openssl dhparam -out /opt/custom-tunnel/certs/dhparam.pem 2048

# Create docker-compose.yml with volume mount for certs
cat > /opt/custom-tunnel/docker-compose.yml << EOF
version: '3'
services:
  xray:
    build: .
    restart: always
    ports:
      - "8000:8000"
      - "8001:8001"
    volumes:
      - ./certs:/app/certs
    network_mode: "host"
EOF

# Create init script for the service
cat > /etc/init.d/custom-tunnel << 'EOF'
#!/sbin/openrc-run

name="custom-tunnel"
description="Custom Tunnel Service"
command="/usr/bin/docker-compose"
directory="/opt/custom-tunnel"
command_args="up -d"
command_background="yes"
pidfile="/run/${RC_SVCNAME}.pid"
command_user="root:root"
depend() {
  need net docker
  after firewall
}
stop() {
  ebegin "Stopping ${name}"
  cd "${directory}" && /usr/bin/docker-compose down
  eend $?
}
EOF

# Make the init script executable
chmod +x /etc/init.d/custom-tunnel

# Enable the service at boot
rc-update add docker boot
rc-update add custom-tunnel default

# Start docker service
service docker start

echo "VM setup completed successfully!"
echo "For better security, please replace the self-signed certificates with trusted ones."
echo "You can do this by mounting your own certificates to /opt/custom-tunnel/certs/"
echo "Required files: fullchain.pem and privkey.pem"
