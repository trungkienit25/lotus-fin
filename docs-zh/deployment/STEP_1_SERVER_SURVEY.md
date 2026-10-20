# 步骤 1：云服务器环境勘测与基线审计

> **阶段：** Lotus Fin 云端部署流程 7 个步骤中的第 1 步  
> **目标：** 在安装任何软件包之前，对硬件容量、操作系统版本、网络端口监听、防火墙状态及出站互联网连通性进行全面勘测与基准审计。  
> **运行环境：** Linux 云服务器 / VPS (Ubuntu 22.04 LTS / Debian 12)  

---

## 1. 勘测与审计目标

在部署前，运维与实施工程师必须明确掌握：
1. **硬件资源基线：** 可用 vCPU 核心数、物理内存容量以及 SSD 剩余可用空间。
2. **操作系统兼容性：** Linux 内核版本与 Ubuntu/Debian 发行版本（确保完全兼容 Docker CE 与 Frappe v16）。
3. **网络端口占用排查：** 严密排查 `80` (HTTP)、`443` (HTTPS)、`8080` (Frappe 网关) 及 `3306` (MariaDB) 是否存在冲突占用。
4. **防火墙规则审查：** 检查主机层 `ufw` 与云厂商安全组 (Security Group) 的放行策略。
5. **出站互联网连通性：** 验证拉取 GitHub 仓库与 Docker Hub 镜像注册表的网络通路是否通畅。

---

## 2. 自动化诊断脚本

通过 SSH 远程登录服务器（建议以 `root` 或拥有 sudo 权限的用户操作）：
```bash
ssh root@<YOUR_SERVER_IP>
```

执行以下系统勘测脚本：
```bash
cat << 'EOF' > /tmp/survey.sh
#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "          LOTUS FIN - SYSTEM SURVEY REPORT                "
echo "=========================================================="

echo -e "\n[1] OS & KERNEL INFORMATION"
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo "OS: $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2)"

echo -e "\n[2] HARDWARE SPECS (CPU / RAM / DISK)"
echo "CPU Cores: $(nproc) vCPU"
echo "CPU Model: $(lscpu | grep 'Model name' | sed 's/Model name:[ \t]*//' || echo 'Virtual CPU')"
echo -e "\nRAM & Swap:"
free -h
echo -e "\nStorage Capacity (Disk Space):"
df -h /

echo -e "\n[3] BASE SYSTEM UTILITIES"
echo "Git: $(git --version 2>/dev/null || echo 'NOT INSTALLED')"
echo "Docker: $(docker --version 2>/dev/null || echo 'NOT INSTALLED')"
echo "Nginx: $(nginx -v 2>&1 || echo 'NOT INSTALLED')"

echo -e "\n[4] LISTENING NETWORK PORTS"
ss -tulpn | grep -E ':(22|80|443|8080|3306) ' || echo "Key ports are currently free"

echo -e "\n[5] LOCAL FIREWALL STATUS"
ufw status verbose 2>/dev/null || echo "UFW inactive or unconfigured"

echo -e "\n[6] OUTBOUND CONNECTIVITY CHECK"
curl -Is https://github.com | head -n 1 || echo "GitHub unreachable"
curl -Is https://registry-1.docker.io | head -n 1 || echo "Docker Hub unreachable"
EOF

chmod +x /tmp/survey.sh
/tmp/survey.sh
```

---

## 3. 验收标准与合规对照表

| 检查项 | 最低配置要求 | 推荐生产配置 | 处置方案（若不满足） |
|---|---|---|---|
| **CPU 核心** | 2 vCPU | 4 vCPU | 若不足 2 vCPU，需升级云实例规格 |
| **物理内存** | 4 GB | 8 GB | 必须在步骤 2 中配置 2GB Swap 内存缓冲 |
| **磁盘存储** | 30 GB 剩余 SSD | 50 GB+ 剩余 SSD | 扩容云盘或执行 `docker system prune` 清理垃圾文件 |
| **80 与 443 端口** | 必须空闲可用 | 统一由 Host Nginx 监听接管 | 关闭或卸载冲突的 Apache/Caddy 服务 |
| **8080 与 3306 端口** | 严禁绑定在 `0.0.0.0` | 仅允许绑定在内部回环或 Docker 网络 | 移除公网端口映射，确保数据库私网隔离 |
| **操作系统** | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04 LTS | 若为过旧的 Linux 发行版，需重装系统镜像 |

满足以上准入基线后，请转入 **[步骤 2：操作系统安全加固与 Docker 环境搭建](./STEP_2_OS_HARDENING_AND_DOCKER.md)**。

