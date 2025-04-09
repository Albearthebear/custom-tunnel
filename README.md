# Custom Xray Tunnel Server

A secure, high-performance VLESS over TLS tunnel server packaged as a Docker container, suitable for securing various types of traffic.

## Overview

This project provides a containerized Xray server using the VLESS protocol over TLS. It's designed for easy deployment and use, leveraging Docker and the GitHub Container Registry (GHCR).

- **Security**: Encrypts traffic using TLS 1.3.
- **Protocol**: Utilizes the efficient VLESS protocol.
- **Containerized**: Packaged as a Docker image for portability and easy deployment.
- **Configuration**: Uses external volumes for TLS certificates and configuration, separating secrets from the image.

## Architecture

```
┌───────────────┐      ┌──────────────────────────────────┐      ┌───────────────┐
│               │      │       VM / Docker Host           │      │               │
│ Xray Client   │──────│──────────► Xray Container        │──────│► Destination   │
│ (VLESS/TLS)   │ TLS  │ (Listening on Port 443)          │      │ (e.g., Game   │
│               │      │        (VLESS on Port 8000)      │      │ Server)       │
└───────────────┘      └──────────────────────────────────┘      └───────────────┘
                           ▲      │ ▲      │
                           │      │ │      │
                           └──────┘ └──────┘
                           Volume Mounts:
                           - /app/certs (TLS Certs)
                           - /app/config.json (Xray Config)
```

## Components

### Xray Server Container (`xray-server-vm/`)

- **Base Image**: `alpine:3.19` (minimal footprint).
- **Xray Version**: Pinned to `v1.8.10` (or specified version) for reproducibility.
- **Protocol**: VLESS inbound on port `8000` (internal).
- **Encryption**: TLS 1.3 configured via `streamSettings`.
- **User**: Runs as a non-root `xray` user for enhanced security.
- **Configuration**:
    - `Dockerfile`: Defines the image build process.
    - `docker-compose.yml`: Defines how to run the container, mapping ports and volumes.
    - `server/config.json`: Xray server configuration (mounted at runtime).
    - `server/certs/`: Directory containing TLS certificates (`fullchain.pem`, `privkey.pem`) (mounted at runtime).

## Setup Instructions

### Prerequisites

- Docker and Docker Compose (or `docker compose` v2+) installed.
- A server/VM (e.g., Google Cloud e2 instance) with Docker installed.
- A registered domain name pointed to your server's IP (Recommended for Let's Encrypt).
- Access to your server's terminal.
- A GitHub account (for GHCR).
- GitHub Personal Access Token (PAT) with `write:packages` scope.

### 1. Prepare Configuration Files

