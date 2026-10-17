# Lotus Fin — 运维与一键自动化部署中文手册

本手册详细阐述了 Lotus Fin 自动化运维脚本的设计原理、目录规范以及在各类服务器上的操作流程。

---

## 📁 脚本目录架构设计 (`/scripts`)

所有与系统运行、开发、打包、部署相关的脚本均已归类收敛至 [`scripts/`](../../scripts) 目录：

```
scripts/
├── deploy/                 # 🚀 云端生产环境全自动一键部署流水线
│   └── run-deploy.sh       # 涵盖环境自检、Swap自动分配、数据库无损迁移与80端口上线
├── dev/                    # 💻 开发者本地启动脚本
│   ├── run-dev.sh          # Linux / macOS / WSL 自动拉起后端容器与 Vite 开发服务器
│   └── run-dev.ps1         # Windows 原生 PowerShell 启动脚本
├── packaging/              # 📦 生产容器打包
│   └── run-packaging.sh    # 多阶段构建 lotus-fin/gateway (React 前端 + Nginx 反向代理)
├── container/              # 🐳 容器生命周期管理
│   └── run-container.sh    # 针对生产容器的 start/stop/restart/logs/status 操作
└── data/database/          # 🗄️ 数据库无损迁移种子快照
    └── initial_db_seed.sql.gz  # 预打包好的真实企业总账、基础数据与凭证
```

同时，在根目录下保留有统一调用脚本 [`run.sh`](../../run.sh)，支持简明指令直接分发。

---

## 🚀 1. 云端生产环境一键部署 (`run.sh deploy`)

在您购置新的云服务器（例如 Ubuntu、Debian 或各公有云 VPS）后，只需依次执行：

```bash
git clone https://github.com/your-org/lotus-fin.git
cd lotus-fin

# 赋权并启动全自动部署
chmod +x run.sh scripts/*/*.sh
./run.sh deploy
```

### 7 步全自动部署流水线详解：
1. **主机系统资源审查：** 检查系统内存，若检测到服务器 Swap 交换空间小于 1GB，**将自动创建 2GB Swapfile 并持久化挂载至 `/etc/fstab`**，从根本上防止 Frappe/ERPNext 进程在低配 VPS 上因内存溢出（OOM）崩溃。
2. **Docker 环境自愈：** 自动检查 `docker` 与 `docker compose` 命令。若机器未安装，脚本会自动配置 Docker 官方源并完成无人值守安装。
3. **环境参数校验：** 自动加载或生成生产环境变量配置文件 `docker/production/.env.production`。
4. **Nginx 前端网关打包：** 多阶段自动编译 React 19 单页应用代码，并将产物嵌入基于 Alpine 的轻量级 Nginx 容器镜像中。
5. **容器编排集群启动：** 启动数据库、Redis 队列/缓存及后端微服务，由 Nginx 在**标准 HTTP 80 端口**对外提供服务。
6. **历史数据无损导入（Hydration）：**
   - 自动检测并解压 [`scripts/data/database/initial_db_seed.sql.gz`](../../scripts/data/database/initial_db_seed.sql.gz) 数据库快照导入 MariaDB。
   - 自动执行 `bench migrate` 完成结构同步。
   - 自动注入 SMTP 邮件发送网关账号以及企业演示财务账簿。
7. **服务就绪核验：** 执行内部健康嗅探（HTTP 200 验证），获取服务器公网 IP 并打印访问入口。

---

## 💻 2. 本地开发调试运行指南

### Linux / macOS / WSL 环境：
```bash
./run.sh dev
# 实际执行：./scripts/dev/run-dev.sh
```

### Windows 原生 PowerShell 环境：
```powershell
.\scripts\dev\run-dev.ps1
```

- 该命令会自动启动后端的 Frappe 与 MariaDB 容器，将 `lotus_fin` 模块安装至 Python 虚拟环境，并启动 Vite 开发服务器（端口 `5173`，自动代理 API 请求至 `8080`）。

---

## 📦 3. 生产镜像独立打包 (`run.sh packaging`)

在修改了前端 UI 界面或需要发布新版本 Docker 镜像时：
```bash
./run.sh packaging
# 实际执行：./scripts/packaging/run-packaging.sh
```

---

## 🐳 4. 容器生命周期管理指令

进入生产维护阶段后，使用以下指令进行容器运维：

```bash
./scripts/container/run-container.sh status   # 查看各容器运行状态与内存占用
./scripts/container/run-container.sh logs     # 实时跟踪聚合输出日志
./scripts/container/run-container.sh restart  # 热重启所有服务
./scripts/container/run-container.sh stop     # 优雅停止所有容器
./scripts/container/run-container.sh clean    # 销毁容器及关联虚拟网络
```

---

## 🌐 5. 端口规划与 Nginx 路由规范

系统统一收敛流量入口，无需在宿主机额外安装或配置 Nginx：
- **监听端口：** `80` (HTTP)
- **`/` 根路由：** 由 Nginx 直接提供高性能的 React 静态资源服务，内置 Gzip 压缩支持。
- **`/(api|assets|files|desk|app|socket.io)/` 业务路由：** 由 Nginx 反向代理至内部 `frappe-frontend:8080` 后端服务。
- 用户和外部系统仅需访问统一的 `http://<SERVER_IP>/` 即可使用全部功能。
