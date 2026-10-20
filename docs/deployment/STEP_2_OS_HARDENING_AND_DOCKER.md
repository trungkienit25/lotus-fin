# STEP 2: OS HARDENING & DOCKER ENVIRONMENT SETUP

> **Stage:** Step 2 of 7 in the Lotus Fin Cloud Deployment Process  
> **Objective:** Provision a 2GB Swap file, install official Docker Engine & Docker Compose v2, configure Docker container log rotation to prevent SSD storage exhaustion, and prepare filesystem deployment directories.  
> **Prerequisites:** Completed [Step 1: Cloud Server Survey & Audit](./STEP_1_SERVER_SURVEY.md).  

---

## 1. RATIONALE & ARCHITECTURAL NECESSITY

1. **Virtual Memory (Swap Allocation):**
   * Heavy operational tasks such as `bench migrate`, `bench build`, or bulk transactional ledger parsing in MariaDB introduce transient memory spikes.
   * In un-swapped environments, memory spikes to 100% trigger the Linux kernel **OOM (Out-of-Memory) Killer**, which terminates `mysqld` or `gunicorn` processes and risks catastrophic database corruption.
2. **Docker Container Log Rotation:**
   * By default, Docker logs container stdout/stderr as unbounded JSON files. Over weeks of production execution, logs accumulate to 10–20 GB, exhausting SSD capacity.
   * Setting `max-size: 10m` with `max-file: 3` enforces a hard cap of **30 MB total logs per container**, protecting disk space.

---

## 2. STEP-BY-STEP PROVISIONING

Connect to the server via SSH: `ssh root@<YOUR_SERVER_IP>` and run the following commands:

### 2.1. Allocate 2GB Swap Memory & Optimize Swappiness
Execute the provisioning block:

```bash
# 1. Allocate a 2GB swap file
fallocate -l 2G /swapfile

# 2. Restrict file permissions strictly to root
chmod 600 /swapfile

# 3. Format swap structure
mkswap /swapfile

# 4. Activate swap
swapon /swapfile

# 5. Persist mount in fstab for automatic reactivation across reboots
if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# 6. Tune swappiness to 10 (utilizes Swap only when physical RAM drops below 10%)
sysctl vm.swappiness=10
if ! grep -q 'vm.swappiness' /etc/sysctl.conf; then
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
fi
```

*Verification:*
```bash
free -h
```
*Expected Output:* `Swap:` displays `total: 2.0Gi`.

---

### 2.2. Install Official Docker Engine & Docker Compose v2 (Docker CE)
Install upstream packages directly from the official Docker repository:

```bash
# 1. Install security and certificate prerequisites
apt update
apt install -y ca-certificates curl gnupg lsb-release

# 2. Register official Docker GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes

# 3. Register official Docker Apt repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Update repository indices and install Docker CE & Compose plugin
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 5. Enable and start Docker systemd service
systemctl enable docker
systemctl start docker
```

*Verification:*
```bash
docker --version && docker compose version
```
*Expected Output:*  
* `Docker version 27.x.x` (or newer)  
* `Docker Compose version v2.x.x`

---

### 2.3. Configure Docker Log Rotation
Apply a global JSON log policy to `/etc/docker/daemon.json`:

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

# Restart daemon to apply immediately
systemctl restart docker
```

---

### 2.4. Prepare Deployment Filesystem Directories
Create directory targets for frontend static distribution and project source code:

```bash
# Directory hosting compiled React SPA assets served by Host Nginx
mkdir -p /var/www/lotus-fin-fe
chmod -R 755 /var/www/lotus-fin-fe

# Root directory for Lotus Fin application repository
mkdir -p ~/lotus-fin
```

---

## 3. ACCEPTANCE CHECKLIST

Before progressing to Step 3, verify that all conditions below are satisfied:

- [ ] Command `swapon --show` reports `/swapfile partition 2G`.
- [ ] Command `sysctl vm.swappiness` outputs `vm.swappiness = 10`.
- [ ] Command `docker info` runs without daemon errors.
- [ ] Command `docker compose version` validates Compose v2 availability.
- [ ] File `/etc/docker/daemon.json` contains `max-size: 10m`.
- [ ] Directory `/var/www/lotus-fin-fe` exists with appropriate permissions.

---

👉 **Proceed to:** [STEP 3: FRAPPE & ERPNEXT BACKEND DOCKER CLUSTER DEPLOYMENT](./STEP_3_BACKEND_DEPLOYMENT.md)