1.  **Clone Repository (Optional):** If you haven't already, get the base files:
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>/xray-server-vm
    ```
2.  **Generate UUID:** Create a unique UUID for your client configuration.
    ```bash
    # On Linux/macOS
    uuidgen
    # On Windows PowerShell
    # [guid]::NewGuid()
    ```
3.  **Update `server/config.json`:** Replace the placeholder `"id"` value within the `"clients"` array with the UUID you just generated.
4.  **Obtain TLS Certificates:**
    *   **Recommended (Let's Encrypt):** Use `certbot` on your server to obtain certificates for your domain name.
        ```bash
        # Example using standalone (stop any service on port 80/443 first)
        # sudo certbot certonly --standalone -d your.domain.com
        ```
        Copy the resulting `fullchain.pem` and `privkey.pem` (usually from `/etc/letsencrypt/live/your.domain.com/`) into the `xray-server-vm/server/certs/` directory.
    *   **Alternative (Self-Signed):** If not using a domain, generate self-signed certs directly in the `certs` directory (requires `openssl`):
        ```bash
        cd server/certs
        openssl req -x509 -newkey rsa:4096 -keyout privkey.pem -out fullchain.pem -days 3650 -nodes -subj "/CN=YourServerIP_or_Domain"
        cd ../..
        ```
        *Note: Using self-signed certificates requires enabling "Allow Insecure" or equivalent in your client.*

### 2. Build and Push Docker Image to GHCR

1.  **Log in to GHCR:**
    ```bash
    docker login ghcr.io -u YOUR_GITHUB_USERNAME
    # Paste your PAT when prompted for password
    ```
2.  **Build the Image:** (Navigate to the `xray-server-vm` directory first)
    ```bash
    # Replace with your GH username, desired image name, and tag
    docker build -t ghcr.io/YOUR_GITHUB_USERNAME/xray-server:latest .
    ```
3.  **Push the Image:**
    ```bash
    docker push ghcr.io/YOUR_GITHUB_USERNAME/xray-server:latest
    ```

### 3. Deploy and Run on Server

1.  **Prepare Server Files:**
    *   Ensure you have the `xray-server-vm/server/` directory on your server containing:
        *   `certs/fullchain.pem`
        *   `certs/privkey.pem`
        *   `config.json` (with your unique UUID)
    *   Ensure you have the `xray-server-vm/docker-compose.yml` file on your server. **Important:** Modify this `docker-compose.yml` file to use the `image:` directive instead of `build: .`:

        ```yaml
        version: '3'
        services:
          xray:
            # Point to your image on GHCR
            image: ghcr.io/YOUR_GITHUB_USERNAME/xray-server:latest
            restart: always
            ports:
              - "443:8000" # Map host port 443 to container port 8000
            volumes:
              # Mount local certs and config into the container
              - ./server/certs:/app/certs
              - ./server/config.json:/app/config.json
            # Optional: Mount logs externally if desired
            # - ./logs:/var/log/xray
        ```
2.  **Configure Firewall:** Ensure your server's firewall (e.g., Google Cloud VPC firewall) allows **ingress TCP traffic on port 443**.
3.  **Run the Container:** Navigate to the directory containing your modified `docker-compose.yml` and the `server` subdirectory, then run:
    ```bash
    docker compose up -d
    ```

## Usage

### Connecting from a Client

Use any Xray-compatible client (e.g., v2rayN, Nekoray, V2RayNG) with the following settings:

-   **Address:** Your server's public IP address or domain name.
-   **Port:** `443`
-   **User ID / UUID:** The unique UUID you generated and put in `config.json`.
-   **Protocol:** VLESS
-   **Encryption:** `none` (TLS provides the actual encryption)
-   **Transport:** `tcp`
-   **Security Type:** `tls`
-   **SNI / Server Name (for TLS):** Your server's domain name (Important if using Let's Encrypt certificates). If using IP/self-signed certs, you might use the IP or leave blank depending on client behavior.
-   **Allow Insecure:** `true` / `yes` ONLY if using self-signed certificates. `false` / `no` for Let's Encrypt.

*(Sample client JSON configuration structure - adapt to your specific client)*
```json
{
  // ... client-specific structure ...
  "address": "YOUR_SERVER_IP_OR_DOMAIN",
  "port": 443,
  "id": "YOUR_UNIQUE_UUID", // Replace this
  "network": "tcp",
  "type": "none", // Header type for TCP, irrelevant here
  "security": "tls",
  "tlsSettings": {
    "serverName": "YOUR_SERVER_DOMAIN", // Use domain for SNI if applicable
    "allowInsecure": false // Set to true ONLY for self-signed certs
  }
  // ... other client settings (protocol: vless, etc.)
}
```

## Maintenance

### Updating the Server

1.  **Update Image (Optional):** If you've updated the `Dockerfile` locally, rebuild and push the new image to GHCR:
    ```bash
    # On your local machine
    docker build -t ghcr.io/YOUR_GITHUB_USERNAME/xray-server:latest .
    docker push ghcr.io/YOUR_GITHUB_USERNAME/xray-server:latest
    ```
2.  **Pull New Image & Restart:** On the server:
    ```bash
    # Pull the latest image version used in your compose file
    docker compose pull xray
    # Stop and restart the container with the new image and existing config/certs
    docker compose up -d --force-recreate
    ```

### Renewing Let's Encrypt Certificates

Certificates typically last 90 days. Set up automatic renewal using `certbot renew`.

1.  Configure `certbot` for automatic renewal (often done during initial setup). You might need a cron job or systemd timer.
2.  You'll need a mechanism (e.g., a `certbot` deploy hook script) to copy the renewed certificates from `/etc/letsencrypt/live/your.domain.com/` to your `./server/certs/` directory *and then* restart the Docker container so Xray picks up the new certs:
    ```bash
    # Example concept for a deploy hook script:
    # cp /etc/letsencrypt/live/your.domain.com/*.pem /path/to/your/xray-server-vm/server/certs/
    # cd /path/to/your/xray-server-vm/
    # docker compose restart xray
    ```

### Checking Logs

```bash
# On the server, in the directory with docker-compose.yml
docker compose logs -f xray
```

## Security Considerations

-   **UUID:** Keep your VLESS UUID secret.
-   **Certificates:** Use trusted certificates (Let's Encrypt) for production. Avoid "Allow Insecure" in clients unless absolutely necessary for testing with self-signed certs.
-   **Server Updates:** Keep the base OS, Docker, and Xray (by rebuilding the image occasionally) updated.