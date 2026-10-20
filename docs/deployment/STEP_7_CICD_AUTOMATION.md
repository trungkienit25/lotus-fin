# STEP 7: GITHUB ACTIONS CI/CD AUTOMATION

> **Stage:** Step 7 of 7 in the Lotus Fin Cloud Deployment Process  
> **Objective:** Configure an automated CI/CD deployment pipeline. Whenever developers push or merge commits into the primary branch, the pipeline executes automated type checks, compiles the frontend bundle, and deploys updates to the cloud server within 30 seconds without manual interventions.  
> **Prerequisites:** Completed [Step 6: Comprehensive Verification Matrix](./STEP_6_TESTING_AND_VERIFICATION.md).  

---

## 1. CI/CD PIPELINE ARCHITECTURE

```text
 [ Developer Commit ]
         |
    git push origin main
         |
         v
 +--------------------------------------------------------------+
 |                GITHUB ACTIONS RUNNER (Cloud)                 |
 |                                                              |
 |  1. Checkout Code Repository                                 |
 |  2. Setup Node.js 20 & Cache npm dependencies                |
 |  3. Execute TypeCheck: npx tsc --noEmit                      |
 |  4. Build Production SPA: npm run build (1.47s)              |
 |  5. Package Artifact: dist.tar.gz (~820 KB)                  |
 +--------------------------------------------------------------+
                                 |
                     Encrypted SSH / SCP Deploy
                                 |
                                 v
 +--------------------------------------------------------------+
 |            LINUX CLOUD SERVER (<YOUR_SERVER_IP>)             |
 |                                                              |
 |  1. Extract dist.tar.gz into /var/www/lotus-fin-fe/          |
 |  2. Git pull latest code on server                           |
 |  3. Sync lotus_fin app code into backend container           |
 |  4. bench --site frontend migrate                            |
 |  5. bench --site frontend clear-cache                        |
 |  6. docker restart frappe_docker-backend-1                   |
 |  7. docker system prune -f (Clean unused build caches)       |
 +--------------------------------------------------------------+
```

---

## 2. GITHUB SECRETS CONFIGURATION

Navigate to **GitHub Repository -> Settings -> Secrets and variables -> Actions**, then register the following encrypted secrets:

| Secret Name | Value Description |
| :--- | :--- |
| `SERVER_HOST` | Public IP address or domain of the cloud server |
| `SERVER_USER` | Deploy user account (e.g., `root` or `deploy`) |
| `SERVER_SSH_KEY` | Private SSH Key (OpenSSH format) authorized in `~/.ssh/authorized_keys` on the server |
| `SERVER_SSH_PORT` | SSH daemon listening port (default: `22`) |

---

## 3. GITHUB ACTIONS WORKFLOW SPECIFICATION

Create `.github/workflows/deploy.yml` in the repository:

```yaml
name: Lotus Fin - Continuous Deployment (CD)

on:
  push:
    branches: [ main, develop ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: 1. Checkout repository
        uses: actions/checkout@v4

      - name: 2. Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: 3. Install frontend dependencies
        run: |
          cd frontend
          npm ci

      - name: 4. Static type checking
        run: |
          cd frontend
          npx tsc --noEmit

      - name: 5. Build production bundle
        run: |
          cd frontend
          npm run build

      - name: 6. Compress build artifacts
        run: |
          cd frontend
          tar -czf ../dist.tar.gz -C dist .

      - name: 7. Transfer build artifact to server via SCP
        uses: appleboy/scp-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          port: ${{ secrets.SERVER_SSH_PORT || 22 }}
          source: "dist.tar.gz"
          target: "/tmp"

      - name: 8. Execute deployment commands on server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          port: ${{ secrets.SERVER_SSH_PORT || 22 }}
          script: |
            set -e
            echo "Deploying frontend..."
            rm -rf /var/www/lotus-fin-fe/*
            tar -xzf /tmp/dist.tar.gz -C /var/www/lotus-fin-fe/
            rm -f /tmp/dist.tar.gz
            chown -R www-data:www-data /var/www/lotus-fin-fe

            echo "Synchronizing backend repository..."
            cd ~/lotus-fin
            git fetch origin main
            git reset --hard origin/main

            echo "Syncing code and running migrations..."
            ./run.sh sync

            echo "Restarting backend container..."
            docker compose -f frappe_docker/pwd.yml restart backend

            echo "Cleaning unused docker caches..."
            docker system prune -f

            echo "Lotus Fin deployed successfully!"
```

---

## 4. PIPELINE VERIFICATION

1. Commit and push the workflow configuration:
   ```bash
   git add .github/workflows/deploy.yml
   git commit -m "ci(deploy): add automated GitHub Actions deployment pipeline"
   git push origin main
   ```
2. Navigate to the **Actions** tab on GitHub to monitor execution in real time.
3. Once completed (green checkmark), access your server domain or IP address in a web browser to verify the live production build.
