# Custom Tunnel with IP Rotation

A secure, high-performance tunneling solution with automatic IP rotation, optimized for gaming and other latency-sensitive applications.

## Overview

This project provides a custom tunneling solution with two main components:

1. **Xray Server VM**: A high-performance VLESS over TLS tunnel server optimized for gaming traffic
2. **IP Rotation Container**: A service that automatically rotates the VM's IP address to avoid blocking

The system is designed to provide:
- **Security**: TLS 1.3 encryption with strong cipher suites
- **Performance**: Optimized for low latency and gaming traffic
- **Resilience**: Automatic IP rotation every 12 hours to avoid detection/blocking
- **Simplicity**: Easy deployment on Google Cloud Platform

## Architecture

```
┌─────────────────┐     ┌─────────────────────┐     ┌───────────────┐
│                 │     │                     │     │               │
│    Client       │━━━━━│  Xray Server VM     │━━━━━│  Destination  │
│    Device       │     │  (Rotates IP)       │     │  Service      │
│                 │     │                     │     │               │
└─────────────────┘     └─────────────────────┘     └───────────────┘
                                   ▲
                                   │
                        ┌─────────────────────┐
                        │                     │
                        │  IP Rotation        │
                        │  Function           │
                        │                     │
                        └─────────────────────┘
```

## Components

### Xray Server VM

- Running Alpine Linux for minimal footprint
- VLESS protocol with TLS 1.3 encryption
- Network optimizations for gaming traffic:
  - TCP Fast Open
  - TCP No Delay
  - BBR congestion control
  - Optimized buffer sizes
- Self-healing with automatic restarts

### IP Rotation Container

- Cloud Function that rotates the VM's external IP address
- Fully automated operation
- Configurable rotation schedule (default: every 12 hours)
- Manages old IP address cleanup

## Setup Instructions

### Prerequisites

- Google Cloud Platform account
- `gcloud` CLI tool installed and configured
- Bash shell environment

### Deploying the Xray Server VM

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/custom-tunnel.git
   cd custom-tunnel
   ```

2. Run the deployment script:
   ```bash
   cd xray-server-vm/server
   ./gcp_deploy.sh
   ```

3. Note the server IP address displayed at the end of the deployment.

### Deploying the IP Rotation Function

1. From the project root, run:
   ```bash
   cd ip-rotation-container
   ./deploy_ip_rotation.sh
   ```

2. The function will be deployed and ready to use.

## Usage

### Connecting to the Tunnel

You can use any VLESS-compatible client. Here's a sample configuration:

```json
{
  "outbounds": [
    {
      "protocol": "vless",
      "settings": {
        "vnext": [
          {
            "address": "YOUR_SERVER_IP",
            "port": 8000,
            "users": [
              {
                "id": "de04add9-5c68-8bab-950c-08cd5320df18",
                "encryption": "none"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {
          "serverName": "YOUR_SERVER_IP"
        }
      }
    }
  ]
}
```

### Triggering IP Rotation Manually

To manually rotate the IP address:

```bash
curl https://REGION-PROJECT_ID.cloudfunctions.net/rotate_ip
```

To rotate and immediately release the old IP:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"release_old_ip": true}' https://REGION-PROJECT_ID.cloudfunctions.net/rotate_ip
```

## Maintenance

### Updating TLS Certificates

To replace the self-signed certificate with a trusted one:

1. Obtain or generate your certificates
2. Upload them to the server:
   ```bash
   scp fullchain.pem privkey.pem root@YOUR_SERVER_IP:/opt/custom-tunnel/certs/
   ```
3. Restart the service:
   ```bash
   ssh root@YOUR_SERVER_IP "rc-service custom-tunnel restart"
   ```

### Checking Logs

To view server logs:

```bash
ssh root@YOUR_SERVER_IP "cd /opt/custom-tunnel && docker-compose logs -f"
```

To view IP rotation logs:

```bash
gcloud functions logs read rotate_ip
```

## Security Considerations

- The default setup uses a self-signed certificate. For production use, replace it with a trusted certificate.
- The UUID in the configuration is an example - generate your own before deployment.
- Consider implementing additional authentication methods for high-security deployments.
- The IP rotation function allows unauthenticated requests by default. Add authentication for production environments.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is provided for legitimate use cases such as securing your online gaming connections or protecting privacy. Users are responsible for complying with all applicable laws and regulations in their jurisdiction. 