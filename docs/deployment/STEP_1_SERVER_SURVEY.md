# STEP 1: CLOUD SERVER SURVEY & AUDIT

> **Stage:** Step 1 of 7 in the Lotus Fin Cloud Deployment Process  
> **Objective:** Comprehensive pre-deployment survey of hardware, OS, network ports, firewall, and Internet egress.  
> **Environment:** Linux Cloud Server / VPS (Ubuntu 22.04 LTS / Debian 12)  

---

## 1. SURVEY OBJECTIVES
Prior to installing packages, operations engineers must assess:
1. **Hardware Capacity:** Available vCPUs, physical RAM, and free SSD storage space.
2. **Operating System:** Linux Kernel and Ubuntu/Debian distribution release (ensuring compatibility with Docker & Frappe v16).
3. **Network Ports:** Audit whether ports `80` (HTTP), `443` (HTTPS), `8080` (Frappe), or `3306` (MariaDB) are already occupied.
4. **Firewalls:** Inspect the status of local `ufw` and cloud-level Security Groups.
5. **Outbound Internet Access:** Verify GitHub repository pulling and Docker Hub registry reachability.

---

## 2. AUTOMATED DIAGNOSTIC SCRIPT

Connect to the server via SSH as `root` (or sudo user):
```bash
ssh root@<YOUR_SERVER_IP>
```

Execute the automated system survey script:
```bash
cat << 'EOF' > /tmp/survey.sh
#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "          LOTUS FIN - SYSTEM SURVEY REPORT                "
echo "=========================================================="

echo -e "
[1] OS & KERNEL INFORMATION"
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo "OS: $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2)"

echo -e "
[2] HARDWARE SPECS (CPU / RAM / DISK)"
echo "CPU Cores: $(nproc) vCPU"
echo "CPU Model: $(lscpu | grep 'Model name' | sed 's/Model name:[ 	]*//' || echo 'Virtual CPU')"
echo -e "
RAM & Swap:"
free -h
echo -e "
Storage Capacity (Disk Space):"
df -h /

echo -e "
[3] BASE SYSTEM UTILITIES"
echo "Git: $(git --version 2>/dev/null || echo 'NOT INSTALLED')"
echo "Docker: $(docker --version 2>/dev/null || echo 'NOT INSTALLED')"
echo "Nginx: $(nginx -v 2>&1 || echo 'NOT INSTALLED')"

echo -e "
[4] LISTENING NETWORK PORTS"
ss -tulpn | grep -E ':(22|80|443|8080|3306)' || echo "Key ports are currently free"

echo -e "
[5] LOCAL FIREWALL STATUS"
ufw status verbose 2>/dev/null || echo "UFW inactive or unconfigured"

echo -e "
[6] OUTBOUND CONNECTIVITY CHECK"
curl -Is https://github.com | head -n 1 || echo "GitHub unreachable"
curl -Is https://registry-1.docker.io | head -n 1 || echo "Docker Hub unreachable"
EOF

chmod +x /tmp/survey.sh
/tmp/survey.sh
```

---

## 3. AUDIT EVALUATION CHECKLIST

| Verification Item | Minimum Requirement | Recommended | Action if Inadequate |
|---|---|---|---|
| **CPU** | 2 vCPU | 4 vCPU | Adjust Cloud VM tier if < 2 vCPU |
| **RAM** | 4 GB | 8 GB | Mandatory 2GB Swap configuration (Step 2) |
| **Storage** | 30 GB SSD free | 50 GB+ SSD free | Expand disk or clean old volumes via `docker system prune` |
| **Ports 80 & 443** | Must be open/available | Handled by Host Nginx | Terminate conflicting web servers (Apache, Caddy) |
| **Ports 8080 & 3306** | Must NOT bind to `0.0.0.0` | Bound to internal loopback only | Remap or remove public bindings |
| **OS Distribution** | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04 LTS | Re-image VM if running incompatible legacy distros |

Once all criteria are verified, proceed to **[Step 2: OS Hardening & Docker Setup](./STEP_2_OS_HARDENING_AND_DOCKER.md)**.
