# 步骤 2：操作系统安全加固与 DOCKER 环境搭建

> **阶段：** Lotus Fin 云端部署流程 7 个步骤中的第 2 步  
> **目标：** 分配 2GB Swap 虚拟内存缓冲，安装官方最新 Docker Engine & Docker Compose v2，配置容器日志轮转以防止 SSD 存储耗尽，并准备应用系统目录。  
> **前置条件：** 已完成 [步骤 1：云服务器环境勘测与基线审计](./STEP_1_SERVER_SURVEY.md)。  

---

## 1. 架构必要性与实施原理

1. **虚拟内存 (Swap 缓冲机制)：**
   * 在执行 `bench migrate`、前端构建或 MariaDB 批量导入会计凭证总账等密集型任务时，系统瞬时内存会发生尖峰突增。
   * 若未配置 Swap，当内存使用率触及 100% 时，Linux 内核的 **OOM Killer (内存溢出终止机制)** 将强行杀死 `mysqld` 或 `gunicorn` 进程，极易造成数据库文件不可逆损坏。
2. **Docker 日志轮转配置：**
   * 默认情况下，Docker 以无限制的 JSON 文件记录容器的 stdout/stderr 日志。在长周期连续运行后，日志体积可能膨胀至 10–20 GB，直接导致 SSD 磁盘写满。
   * 通过全局配置 `max-size: 10m` 与 `max-file: 3`，可将每个容器的日志上限严格限制在 **30 MB** 以内，保障磁盘安全。

---

## 2. 详细配置与安装流程

通过 SSH 远程连接至云服务器：`ssh root@<YOUR_SERVER_IP>` 并顺序执行：

### 2.1. 创建 2GB Swap 虚拟内存并优化 Swappiness
执行以下自动化配置脚本块：

```bash
# 1. 预分配 2GB Swap 文件
fallocate -l 2G /swapfile

# 2. 严格收紧文件权限，仅允许 root 读写
chmod 600 /swapfile

# 3. 格式化为交换分区结构
mkswap /swapfile

# 4. 激活挂载 Swap
swapon /swapfile

# 5. 写入 /etc/fstab，确保服务器重启后自动生效
if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# 6. 将 swappiness 调优为 10（仅当物理 RAM 剩余不足 10% 时才使用 Swap）
sysctl vm.swappiness=10
if ! grep -q 'vm.swappiness' /etc/sysctl.conf; then
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
fi
```

*校验输出：*
```bash
free -h
```
*预期结果：* `Swap:` 行正确显示 `total: 2.0Gi`。

---

### 2.2. 安装 Docker Engine 与 Docker Compose v2 官方最新版 (Docker CE)
直接从 Docker 官方源获取最新稳定版（避免使用操作系统自带的过旧发行版）：

```bash
# 1. 安装基础依赖与证书工具
apt update
apt install -y ca-certificates curl gnupg lsb-release

# 2. 导入 Docker 官方 GPG 密钥
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes

# 3. 添加 Docker 官方 APT 软件源
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. 更新软件索引并安装 Docker CE 及 Compose 插件
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 5. 设置 Docker 服务开机自启并立即启动
systemctl enable docker
systemctl start docker
```

*版本验证：*
```bash
docker --version && docker compose version
```
*预期输出：*  
* `Docker version 27.x.x` (或更新版本)  
* `Docker Compose version v2.x.x`

---

### 2.3. 配置 Docker 日志轮转 (防磁盘占满)
创建并写入全局 `/etc/docker/daemon.json` 配置文件：

```bash
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# 重启 Docker 守护进程以立即应用策略
systemctl restart docker
```

---

### 2.4. 建立系统部署目录结构
创建用于存放前端静态分发资源与后端核心工程代码的目标目录：

```bash
# 存放 React SPA 生产静态打包产物的目录（供宿主机 Nginx 直接读取分发）
mkdir -p /var/www/lotus-fin-fe
chmod -R 755 /var/www/lotus-fin-fe

# 存放 Lotus Fin 源码仓库的根目录
mkdir -p ~/lotus-fin
```

---

## 3. 验收检查清单

在推进至步骤 3 之前，请确认以下各项均已通过验证：

- [ ] 命令 `swapon --show` 输出 `/swapfile partition 2G`。
- [ ] 命令 `sysctl vm.swappiness` 输出 `vm.swappiness = 10`。
- [ ] 命令 `docker info` 执行成功且守护进程无异常报错。
- [ ] 命令 `docker compose version` 能够正确识别 Compose v2。
- [ ] 文件 `/etc/docker/daemon.json` 包含 `max-size: 10m`。
- [ ] 目录 `/var/www/lotus-fin-fe` 存在且权限为 `755`。

---

👉 **下一步：** [步骤 3：Frappe 与 ERPNext 后端 Docker 集群部署](./STEP_3_BACKEND_DEPLOYMENT.md)

