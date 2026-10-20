# 步骤 6：全链路场景集成测试与功能验收

> **阶段：** Lotus Fin 云端部署流程 7 个步骤中的第 6 步  
> **目标：** 针对部署落地的生产系统执行包含 6 大业务场景的全量测试矩阵：网络连通性、Frappe Desk 会计控制台身份鉴权、AI Copilot 智能问答接口、自动化单元测试集、What-If 财务多因素压力模拟以及系统硬件资源开销审计。  
> **前置条件：** 已完成 [步骤 5：React 前端打包与生产发布](./STEP_5_FRONTEND_DEPLOYMENT.md)。  

---

## 1. 6 大场景自动化验收矩阵

| 场景序号与名称 | 验证范围与手段 | 验收合格基准线 (Acceptance Criteria) |
| :--- | :--- | :--- |
| **1. 网络与端口探活** | 测试 Host Nginx、公网端口及发往 Docker :8080 回环转发 | HTTP 200 OK，网关平均延迟 < 50ms |
| **2. Frappe Desk 会计台** | 模拟管理员凭证登录后台，加载财务健康仪表盘 | 成功获取 Cookie，页面图表及数据表正常渲染 |
| **3. AI Copilot 接口** | 向 `/api/method/chat_copilot` 发送自然语言财务诊断指令 | 正确返回包含 4 大指标的 JSON 信封与 UI 卡片，无越权报错 |
| **4. 自动化单元测试** | 在容器内部执行 Python 财务核算用例测试套件 | 全部用例通过 (PASS)，单次测试耗时 < 2 秒 |
| **5. What-If 压力模拟** | 运行复合冲击场景（营业收入下滑 20%，账期拖延 15 天） | 完整返回 9 项财务 KPI 压力测算矩阵，无 `NaN`/`Null` 异常 |
| **6. 硬件开销审计** | 实时采样 9 个容器的物理内存与 CPU 负载情况 | Docker 集群常驻内存 <= 1.4 GB；8GB 宿主机空闲 RAM >= 6.0 GB |

---

## 2. 详细测试执行脚本

通过 SSH 连接到云服务器：`ssh root@<YOUR_SERVER_IP>` 并逐一运行：

### 2.1. 场景 1：网络连通性与 Ping 探活测试
```bash
# 验证宿主机 Nginx 正常对外响应
curl -Is http://localhost/ | head -n 1
# 预期输出：HTTP/1.1 200 OK

# 验证 API 路径正确反向代理至 Docker 容器
curl -s http://localhost/api/method/ping
# 预期输出：{"message":"pong"}
```

---

### 2.2. 场景 2：Frappe Desk 身份认证与会话测试
```bash
# 使用管理员账号发起 API 登录，并将会话凭据保存至本地临时文件
curl -s -X POST http://localhost/api/method/login \
  -H "Content-Type: application/json" \
  -d '{"usr": "Administrator", "pwd": "admin"}' \
  -c /tmp/cookie.txt

# 预期返回：{"message":"Logged In","home_page":"/app"}
```

---

### 2.3. 场景 3：AI Copilot 智能分析端点调用测试
```bash
# 携带认证 Cookie 调用财务健康分析智能体
curl -s -X POST http://localhost/api/method/lotus_fin.api.ai_insights.chat_copilot \
  -H "Content-Type: application/json" \
  -b /tmp/cookie.txt \
  -d '{
    "message": "Analyze corporate financial health for Lotus-fin (Demo) as of 2026-10-01",
    "company": "Lotus-fin (Demo)"
  }' | jq .
```
验证返回体中包含 `status: "SUCCESS"`，具备强类型财务事实（Revenue、COGS、Gross Margin、DSCR）以及确定性渲染的交互式 UI Widget 结构。

---

### 2.4. 场景 4：执行自动化单元测试套件
```bash
cd ~/lotus-fin

# 在 Docker 容器内部执行财务健康核心计算测试集
./run.sh test lotus_fin.tests.test_financial_health
```
确保终端输出显示用例全部通过，零失败退出。

---

### 2.5. 场景 5：运行 What-If 复合因素财务压力模拟
```bash
# 启动多因素压力测算引擎
./run.sh simulate
```
检查标准输出中是否完整包含了 9 项压力仿真 KPI：
- 营收偏差率 (Revenue Variance)、毛利率变动 (Gross Margin delta)、经营现金流 (Operating Cashflow)、期末现金 (Closing Cash)、现金跑道 (Cash Runway)、营运资金 (Net Working Capital)、偿债倍数 (DSCR)、逾期应收账款 (Overdue Receivables) 以及应付账款聚集 (Payables Cluster)。

---

### 2.6. 场景 6：系统硬件开销与资源审计
```bash
# 抓取当前所有容器的瞬时 CPU 与内存资源占用快照
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# 审查宿主机的物理内存与 Swap 交换区使用状态
free -h
```

验收全部通过后，请进入 **[步骤 7：GitHub Actions CI/CD 自动化流水线配置](./STEP_7_CICD_AUTOMATION.md)**。

