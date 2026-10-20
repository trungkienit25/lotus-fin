# STEP 4: HOST NGINX REVERSE PROXY & SSL CONFIGURATION

> **Stage:** Step 4 of 7 in the Lotus Fin Cloud Deployment Process  
> **Objective:** Configure Host Nginx to serve the React SPA, reverse-proxy API & Frappe Desk traffic to loopback port `8080`, enable WebSocket proxying, and configure Let's Encrypt TLS.  
> **Prerequisites:** Completed [Step 3: Backend Docker Deployment](./STEP_3_BACKEND_DEPLOYMENT.md).  

---

## 1. NGINX REVERSE PROXY ARCHITECTURAL ROLE

Host Nginx functions as the **single public entrypoint** for inbound network traffic:
1. **Frontend Static Server:** Serves pre-compiled HTML, CSS, and JS assets directly from `/var/www/lotus-fin-fe` under sub-10ms response latencies without touching the container layer.
2. **API & Desk Reverse Proxy:** Forwards `/api/`, `/assets/`, `/desk/`, and `/app/` routes to the internal Frappe container proxy at `127.0.0.1:8080`.
3. **WebSocket Proxying:** Maintains bi-directional Socket.io streaming channels for the AI Copilot.
4. **SSL / TLS Termination:** Terminates HTTPS on port 443 with modern forward-secrecy cipher suites.

---

## 2. NGINX VIRTUAL HOST CONFIGURATION

Create `/etc/nginx/sites-available/lotusfin`:

```bash
cat > /etc/nginx/sites-available/lotusfin << 'EOF'
# Rate limiting zone: 10 requests per second per IP
limit_req_zone $binary_remote_addr zone=lotus_limit:10m rate=10r/s;

server {
    listen 80;
    server_name _; # Replace with your production domain (e.g., demo.lotusfin.vn)

    client_max_body_size 50m;

    access_log /var/log/nginx/lotusfin_access.log;
    error_log /var/log/nginx/lotusfin_error.log;

    # 1. SERVE REACT SINGLE PAGE APPLICATION (SPA)
    location / {
        root /var/www/lotus-fin-fe;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;

        # Cache control for static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, no-transform";
        }
    }

    # 2. PROXY APIS & FRAPPE DESK TO DOCKER PORT 8080
    location ~ ^/(api|app|desk|assets|files|private)/ {
        limit_req zone=lotus_limit burst=20 nodelay;

        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Extended timeouts for LLM synthesis and heavy accounting queries
        proxy_read_timeout 180s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 180s;
    }

    # 3. WEBSOCKET REAL-TIME PROXY FOR AI COPILOT
    location /socket.io {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF
```

---

## 3. ACTIVATE VIRTUAL HOST & VERIFY

```bash
# Enable virtual host by symlinking into sites-enabled
ln -sf /etc/nginx/sites-available/lotusfin /etc/nginx/sites-enabled/

# Remove default site if present
rm -f /etc/nginx/sites-enabled/default

# Test Nginx syntax
nginx -t

# Reload Nginx service
systemctl reload nginx
```

---

## 4. PROVISION SSL CERTIFICATE (LET'S ENCRYPT)

When a domain name is pointed to your public IP:
```bash
# Install Certbot and Nginx plugin
apt-get install -y certbot python3-certbot-nginx

# Obtain and install TLS certificate automatically
certbot --nginx -d your_domain.com

# Verify automatic certificate renewal timer
systemctl status certbot.timer
```

Proceed to **[Step 5: Frontend Deployment](./STEP_5_FRONTEND_DEPLOYMENT.md)**.
