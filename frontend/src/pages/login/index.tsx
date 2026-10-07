import React, { useState } from "react";
import { useLogin } from "@refinedev/core";
import { Form, Input, Button, Card, Typography, Alert } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;

export const LoginPage: React.FC = () => {
  const { mutate: login, isPending } = useLogin();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const onFinish = (values: any) => {
    setErrorMessage(null);
    login(
      { email: values.email, password: values.password },
      {
        onError: (error: any) => {
          setErrorMessage(error?.message || "Đăng nhập thất bại");
        },
      }
    );
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
      }}
    >
      <Card
        style={{
          width: 420,
          borderRadius: 12,
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.3)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <Title level={2} style={{ margin: 0, color: "#1677ff" }}>
            Lotus Fin
          </Title>
          <Text type="secondary">Cổng Quản Trị Tài Chính & Doanh Nghiệp Thông Minh</Text>
        </div>

        {errorMessage && (
          <Alert
            message={errorMessage}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        <Form layout="vertical" onFinish={onFinish} initialValues={{ email: "Administrator", password: "" }}>
          <Form.Item
            name="email"
            label="Tên đăng nhập / Email"
            rules={[{ required: true, message: "Vui lòng nhập tài khoản!" }]}
          >
            <Input prefix={<UserOutlined />} placeholder="Ví dụ: Administrator" size="large" />
          </Form.Item>

          <Form.Item
            name="password"
            label="Mật khẩu"
            rules={[{ required: true, message: "Vui lòng nhập mật khẩu!" }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Mật khẩu" size="large" />
          </Form.Item>

          <Form.Item style={{ marginTop: 24 }}>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              loading={isPending}
            >
              Đăng nhập hệ thống
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

