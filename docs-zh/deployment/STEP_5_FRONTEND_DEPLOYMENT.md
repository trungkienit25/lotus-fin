# 步骤 5：REACT 前端打包与生产发布

> **阶段：** Lotus Fin 云端部署流程 7 个步骤中的第 5 步  
> **目标：** 将 React 单页应用 (TypeScript / Vite / Tailwind CSS) 编译为高压缩率的生产静态分发产物，并部署至宿主机 Nginx 根目录。  
> **前置条件：** 已完成 [步骤 4：宿主机 Nginx 反向代理与 SSL HTTPS 安全配置](./STEP_4_NGINX_AND_SSL_CONFIG.md)。  

---

## 1. 资源优化策略：本地/CI 预编译 vs. 云端编译

为了最大限度节省云服务器的硬件开销，Lotus Fin 严格强制在本地开发机或 CI Runner 流水线上完成前端打包，严禁在生产云主机上执行 `npm install`：

| 评估维度 | 在云主机上直接编译 | 本地 / CI 流水线预编译 (强制标准) |
| :--- | :--- | :--- |
| **磁盘占用** | 安装 `node_modules` 吞噬 **~1.2 GB** 空间 | **仅占用 ~820 KB** (极度轻量的生产打包压缩产物) |
| **内存消耗** | 打包瞬时峰值消耗 **1.5 GB RAM** | **0 字节** 运行时内存消耗 |
| **构建耗时** | 需 45 - 90 秒 | **1.47 秒** (得益于 Vite 与 Rolldown 引擎加速) |
| **系统稳定性风险** | 极易引发 Linux OOM Killer 杀掉后端进程 | 对生产正在运行的业务实现零运行时干扰 |

---

## 2. 详细打包与部署步骤

### 阶段 A：在本地机器或 CI 运行器中打包产物

进入本地代码根目录 `lotus-fin`：

```bash
# 1. 切换至前端代码目录
cd frontend

# 2. 执行 TypeScript 静态类型检查与生产打包
npm run build
```

*实际构建基准输出示例：*
```text
vite building client environment for production...
transformed modules.
dist/index.html                   0.82 kB | gzip:  0.44 kB
dist/assets/index-D7hH4k4k.css   42.18 kB | gzip:  8.61 kB
dist/assets/index-B9z8aXy1.js   521.14 kB | gzip: 162.30 kB
built in 1470ms
```

压缩归档构建产物：
```bash
# 3. 打包生成轻量 tarball 归档文件
tar -czf dist.tar.gz -C dist .
```

---

### 阶段 B：安全分发并解压至云服务器

将归档文件同步至服务器并就地解压生效：

```bash
# 1. 通过 SCP 加密管道将打包文件传送到云服务器
scp dist.tar.gz root@<YOUR_SERVER_IP>:/tmp/

# 2. SSH 登录云服务器
ssh root@<YOUR_SERVER_IP>

# 3. 清空原发布目录并解压新版本静态产物
rm -rf /var/www/lotus-fin-fe/*
tar -xzf /tmp/dist.tar.gz -C /var/www/lotus-fin-fe/

# 4. 赋予 Nginx 运行用户权限并修正访问模式
chown -R www-data:www-data /var/www/lotus-fin-fe
chmod -R 755 /var/www/lotus-fin-fe

# 5. 清理临时归档文件
rm -f /tmp/dist.tar.gz
```

---

## 3. 结果验证

在服务器上通过 curl 探活前端入口：
```bash
curl -I http://localhost/
# 预期输出：HTTP/1.1 200 OK，并且 Content-Type 为 text/html
```

验证通过后，请进入 **[步骤 6：全链路场景集成测试与功能验收](./STEP_6_TESTING_AND_VERIFICATION.md)**。

