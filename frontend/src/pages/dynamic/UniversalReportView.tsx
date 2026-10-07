import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Table,
  Typography,
  Spin,
  Space,
  Card,
  Alert,
  Form,
  Select,
  DatePicker,
  Button,
  Row,
  Col,
  Tag,
} from "antd";
import {
  FilterOutlined,
  ReloadOutlined,
  ArrowLeftOutlined,
  TableOutlined,
} from "@ant-design/icons";
import axios from "axios";
import dayjs from "dayjs";

const { Title, Text } = Typography;

interface ReportColumn {
  label: string;
  fieldname: string;
  fieldtype: string;
  width?: number | string;
  options?: string;
  hidden?: number;
}

export const UniversalReportView: React.FC = () => {
  const { reportName: rawReportName } = useParams<{ reportName: string }>();
  const reportName = rawReportName ? decodeURIComponent(rawReportName) : "";
  const navigate = useNavigate();

  const [form] = Form.useForm();
  const [columns, setColumns] = useState<ReportColumn[]>([]);
  const [dataSource, setDataSource] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Danh sách công ty và năm tài chính cho bộ lọc tiêu chuẩn
  const [companies, setCompanies] = useState<string[]>([]);
  const [fiscalYears, setFiscalYears] = useState<string[]>([]);

  // 1. Nạp danh sách Company và Fiscal Year làm bộ lọc mặc định
  useEffect(() => {
    Promise.all([
      axios.get("/api/resource/Company?limit_page_length=100"),
      axios.get("/api/resource/Fiscal Year?limit_page_length=50"),
    ])
      .then(([compRes, fyRes]) => {
        const compList = (compRes.data?.data || []).map((c: any) => c.name);
        const fyList = (fyRes.data?.data || []).map((f: any) => f.name);
        setCompanies(compList);
        setFiscalYears(fyList);

        // Thiết lập bộ lọc mặc định
        const defaultCompany =
          compList.find((c: string) => c.includes("Demo")) || compList[0] || "Lotus-fin";
        const currentYear = new Date().getFullYear();
        const defaultFy =
          fyList.find((f: string) => f.includes(String(currentYear))) ||
          fyList[0] ||
          "2025";

        form.setFieldsValue({
          company: defaultCompany,
          fiscal_year: defaultFy,
          date_range: [
            dayjs().startOf("year"),
            dayjs().endOf("year"),
          ],
        });

        // Tự động chạy báo cáo với filter mặc định
        executeReport({
          company: defaultCompany,
          fiscal_year: defaultFy,
          from_date: dayjs().startOf("year").format("YYYY-MM-DD"),
          to_date: dayjs().endOf("year").format("YYYY-MM-DD"),
        });
      })
      .catch((err) => {
        console.error("Lỗi nạp metadata filter báo cáo:", err);
        // Chạy với filter fallback
        executeReport({
          company: "Lotus-fin (Demo)",
          fiscal_year: "2025",
          from_date: "2025-01-01",
          to_date: "2026-12-31",
        });
      });
  }, [reportName]);

  // 2. Hàm gọi API chạy báo cáo frappe.desk.query_report.run
  const executeReport = async (filters: any) => {
    if (!reportName) return;
    setLoading(true);
    setError(null);

    try {
      const res = await axios.post("/api/method/frappe.desk.query_report.run", {
        report_name: reportName,
        filters: filters,
      });

      const message = res.data?.message;
      if (!message) {
        throw new Error("Không nhận được dữ liệu kết quả từ hệ thống báo cáo.");
      }

      const cols: ReportColumn[] = (message.columns || []).map((col: any) => {
        if (typeof col === "string") {
          const parts = col.split(":");
          return {
            label: parts[0] || col,
            fieldname: (parts[0] || col).toLowerCase().replace(/\s+/g, "_"),
            fieldtype: parts[1] || "Data",
            width: parts[2] ? parseInt(parts[2]) : undefined,
          };
        }
        return col;
      });

      setColumns(cols.filter((c) => !c.hidden));
      setDataSource(message.result || []);
    } catch (err: any) {
      console.error(`Lỗi thực thi báo cáo ${reportName}:`, err);
      // Đọc server messages nếu có
      let errMsg =
        err.response?.data?.message ||
        err.response?.data?.exc ||
        err.message ||
        `Lỗi khi chạy báo cáo "${reportName}"`;

      if (err.response?.data?._server_messages) {
        try {
          const smsgs = JSON.parse(err.response.data._server_messages);
          const first = JSON.parse(smsgs[0]);
          if (first?.message) {
            errMsg = first.message.replace(/<[^>]+>/g, ""); // Strip HTML tags
          }
        } catch (_) {}
      }
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterSubmit = (values: any) => {
    const filters: any = {
      company: values.company,
      fiscal_year: values.fiscal_year,
    };
    if (values.date_range && values.date_range.length === 2) {
      filters.from_date = values.date_range[0].format("YYYY-MM-DD");
      filters.to_date = values.date_range[1].format("YYYY-MM-DD");
    }
    executeReport(filters);
  };

  return (
    <div style={{ maxWidth: 1600, margin: "0 auto", paddingBottom: 48 }}>
      {/* Header Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <Space align="center" size="middle">
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(-1)}
            style={{ borderRadius: 6 }}
          >
            Quay lại
          </Button>
          <Title level={3} style={{ margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
            <TableOutlined style={{ color: "#1677ff" }} />
            {reportName}
          </Title>
          <Tag color="blue">Report View</Tag>
        </Space>

        <Button
          type="primary"
          icon={<ReloadOutlined />}
          onClick={() => {
            const values = form.getFieldsValue();
            handleFilterSubmit(values);
          }}
          loading={loading}
        >
          Làm mới dữ liệu
        </Button>
      </div>

      {/* Form bộ lọc báo cáo */}
      <Card
        style={{
          marginBottom: 20,
          borderRadius: 8,
          boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
        }}
        bodyStyle={{ padding: "16px 20px" }}
      >
        <Form
          form={form}
          layout="inline"
          onFinish={handleFilterSubmit}
          style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" }}
        >
          <Form.Item name="company" label="Công ty" style={{ marginBottom: 8 }}>
            <Select style={{ width: 220 }} placeholder="Chọn công ty">
              {companies.map((c) => (
                <Select.Option key={c} value={c}>
                  {c}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="fiscal_year" label="Năm tài chính" style={{ marginBottom: 8 }}>
            <Select style={{ width: 140 }} placeholder="Năm tài chính">
              {fiscalYears.map((fy) => (
                <Select.Option key={fy} value={fy}>
                  {fy}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="date_range" label="Khoảng ngày" style={{ marginBottom: 8 }}>
            <DatePicker.RangePicker format="YYYY-MM-DD" style={{ width: 260 }} />
          </Form.Item>

          <Form.Item style={{ marginBottom: 8 }}>
            <Button
              type="default"
              htmlType="submit"
              icon={<FilterOutlined />}
              loading={loading}
            >
              Lọc kết quả
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* Thông báo lỗi nếu có */}
      {error && (
        <Alert
          message="Thông báo từ hệ thống Báo cáo"
          description={error}
          type="warning"
          showIcon
          style={{ marginBottom: 20 }}
        />
      )}

      {/* Bảng dữ liệu Báo cáo */}
      <Card
        style={{
          borderRadius: 8,
          boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
        }}
        bodyStyle={{ padding: 0 }}
      >
        <Table
          dataSource={dataSource}
          rowKey={(record, index) => record.name || record.gl_entry || `row-${index}`}
          loading={loading}
          scroll={{ x: "max-content", y: 600 }}
          bordered
          size="middle"
          pagination={{
            pageSize: 50,
            showSizeChanger: true,
            pageSizeOptions: ["20", "50", "100", "200"],
            showTotal: (total) => `Tổng số ${total} dòng kết quả`,
          }}
          columns={columns.map((col) => ({
            title: col.label,
            dataIndex: col.fieldname,
            key: col.fieldname,
            width: col.width || 150,
            render: (value: any, record: any) => {
              if (value === null || value === undefined || value === "") return "-";
              if (col.fieldtype === "Currency" || col.fieldtype === "Float") {
                const num = Number(value);
                if (isNaN(num)) return value;
                return (
                  <span
                    style={{
                      fontVariantNumeric: "tabular-nums",
                      fontWeight: record.account?.includes("Total") ? 600 : "normal",
                      color: num < 0 ? "#cf1322" : "inherit",
                    }}
                  >
                    {num.toLocaleString("vi-VN", { minimumFractionDigits: 2 })}
                  </span>
                );
              }
              if (col.fieldtype === "Date") {
                return value;
              }
              if (col.fieldtype === "Link" && typeof value === "string") {
                return (
                  <a
                    onClick={() => {
                      if (col.options) {
                        navigate(`/app/${encodeURIComponent(col.options)}/${encodeURIComponent(value)}`);
                      }
                    }}
                  >
                    {value}
                  </a>
                );
              }
              return (
                <span style={{ fontWeight: record.account?.includes("Total") ? 600 : "normal" }}>
                  {String(value)}
                </span>
              );
            },
          }))}
        />
      </Card>
    </div>
  );
};

