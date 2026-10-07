import React, { useState } from "react";
import { FloatButton, Drawer, Input, Button, List, Typography, Space, Tag, Spin } from "antd";
import { RobotOutlined, SendOutlined } from "@ant-design/icons";
import axios from "axios";

const { Text, Paragraph } = Typography;

interface ChatMessage {
  sender: "user" | "assistant";
  content: string;
  toolCalls?: string[];
  widget?: any;
}

export const LotusCopilotDrawer: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: "assistant",
      content: "Xin chào! Tôi là Lotus Copilot. Tôi có thể hỗ trợ bạn đối soát dòng tiền, tính chỉ số sức khỏe tài chính và mô phỏng kịch bản What-If.",
    },
  ]);
  const [loading, setLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userText = inputMessage;
    setInputMessage("");
    setMessages((prev) => [...prev, { sender: "user", content: userText }]);
    setLoading(true);

    try {
      const res = await axios.post("/api/method/lotus_fin.presentation.controller.copilot_controller.handle_send_message", {
        message: userText,
      });

      const responseData = res.data?.message;
      if (responseData) {
        setMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            content: responseData.reply || "Đã xử lý tác vụ.",
            toolCalls: responseData.executed_tools,
            widget: responseData.ui_widget,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            sender: "assistant",
            content: "Đã ghi nhận yêu cầu nhưng không nhận được phản hồi phù hợp.",
          },
        ]);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          content: `Lỗi kết nối Copilot: ${err.response?.data?.message || err.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <FloatButton
        icon={<RobotOutlined />}
        type="primary"
        style={{ right: 24, bottom: 24, width: 56, height: 56 }}
        tooltip="Mở Trợ Lý Tài Chính Lotus Copilot"
        onClick={() => setOpen(true)}
      />

      <Drawer
        title={
          <Space>
            <RobotOutlined style={{ color: "#1677ff", fontSize: 20 }} />
            <span>Lotus Copilot (AI Financial Advisor)</span>
          </Space>
        }
        placement="right"
        width={450}
        onClose={() => setOpen(false)}
        open={open}
      >
        <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
          <div style={{ flex: 1, overflowY: "auto", marginBottom: 16 }}>
            <List
              itemLayout="horizontal"
              dataSource={messages}
              renderItem={(item) => (
                <div
                  style={{
                    marginBottom: 16,
                    textAlign: item.sender === "user" ? "right" : "left",
                  }}
                >
                  <div
                    style={{
                      display: "inline-block",
                      maxWidth: "85%",
                      padding: "10px 14px",
                      borderRadius: 10,
                      background: item.sender === "user" ? "#1677ff" : "#f0f2f5",
                      color: item.sender === "user" ? "#fff" : "#000",
                      textAlign: "left",
                    }}
                  >
                    <Paragraph style={{ margin: 0, color: item.sender === "user" ? "#fff" : "#000" }}>
                      {item.content}
                    </Paragraph>

                    {item.toolCalls && item.toolCalls.length > 0 && (
                      <div style={{ marginTop: 8 }}>
                        <Text type="secondary" style={{ fontSize: 11, display: "block" }}>
                          Công cụ đã kích hoạt:
                        </Text>
                        <Space wrap size={[0, 4]}>
                          {item.toolCalls.map((t) => (
                            <Tag color="blue" key={t}>
                              {t}
                            </Tag>
                          ))}
                        </Space>
                      </div>
                    )}
                  </div>
                </div>
              )}
            />
            {loading && (
              <div style={{ textAlign: "center", padding: 8 }}>
                <Spin tip="AI đang phân tích sổ cái & tính toán..." />
              </div>
            )}
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            <Input.TextArea
              rows={2}
              placeholder="Hỏi về dòng tiền, chỉ số nợ, hoặc mô phỏng What-If..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              style={{ height: "auto" }}
              onClick={handleSendMessage}
              loading={loading}
            />
          </div>
        </div>
      </Drawer>
    </>
  );
};

