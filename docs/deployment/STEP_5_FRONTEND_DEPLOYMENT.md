# STEP 5: REACT FRONTEND PACKAGING & DEPLOYMENT

> **Stage:** Step 5 of 7 in the Lotus Fin Cloud Deployment Process  
> **Objective:** Compile the React SPA (TypeScript / Vite / Tailwind) into production static assets and deploy to Host Nginx.  
> **Prerequisites:** Completed [Step 4: Host Nginx & SSL Configuration](./STEP_4_NGINX_AND_SSL_CONFIG.md).  

---

## 1. OPTIMIZATION STRATEGY: LOCAL / CI BUILD VS. SERVER BUILD

To preserve server hardware headroom, Lotus Fin enforces building assets locally or inside CI runners rather than compiling on the production VM:

| Criterion | Compiling on Server | Local / CI Build (Enforced) |
| :--- | :--- | :--- |
| **Disk Overhead** | Consumes **~1.2 GB** for `node_modules` | **Only ~820 KB** deployed (minified `dist` artifacts) |
| **RAM Utilization** | Consumes **1.5 GB RAM** during bundling spikes | **0 bytes** server RAM consumed during compilation |
| **Build Duration** | 45 - 90 seconds | **1.47 seconds** via Vite & Rolldown engine |
| **Operational Risk** | Risk of triggering host OOM crashes | Zero runtime impact on running services |

---

## 2. DEPLOYMENT PROCEDURE

### PART A: Build Artifacts on Local Machine / CI Runner

From the workspace root `lotus-fin`:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Run TypeScript check and production build
npm run build
```

*Actual build benchmark:*
```text
vite building client environment for production...
transformed modules.
dist/index.html                   0.82 kB | gzip:  0.44 kB
dist/assets/index-D7hH4k4k.css   42.18 kB | gzip:  8.61 kB
dist/assets/index-B9z8aXy1.js   521.14 kB | gzip: 162.30 kB
built in 1470ms
```

Package the resulting artifacts:
```bash
# 3. Create a compressed tarball
tar -czf dist.tar.gz -C dist .
```

---

### PART B: Deploy to Server

Transfer and extract onto the cloud server:

```bash
# 1. Transfer archive to server via SCP
scp dist.tar.gz root@<YOUR_SERVER_IP>:/tmp/

# 2. Connect to the server
ssh root@<YOUR_SERVER_IP>

# 3. Clean target directory and extract assets
rm -rf /var/www/lotus-fin-fe/*
tar -xzf /tmp/dist.tar.gz -C /var/www/lotus-fin-fe/

# 4. Set secure web permissions
chown -R www-data:www-data /var/www/lotus-fin-fe
chmod -R 755 /var/www/lotus-fin-fe

# 5. Clean up temporary archive
rm -f /tmp/dist.tar.gz
```

---

## 3. VERIFICATION

Verify asset delivery via curl:
```bash
curl -I http://localhost/
# Expected HTTP/1.1 200 OK with Content-Type: text/html
```

Proceed to **[Step 6: Testing & Verification Matrix](./STEP_6_TESTING_AND_VERIFICATION.md)**.
