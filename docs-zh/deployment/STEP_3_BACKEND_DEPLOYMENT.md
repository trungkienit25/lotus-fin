# 步骤 3：FRAPPE 与 ERPNEXT 后端 DOCKER 集群部署

> **阶段：** Lotus Fin 云端部署流程 7 个步骤中的第 3 步  
> **目标：** 拉取代码仓库，启动 Frappe v16 & ERPNext 的 9 个核心容器服务，挂载并安装 `lotus_fin` 应用，执行 MariaDB 11.8 数据库迁移，并灌入企业级财务演示测试数据集。  
> **前置条件：** 已完成 [步骤 2：操作系统安全加固与 Docker 环境搭建](./STEP_2_OS_HARDENING_AND_DOCKER.md)。  

---

## 1. 9 容器后端微服务集群拓扑

后端架构严格遵循 Frappe 官方生产规范，使用 Docker Compose 进行编排封装 (`frappe_docker/pwd.yml`)：

```text
                                  [ 端口 8080 ]
                                        |
                                        v
                         +-----------------------------+
                         |  frappe_docker-frontend-1   |
                         | (Frappe 内部 Nginx 入口代理) |
                         +--------------+--------------+
                                        |
                 +----------------------+----------------------+
                 |                      |                      |
                 v                      v                      v
        +-----------------+    +-----------------+    +-----------------+
        |     backend     |    |    websocket    |    |       db        |
        | (Gunicorn 应用) |    | (SocketIO 实时) |    | (MariaDB 11.8)  |
        +--------+--------+    +-----------------+    +-----------------+
                 |
                 +------------------------------+
                 |                              |
                 v                              v
        +-----------------+            +-----------------+
        |   queue-short   |            |   queue-long    |
        | (短时任务队列)  |            | (长时异步队列)  |
        +--------+--------+            +--------+--------+
                 |                              |
                 v                              v
        +-----------------+            +-----------------+
        |   redis-queue   |            |   redis-cache   |
        | (Celery / RQ)   |            | (系统内存缓存)  |
        +-----------------+            +-----------------+
                 ^
                 |
        +-----------------+
        |    scheduler    |
        | (Frappe 定时器) |
        +-----------------+
```

---

## 2. 详细部署实操步骤

通过 SSH 登录服务器：`ssh root@<YOUR_SERVER_IP>`。

### 2.1. 拉取 Lotus Fin 源代码仓库
```bash
cd ~
git clone https://github.com/trungkienit25/lotus-fin.git ~/lotus-fin
cd ~/lotus-fin

# 赋予部署控制脚本可执行权限
chmod +x run.sh
```

---

### 2.2. 初始化并拉起 9 个容器服务
执行集群启动指令：
```bash
./run.sh up
```

*底层自动化执行逻辑：*
1. 自动检测并克隆 `frappe_docker` 编排配置子模块。
2. 拉取官方权威镜像：
   * `frappe/erpnext:v16.36.1` (~2.89 GB)
   * `mariadb:11.8` (~329 MB)
   * `redis:6.2-alpine` (~28 MB)
3. 启动临时 `create-site` 容器，创建默认站点 `frontend`（默认凭证：`Administrator / admin`）。
4. 顺序启动全部 9 个核心长期运行容器。

> [!NOTE]
> 首次执行需要约 **2 至 3 分钟**（取决于云服务器下载镜像的网络带宽）。

---

### 2.3. 检查容器集群健康状态
查看所有容器的运行状态：
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**9/9 容器集群健康验收标准：**

| 容器名称 | 预期状态 | 端口与网络映射 | 核心职责 |
| :--- | :---: | :---: | :--- |
| `frappe_docker-frontend-1` | `Up ...` | `0.0.0.0:8080->8080/tcp` | Frappe 内部反向代理与静态资源入口 |
| `frappe_docker-backend-1` | `Up ...` | 内部私网通信 | Python Gunicorn 核心业务应用服务器 |
| `frappe_docker-db-1` | `Up ... (healthy)` | `3306/tcp` | MariaDB 关系型数据库 |
| `frappe_docker-websocket-1`| `Up ...` | 内部私网通信 | Socket.io 实时双向事件引擎 |
| `frappe_docker-queue-short-1`| `Up ...` | 内部私网通信 | 短周期后台任务处理（邮件派发、事件通知） |
| `frappe_docker-queue-long-1` | `Up ...` | 内部私网通信 | 重型计算异步处理（生成报表、财务快照） |
| `frappe_docker-scheduler-1` | `Up ...` | 内部私网通信 | 负责定时调度触发的 Cron 任务 |
| `frappe_docker-redis-queue-1`| `Up ...` | `6379/tcp` | Celery / RQ 消息中继队列 |
| `frappe_docker-redis-cache-1`| `Up ...` | `6379/tcp` | 系统级内存数据缓存 |

---

### 2.4. 同步 Lotus Fin 应用代码并执行数据库迁移
确认 9 个容器均处于稳定状态后，运行代码同步命令：
```bash
./run.sh sync
```

*该命令自动依次执行：*
1. 将当前最新的 `lotus_fin` 源码映射拷贝至容器内的 `/home/frappe/frappe-bench/apps/lotus_fin`。
2. 在容器 Python 虚拟环境中安装 `lotus_fin` (`pip install -e`)。
3. 执行数据库结构变更迁移 (`bench --site frontend migrate`)，注册 DocType 模型、自定义字段及 Fixtures。
4. 清空 Redis 缓存并平滑重启 `frappe_docker-backend-1` 容器加载新代码。

> [!TIP]
> 成功预期输出日志：`[OK] Synced source code, built assets, migrated DB, and reloaded successfully!`。

---

### 2.5. 注入企业财务演示数据集
为 AI 核心引擎（AI001 至 AI007）提供真实仿真发票、往来账款及现金流数据：
```bash
./run.sh demo
```

*生成的基础业务数据：*
* 示范企业实体：`Lotus-fin (Demo)`.
* 标准会计科目表 (COA) 及基线资产负债表。
* 完整的全生命周期发票：`Sales Invoice`（销售发票）、`Payment Entry`（付款凭单）及 `AR Overdue`（逾期账款）。
* Copilot 专用控制台端点：`http://localhost:8080/desk/financial-health`。

---

## 3. 验收检查清单

- [ ] 执行 `docker ps` 能看到全部 9 个带有 `frappe_docker-` 前缀的容器。
- [ ] 容器 `frappe_docker-db-1` 状态带有 `(healthy)` 标识。
- [ ] 探测请求 `curl -I http://127.0.0.1:8080/api/method/ping` 正确返回 `HTTP/1.1 200 OK` (pong)。
- [ ] 执行 `docker stats --no-stream` 确认 9 个容器占用的物理内存总和稳定在 **750 MB 至 1.1 GB** 之间。

---

👉 **下一步：** [步骤 4：宿主机 NGINX 反向代理与 SSL HTTPS 安全配置](./STEP_4_NGINX_AND_SSL_CONFIG.md)

