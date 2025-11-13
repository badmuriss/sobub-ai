#!/bin/sh
set -e

# SSL certificate directory
SSL_DIR="/etc/nginx/ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"

# Check if certificates already exist
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "SSL certificates not found. Generating..."

    # Create SSL directory if it doesn't exist
    mkdir -p "$SSL_DIR"

    # Detect local IP address
    # Try multiple methods to get the IP
    LOCAL_IP=$(hostname -i 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

    # If hostname -i returns Docker's internal IP (172.x.x.x), try to get the actual host IP
    # Note: In Docker, we can't reliably get the host's external IP, so we include common ranges
    echo "Generating SSL certificate..."
    echo "Certificate will be valid for:"
    echo "  - localhost"
    echo "  - 127.0.0.1"
    echo "  - Container IP: $LOCAL_IP"
    echo "  - Common local IP ranges: 192.168.x.x, 10.x.x.x"

    # Generate private key
    openssl genrsa -out "$KEY_FILE" 2048 2>/dev/null

    # Generate self-signed certificate with multiple SANs for flexibility
    openssl req -new -x509 -key "$KEY_FILE" -out "$CERT_FILE" -days 365 \
        -subj "/C=BR/ST=State/L=City/O=SobubAI/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1,IP:$LOCAL_IP,IP:192.168.0.0,IP:192.168.1.0,IP:192.168.15.0,IP:10.0.0.0" \
        2>/dev/null

    # Set proper permissions
    chmod 600 "$KEY_FILE"
    chmod 644 "$CERT_FILE"

    echo ""
    echo "    SSL certificates generated successfully!"
    echo ""
    echo "    IMPORTANT: You will see a browser warning about the self-signed certificate."
    echo "    This is normal for local development."
    echo ""
    echo "    On mobile browsers, you need to accept the certificate warning:"
    echo "    - Chrome: Click 'Advanced' → 'Proceed to ... (unsafe)'"
    echo "    - Safari: Click 'Show Details' → 'visit this website'"
    echo "    - Firefox: Click 'Advanced' → 'Accept the Risk and Continue'"
    echo ""
else
    echo "SSL certificates found. Using existing certificates."
    echo "Certificate: $CERT_FILE"
    echo "Private key: $KEY_FILE"
fi

# Execute the main nginx command
exec "$@"
