import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Row, Col, Typography, Spin, Space, Tag, Divider, Empty, Statistic } from "antd";
import {
  FileTextOutlined,
  RightOutlined,
  ThunderboltOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
} from "@ant-design/icons";
import axios from "axios";

const { Title, Text } = Typography;

interface WorkspaceLink {
  label: string;
  type: string; // "Link" | "Card Break"
  link_type: string; // "DocType" | "Page" | "Report"
  link_to?: string;
  hidden?: number;
  onboard?: number;
}

interface WorkspaceData {
  name: string;
  title: string;
  links?: WorkspaceLink[];
  content?: string;
}

export const UniversalWorkspaceView: React.FC = () => {
  const { workspaceName } = useParams<{ workspaceName: string }>();
  const navigate = useNavigate();

  const [workspace, setWorkspace] = useState<WorkspaceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!workspaceName) return;
    setLoading(true);
    setError(null);

    axios
      .get(`/api/resource/Workspace/${encodeURIComponent(workspaceName)}`)
      .then((res) => {
        setWorkspace(res.data?.data);
      })
      .catch((err) => {
        setError(err.response?.data?.message || `Không tải được Workspace "${workspaceName}"`);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [workspaceName]);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "80px" }}>
        <Spin size="large" tip="Đang tải Module Workspace từ ERPNext..." />
      </div>
    );
  }

  if (error || !workspace) {
    return (
      <Card style={{ margin: 24 }}>
        <Empty description={error || "Không tìm thấy Workspace"} />
      </Card>
    );
  }

  // Gom các link theo từng nhóm Card Break (Accounting Masters, Payments, Tax Masters...)
  const cardSections: { title: string; links: WorkspaceLink[] }[] = [];
  let currentSection: { title: string; links: WorkspaceLink[] } = {
    title: "Phổ biến & Tổng quan",
    links: [],
  };

  (workspace.links || []).forEach((link) => {
    if (link.type === "Card Break") {
      if (currentSection.links.length > 0) {
        cardSections.push(currentSection);
      }
      currentSection = {
        title: link.label,
        links: [],
      };
    } else if (link.type === "Link" && !link.hidden) {
      currentSection.links.push(link);
    }
  });
  if (currentSection.links.length > 0) {
    cardSections.push(currentSection);
  }

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto", paddingBottom: 48 }}>
      {/* 1. Dashboard Metrics Summary (Outgoing Bills, Incoming Bills, Incoming Payment, Outgoing Payment) */}
      <div style={{ marginBottom: 28 }}>
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={6}>
            <Card bordered={false} style={{ borderRadius: 10, boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
              <Statistic
                title={<Text type="secondary">Outgoing Bills</Text>}
                value="363,00 K"
                prefix={<span style={{ fontSize: 13, marginRight: 4 }}>VND</span>}
                valueStyle={{ color: "#1f2937", fontWeight: 700 }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card bordered={false} style={{ borderRadius: 10, boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
              <Statistic
                title={<Text type="secondary">Incoming Bills</Text>}
                value="349,15 K"
                prefix={<span style={{ fontSize: 13, marginRight: 4 }}>VND</span>}
                valueStyle={{ color: "#1f2937", fontWeight: 700 }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card bordered={false} style={{ borderRadius: 10, boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
              <Statistic
                title={<Text type="secondary">Incoming Payment</Text>}
                value="47,00 K"
                prefix={<span style={{ fontSize: 13, marginRight: 4 }}>VND</span>}
                valueStyle={{ color: "#52c41a", fontWeight: 700 }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card bordered={false} style={{ borderRadius: 10, boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
              <Statistic
                title={<Text type="secondary">Outgoing Payment</Text>}
                value="164,85 K"
                prefix={<span style={{ fontSize: 13, marginRight: 4 }}>VND</span>}
                valueStyle={{ color: "#fa8c16", fontWeight: 700 }}
              />
            </Card>
          </Col>
        </Row>
      </div>

      {/* 2. Reports & Masters Grid (Accounting Masters, Payments, Tax Masters...) */}
      <div style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: "0 0 16px 0", color: "#374151" }}>
          Reports & Masters
        </Title>
        <Row gutter={[20, 20]}>
          {cardSections.map((section, idx) => (
            <Col xs={24} sm={12} lg={8} key={idx}>
              <Card
                title={<span style={{ fontWeight: 600, fontSize: 15 }}>{section.title}</span>}
                bordered={false}
                style={{
                  borderRadius: 10,
                  boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                  height: "100%",
                }}
                bodyStyle={{ padding: "12px 16px" }}
              >
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {section.links.map((link, lIdx) => (
                    <div
                      key={lIdx}
                      style={{
                        padding: "6px 10px",
                        borderRadius: 6,
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        cursor: "pointer",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "#f3f4f6")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                      onClick={() => {
                        const target = link.link_to || link.label;
                        if (
                          link.link_type === "Report" ||
                          link.link_type === "Query Report" ||
                          link.link_type === "Script Report"
                        ) {
                          navigate(`/report/${encodeURIComponent(target)}`);
                        } else if (link.link_type === "Workspace") {
                          navigate(`/workspace/${encodeURIComponent(target)}`);
                        } else {
                          navigate(`/app/${encodeURIComponent(target)}`);
                        }
                      }}
                    >
                      <Space>
                        <Text style={{ fontSize: 13 }}>{link.label}</Text>
                        {link.onboard ? <Tag color="green" style={{ fontSize: 10, lineHeight: "16px", padding: "0 4px" }}>Chính</Tag> : null}
                      </Space>
                      <RightOutlined style={{ fontSize: 10, color: "#9ca3af" }} />
                    </div>
                  ))}
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </div>
  );
};
