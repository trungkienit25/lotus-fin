import React, { useEffect, useState } from "react";
import { Layout, Menu, Typography, Avatar, Button, Space, Spin, Input, Breadcrumb } from "antd";
import {
  BankOutlined,
  LogoutOutlined,
  UserOutlined,
  AppstoreOutlined,
  SearchOutlined,
  HomeOutlined,
  FolderOutlined,
  FileTextOutlined,
  RightOutlined,
} from "@ant-design/icons";
import { useNavigate, useLocation } from "react-router-dom";
import { useLogout, useGetIdentity } from "@refinedev/core";
import axios from "axios";
import { LotusCopilotDrawer } from "../copilot/LotusCopilotDrawer";

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

interface SidebarItem {
  label: string;
  type: string; // "Link" | "Section Break"
  link_type?: string;
  link_to?: string;
  icon?: string;
}

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { mutate: logout } = useLogout();
  const { data: identity } = useGetIdentity<{ name: string }>();

  // Xác định Workspace hiện tại dựa trên route hoặc lưu trữ
  const currentPath = location.pathname;
  const isHomePage = currentPath === "/" || currentPath === "/home";

  let activeWorkspace = "Invoicing";
  if (currentPath.startsWith("/workspace/")) {
    activeWorkspace = decodeURIComponent(currentPath.replace("/workspace/", ""));
  }

  const [sidebarItems, setSidebarItems] = useState<SidebarItem[]>([]);
  const [loadingSidebar, setLoadingSidebar] = useState(false);
  const [doctypes, setDoctypes] = useState<{ name: string }[]>([]);
  const [searchDocType, setSearchDocType] = useState("");

  // 1. Tải danh mục Sidebar chuẩn từ Workspace Sidebar của ERPNext Desk
  useEffect(() => {
    if (isHomePage) return;

    setLoadingSidebar(true);
    axios
      .get(`/api/resource/Workspace Sidebar/${encodeURIComponent(activeWorkspace)}`)
      .then((res) => {
        const items = res.data?.data?.items || [];
        setSidebarItems(items);
      })
      .catch(() => {
        // Fallback nạp từ Workspace links thông thường nếu không có Workspace Sidebar
        axios.get(`/api/resource/Workspace/${encodeURIComponent(activeWorkspace)}`).then((res) => {
          const links = res.data?.data?.links || [];
          const converted = links.map((l: any) => ({
            label: l.label,
            type: l.type === "Card Break" ? "Section Break" : "Link",
            link_to: l.link_to || l.label,
            link_type: l.link_type,
          }));
          setSidebarItems(converted);
        });
      })
      .finally(() => setLoadingSidebar(false));
  }, [activeWorkspace, isHomePage]);

  // 2. Tải toàn bộ danh sách DocType để phục vụ tìm kiếm nhanh (Ctrl+K)
  useEffect(() => {
    axios
      .get("/api/resource/DocType?limit_page_length=1000")
      .then((res) => setDoctypes(res.data?.data || []))
      .catch(() => {});
  }, []);

  // Xây dựng các nhóm Menu từ mảng sidebarItems (nhóm theo Section Break như Receivables, Payables, Payments...)
  const menuGroups: any[] = [
    {
      key: `/workspace/${encodeURIComponent(activeWorkspace)}`,
      icon: <HomeOutlined />,
      label: "Home",
    },
  ];

  let currentSection: any = null;

  sidebarItems.forEach((item, idx) => {
    if (item.type === "Section Break") {
      if (currentSection) {
        menuGroups.push(currentSection);
      }
      currentSection = {
        key: `section-${idx}`,
        label: item.label,
        children: [],
      };
    } else if (item.type === "Link" && (item.link_to || item.label)) {
      const linkTarget = item.link_to || item.label;
      let targetUrl = `/app/${encodeURIComponent(linkTarget)}`;

      if (item.link_type === "Workspace") {
        targetUrl = `/workspace/${encodeURIComponent(linkTarget)}`;
      } else if (item.link_type === "Dashboard") {
        targetUrl = `/workspace/${encodeURIComponent(activeWorkspace)}`;
      } else if (
        item.link_type === "Report" ||
        item.link_type === "Query Report" ||
        item.link_type === "Script Report"
      ) {
        targetUrl = `/report/${encodeURIComponent(linkTarget)}`;
      }

      const menuItem = {
        key: targetUrl,
        label: item.label,
      };

      if (currentSection) {
        currentSection.children.push(menuItem);
      } else {
        menuGroups.push(menuItem);
      }
    }
  });

  if (currentSection && currentSection.children.length > 0) {
    menuGroups.push(currentSection);
  }

  // Kết quả tìm kiếm
  const searchResults = searchDocType.trim()
    ? doctypes
        .filter((d) => d.name.toLowerCase().includes(searchDocType.toLowerCase()))
        .slice(0, 30)
    : [];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      {/* Chỉ hiển thị Sidebar khi không ở trang chủ chọn Module */}
      {!isHomePage && (
        <Sider
          width={260}
          theme="light"
          style={{
            borderRight: "1px solid #f0f0f0",
            height: "100vh",
            position: "sticky",
            top: 0,
            left: 0,
            overflowY: "auto",
          }}
        >
          {/* Header Sidebar với nút quay về danh sách Module Home */}
          <div style={{ padding: "16px 16px 12px 16px", borderBottom: "1px solid #f0f0f0" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                cursor: "pointer",
                marginBottom: 8,
              }}
              onClick={() => navigate("/home")}
            >
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 8,
                  background: "#1677ff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#fff",
                }}
              >
                <BankOutlined style={{ fontSize: 18 }} />
              </div>
              <div>
                <Title level={5} style={{ margin: 0, lineHeight: 1.2 }}>
                  {activeWorkspace}
                </Title>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  ERPNext Core
                </Text>
              </div>
            </div>

            <Input
              placeholder="Search (Ctrl+K)..."
              prefix={<SearchOutlined />}
              value={searchDocType}
              onChange={(e) => setSearchDocType(e.target.value)}
              allowClear
              size="small"
              style={{ marginTop: 8 }}
            />
          </div>

          {loadingSidebar ? (
            <div style={{ textAlign: "center", padding: "40px 0" }}>
              <Spin size="small" tip="Nạp danh mục sidebar..." />
            </div>
          ) : searchDocType.trim() && searchResults.length > 0 ? (
            <Menu
              mode="inline"
              selectedKeys={[location.pathname]}
              items={searchResults.map((d) => ({
                key: `/app/${encodeURIComponent(d.name)}`,
                icon: <FileTextOutlined />,
                label: d.name,
              }))}
              onClick={({ key }) => navigate(key)}
            />
          ) : (
            <Menu
              mode="inline"
              selectedKeys={[location.pathname]}
              defaultOpenKeys={menuGroups.map((g) => g.key)}
              items={menuGroups}
              onClick={({ key }) => {
                if (key.startsWith("/")) navigate(key);
              }}
              style={{ borderRight: 0 }}
            />
          )}
        </Sider>
      )}

      <Layout>
        <Header
          style={{
            background: "#fff",
            padding: "0 24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "1px solid #f0f0f0",
          }}
        >
          <Space>
            <Button
              type="text"
              icon={<AppstoreOutlined />}
              onClick={() => navigate("/home")}
            >
              Chọn Phân Hệ
            </Button>
            <Text type="secondary">|</Text>
            <Breadcrumb
              items={[
                { title: <span style={{ cursor: "pointer" }} onClick={() => navigate("/home")}>Trang Chủ</span> },
                {
                  title: (
                    <span
                      style={{ cursor: "pointer" }}
                      onClick={() => navigate(`/workspace/${encodeURIComponent(activeWorkspace)}`)}
                    >
                      {activeWorkspace}
                    </span>
                  ),
                },
                {
                  title: currentPath.startsWith("/app/")
                    ? decodeURIComponent(currentPath.replace("/app/", ""))
                    : currentPath.startsWith("/report/")
                    ? decodeURIComponent(currentPath.replace("/report/", ""))
                    : "Dashboard",
                },
              ]}
            />
          </Space>

          <Space size="middle">
            <Space>
              <Avatar icon={<UserOutlined />} style={{ backgroundColor: "#1677ff" }} />
              <Text strong>{identity?.name || "Administrator"}</Text>
            </Space>
            <Button
              type="text"
              icon={<LogoutOutlined />}
              onClick={() => logout()}
            >
              Đăng xuất
            </Button>
          </Space>
        </Header>

        <Content style={{ margin: "24px", minHeight: 280 }}>
          {children}
        </Content>
      </Layout>

      {/* Floating AI Copilot Widget */}
      <LotusCopilotDrawer />
    </Layout>
  );
};
