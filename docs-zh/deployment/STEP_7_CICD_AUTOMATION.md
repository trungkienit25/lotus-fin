# 步骤 7：GITHUB ACTIONS CI/CD 自动化流水线配置

> **阶段：** Lotus Fin 云端部署流程 7 个步骤中的第 7 步  
> **目标：** 配置端到端全自动 CI/CD 交付流水线。当工程师向主干分支提交或合并代码时，流水线自动触发静态类型检查、编译前端生产包并通过加密通道部署到云端服务器，30 秒内完成全量更新，实现零手工介入。  
> **前置条件：** 已完成 [步骤 6：全链路场景集成测试与功能验收](./STEP_6_TESTING_AND_VERIFICATION.md)。  

---

## 1. CI/CD 自动化流水线架构拓扑

```text
 [ 开发者 Git 提交 ]
         |
    git push origin main
         |
         v
 +--------------------------------------------------------------+
 |                 GITHUB ACTIONS RUNNER (云端运行器)            |
 |                                                              |
 |  1. 检出源代码仓库 (actions/checkout)                         |
 |  2. 初始化 Node.js 20 并挂载 npm 缓存                        |
 |  3. 执行静态类型检查：npx tsc --noEmit                         |
 |  4. 构建 React 生产静态产物：npm run build (耗时 ~1.47s)      |
 |  5. 压缩归档打包产物：dist.tar.gz (~820 KB)                   |
 +--------------------------------------------------------------+
                                 |
                     SSH / SCP 加密通道发布
                                 |
                                 v
 +--------------------------------------------------------------+
 |            LINUX 云服务器 (<YOUR_SERVER_IP>)                  |
 |                                                              |
 |  1. 解压 dist.tar.gz 产物覆盖至 /var/www/lotus-fin-fe/        |
 |  2. 在宿主机拉取后端最新代码 (git pull)                       |
 |  3. 同步 lotus_fin 代码至 backend 容器                       |
 |  4. 执行 bench --site frontend migrate 数据库结构同步        |
 |  5. 清空 Redis 缓存：bench --site frontend clear-cache       |
 |  6. 平滑重启后端容器：docker restart frappe_docker-backend-1 |
 |  7. 清理临时构建缓存：docker system prune -f                 |
 +--------------------------------------------------------------+
```

---

## 2. GITHUB REPOSITORY 敏感凭据 (SECRETS) 配置

进入 GitHub 仓库页面：**Settings -> Secrets and variables -> Actions**，添加以下加密环境变量：

| 变量名称 | 含义与取值说明 |
| :--- | :--- |
| `SERVER_HOST` | 云服务器公网固定 IP 地址或绑定域名 |
| `SERVER_USER` | 具备部署权限的主机用户（如 `root` 或 `deploy`） |
| `SERVER_SSH_KEY` | 用于免密登录的 OpenSSH 私钥（需对应服务器的 `~/.ssh/authorized_keys`） |
| `SERVER_SSH_PORT` | SSH 服务监听端口（默认通常为 `22`） |

---

## 3. GITHUB ACTIONS 工作流定义规范

在项目根目录中创建 `.github/workflows/deploy.yml` 自动化文件：

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

## 4. 流水线触发与闭环验证

1. 提交并推送到远端代码仓库：
   ```bash
   git add .github/workflows/deploy.yml
   git commit -m "ci(deploy): add automated GitHub Actions deployment pipeline"
   git push origin main
   ```
2. 打开 GitHub 仓库的 **Actions** 标签页，实时观察各 Step 的执行日志与状态流转。
3. 待流水线输出绿色成功标志后，在浏览器访问云服务器 IP 或域名，验证最新版本已实时生效。

