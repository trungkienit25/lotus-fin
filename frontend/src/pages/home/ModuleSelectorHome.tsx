import React, { useEffect, useState } from "react";
import { Card, Row, Col, Typography, Spin, Space, Tag, Empty } from "antd";
import {
  BankOutlined,
  ShoppingOutlined,
  AppstoreOutlined,
  TeamOutlined,
  SettingOutlined,
  DollarOutlined,
  FolderOutlined,
  ToolOutlined,
  GlobalOutlined,
  ProjectOutlined,
  SafetyCertificateOutlined,
  ArrowRightOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const { Title, Text } = Typography;

interface WorkspaceMeta {
  name: string;
  title: string;
  icon?: string;
  module?: string;
}

// Map các icon tương ứng cho từng module Workspace
const getModuleIcon = (name: string) => {
  const n = name.toLowerCase();
  if (n.includes("invoicing") || n.includes("account") || n.includes("financ")) {
    return <DollarOutlined style={{ fontSize: 32, color: "#1677ff" }} />;
  }
  if (n.includes("selling") || n.includes("crm")) {
    return <ShoppingOutlined style={{ fontSize: 32, color: "#52c41a" }} />;
  }
  if (n.includes("buying")) {
    return <BankOutlined style={{ fontSize: 32, color: "#fa8c16" }} />;
  }
  if (n.includes("stock") || n.includes("asset")) {
    return <AppstoreOutlined style={{ fontSize: 32, color: "#13c2c2" }} />;
  }
  if (n.includes("project")) {
    return <ProjectOutlined style={{ fontSize: 32, color: "#722ed1" }} />;
  }
  if (n.includes("quality")) {
    return <SafetyCertificateOutlined style={{ fontSize: 32, color: "#eb2f96" }} />;
  }
  if (n.includes("user") || n.includes("hr")) {
    return <TeamOutlined style={{ fontSize: 32, color: "#2f54eb" }} />;
  }
  if (n.includes("build") || n.includes("manufactur") || n.includes("subcontract")) {
    return <ToolOutlined style={{ fontSize: 32, color: "#faad14" }} />;
  }
  if (n.includes("website") || n.includes("integration")) {
    return <GlobalOutlined style={{ fontSize: 32, color: "#fa541c" }} />;
  }
  return <SettingOutlined style={{ fontSize: 32, color: "#8c8c8c" }} />;
};

export const ModuleSelectorHome: React.FC = () => {
  const navigate = useNavigate();
  const [workspaces, setWorkspaces] = useState<WorkspaceMeta[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("/api/resource/Workspace?limit_page_length=50")
      .then((res) => {
        const list: WorkspaceMeta[] = res.data?.data || [];
        // Lọc bỏ các workspace nội bộ ẩn
        const filtered = list.filter(
          (w) => !["Home", "Welcome Workspace"].includes(w.name)
        );
        setWorkspaces(filtered);
      })
      .catch((err) => {
        console.error("Lỗi nạp Workspaces:", err);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "100px" }}>
        <Spin size="large" tip="Đang tải các phân hệ ERPNext..." />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1200, margin: "40px auto", padding: "0 24px" }}>
      <div style={{ textAlign: "center", marginBottom: 48 }}>
        <Title level={2} style={{ margin: "0 0 12px 0", color: "#1f2937" }}>
          Trung Tâm Điều Hành Doanh Nghiệp (ERPNext Workspaces)
        </Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          Chọn phân hệ nghiệp vụ để truy cập bảng điều khiển, chứng từ và báo cáo tương ứng
        </Text>
      </div>

      <Row gutter={[24, 24]}>
        {workspaces.map((ws) => (
          <Col xs={12} sm={8} md={6} lg={4} key={ws.name}>
            <Card
              hoverable
              style={{
                borderRadius: 16,
                textAlign: "center",
                border: "1px solid #f0f0f0",
                boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
                transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                cursor: "pointer",
                padding: "8px 0",
              }}
              bodyStyle={{ padding: "16px 8px" }}
              onClick={() => navigate(`/workspace/${encodeURIComponent(ws.name)}`)}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 16,
                  background: "#f8fafc",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 12px auto",
                }}
              >
                {getModuleIcon(ws.name)}
              </div>
              <Text strong style={{ fontSize: 14, color: "#1f2937", display: "block" }}>
                {ws.title || ws.name}
              </Text>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

