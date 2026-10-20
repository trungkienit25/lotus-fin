# 步骤 4：宿主机 NGINX 反向代理与 SSL HTTPS 安全配置

> **阶段：** Lotus Fin 云端部署流程 7 个步骤中的第 4 步  
> **目标：** 配置宿主机 (Host) Nginx，实现高性能直接分发 React 单页应用 (SPA)、将 API 与 Frappe Desk 流量反向代理转发至本地回环端口 `8080`、支持 WebSocket 实时流式传输，并配置 Let's Encrypt TLS 证书。  
> **前置条件：** 已完成 [步骤 3：Frappe 与 ERPNext 后端 Docker 集群部署](./STEP_3_BACKEND_DEPLOYMENT.md)。  

---

## 1. NGINX 反向代理的核心架构角色

宿主机 Nginx 充当整个系统面向公网的**唯一安全入口**：
1. **前端静态资源分发：** 从 `/var/www/lotus-fin-fe` 目录直接读取并分发预先编译好的 HTML、CSS 及 JS 文件，响应延迟低于 10ms，完全无需经过容器应用层。
2. **API 与 Desk 请求反向代理：** 将 `/api/`、`/assets/`、`/desk/` 及 `/app/` 请求无缝转发至内部 Frappe 容器代理端口 `127.0.0.1:8080`。
3. **WebSocket 实时通信代理：** 为 AI 财务助手 (Copilot) 维护 Socket.io 全双工长连接通道。
4. **SSL / TLS 安全终结：** 在 443 端口终结 HTTPS 流量，强制启用前向保密密码套件 (PFS)。

---

## 2. NGINX 虚拟主机站点配置

创建虚拟主机配置文件 `/etc/nginx/sites-available/lotusfin`：

```bash
cat > /etc/nginx/sites-available/lotusfin << 'EOF'
# 限流区域：每个 IP 每秒最多允许 10 个请求
limit_req_zone $binary_remote_addr zone=lotus_limit:10m rate=10r/s;

server {
    listen 80;
    server_name _; # 请替换为生产域名（例如：demo.lotusfin.vn）

    client_max_body_size 50m;

    access_log /var/log/nginx/lotusfin_access.log;
    error_log /var/log/nginx/lotusfin_error.log;

    # 1. 直接分发 REACT 单页应用 (SPA) 静态资源
    location / {
        root /var/www/lotus-fin-fe;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;

        # 针对静态资源开启长期浏览器缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, no-transform";
        }
    }

    # 2. 将 API 与 FRAPPE DESK 请求反向代理至 DOCKER 8080 端口
    location ~ ^/(api|app|desk|assets|files|private)/ {
        limit_req zone=lotus_limit burst=20 nodelay;

        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 针对大模型多步推理与重型财务总账查询设置充裕的超时阈值
        proxy_read_timeout 180s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 180s;
    }

    # 3. 为 AI COPILOT 维持 WEBSOCKET 实时双向通信
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

## 3. 激活虚拟主机并校验配置

```bash
# 创建软链接将站点加入 sites-enabled
ln -sf /etc/nginx/sites-available/lotusfin /etc/nginx/sites-enabled/

# 移除默认的 default 欢迎页（若存在）
rm -f /etc/nginx/sites-enabled/default

# 测试 Nginx 语法完整性
nginx -t

# 平滑重新加载 Nginx 服务
systemctl reload nginx
```

---

## 4. 配置 SSL 证书 (LET'S ENCRYPT 免费自动化证书)

当生产域名已成功解析到服务器公网 IP 后，执行：
```bash
# 安装 Certbot 及 Nginx 自动化配置插件
apt-get install -y certbot python3-certbot-nginx

# 自动化签发并配置 TLS 证书
certbot --nginx -d your_domain.com

# 检查证书自动续期定时任务状态
systemctl status certbot.timer
```

下一步请转入 **[步骤 5：React 前端打包与生产发布](./STEP_5_FRONTEND_DEPLOYMENT.md)**。

