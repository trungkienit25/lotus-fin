import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { List, CreateButton, EditButton, ShowButton, DeleteButton } from "@refinedev/antd";
import { Table, Tag, Typography, Spin, Space, Card, Alert, Badge } from "antd";
import axios from "axios";
import { FieldMeta } from "../../engine/RefineComponentRegistry";

const { Title } = Typography;

export const UniversalListView: React.FC = () => {
  const { doctype: rawDocType } = useParams<{ doctype: string }>();
  const doctype = rawDocType ? decodeURIComponent(rawDocType) : "";
  const navigate = useNavigate();

  const [schema, setSchema] = useState<{ fields: FieldMeta[]; title_field?: string } | null>(null);
  const [loadingSchema, setLoadingSchema] = useState(true);
  const [schemaError, setSchemaError] = useState<string | null>(null);

  // Dữ liệu bảng nạp độc lập từ API
  const [records, setRecords] = useState<any[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loadingData, setLoadingData] = useState<boolean>(true);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(20);

  // 1. Tải Metadata Schema từ Frappe API
  useEffect(() => {
    if (!doctype) return;
    setLoadingSchema(true);
    setSchemaError(null);

    axios
      .get(`/api/method/frappe.desk.form.load.getdoctype?doctype=${encodeURIComponent(doctype)}`)
      .then((res) => {
        const docList = res.data?.docs || [];
        const currentDoc = docList.find((d: any) => d.name === doctype) || docList[0];
        if (currentDoc) {
          setSchema(currentDoc);
        } else {
          setSchemaError(`Không tìm thấy định nghĩa DocType cho "${doctype}"`);
        }
      })
      .catch(async (err) => {
        // Kiểm tra xem liệu đây có phải là một Report bị gõ nhầm /app thay vì /report
        try {
          const reportCheck = await axios.get(`/api/resource/Report/${encodeURIComponent(doctype)}`);
          if (reportCheck.data?.data) {
            navigate(`/report/${encodeURIComponent(doctype)}`, { replace: true });
            return;
          }
        } catch (_) {}

        setSchemaError(err.response?.data?.message || `Lỗi tải schema của DocType "${doctype}"`);
      })
      .finally(() => {
        setLoadingSchema(false);
      });
  }, [doctype]);

  // 2. Tải Dữ liệu bản ghi thực tế từ Frappe REST API chuẩn
  const fetchRecords = async (page: number, size: number) => {
    if (!doctype) return;
    setLoadingData(true);

    const start = (page - 1) * size;

    try {
      // Dùng GET /api/resource/:doctype chuẩn của Frappe REST API
      const res = await axios.get(`/api/resource/${encodeURIComponent(doctype)}`, {
        params: {
          fields: '["*"]',
          limit_start: start,
          limit_page_length: size,
        },
      });

      const items = res.data?.data || [];
      setRecords(items);

      // Gọi get_count
      const countRes = await axios.get(`/api/method/frappe.client.get_count`, {
        params: { doctype },
      });
      setTotalCount(
        typeof countRes.data?.message === "number"
          ? countRes.data?.message
          : items.length
      );
    } catch (err) {
      console.error("Lỗi tải dữ liệu bảng:", err);
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    setCurrentPage(1);
    fetchRecords(1, pageSize);
  }, [doctype]);

  if (loadingSchema) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "64px" }}>
        <Spin size="large" tip={`Đang nạp metadata cấu trúc cho ${doctype}...`} />
      </div>
    );
  }

  if (schemaError) {
    return (
      <Card style={{ margin: "24px" }}>
        <Alert message="Lỗi nạp cấu trúc" description={schemaError} type="error" showIcon />
      </Card>
    );
  }

  // Xác định các trường danh sách:
  // Nếu có title_field mà khác name, ưu tiên đưa vào cột đầu
  const titleFieldName = schema?.title_field;

  let listFields = (schema?.fields || []).filter(
    (f: any) =>
      !f.hidden &&
      !["Section Break", "Column Break", "Table"].includes(f.fieldtype) &&
      (f.in_list_view || f.reqd || f.fieldname === titleFieldName)
  );

  if (listFields.length === 0) {
    listFields = (schema?.fields || [])
      .filter((f: any) => !f.hidden && !["Section Break", "Column Break", "Table"].includes(f.fieldtype))
      .slice(0, 6);
  }

  return (
    <List
      title={<Title level={3} style={{ margin: 0 }}>Danh sách {doctype}</Title>}
      headerButtons={
        <CreateButton
          onClick={() => navigate(`/app/${encodeURIComponent(doctype || "")}/new`)}
        >
          Tạo mới {doctype}
        </CreateButton>
      }
    >
      <Table
        dataSource={records}
        loading={loadingData}
        rowKey="name"
        scroll={{ x: true }}
        bordered
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: totalCount,
          showSizeChanger: true,
          pageSizeOptions: ["10", "20", "50", "100"],
          showTotal: (total) => `Tổng số ${total} bản ghi`,
          onChange: (page, size) => {
            setCurrentPage(page);
            setPageSize(size);
            fetchRecords(page, size);
          },
        }}
      >
        <Table.Column
          dataIndex="name"
          title="ID"
          fixed="left"
          render={(val) => <strong>{val}</strong>}
        />

        {listFields.map((field) => (
          <Table.Column
            key={field.fieldname}
            dataIndex={field.fieldname}
            title={field.label}
            render={(value) => {
              if (value === null || value === undefined || value === "") return "-";
              if (field.fieldtype === "Check") {
                return <Tag color={value ? "green" : "default"}>{value ? "Có" : "Không"}</Tag>;
              }
              if (field.fieldtype === "Currency") {
                return Number(value).toLocaleString();
              }
              if (field.fieldname === "status" || field.fieldname === "workflow_state") {
                const color = value === "Enabled" || value === "Active" || value === "Paid" ? "success" : "default";
                return <Badge status={color as any} text={value} />;
              }
              return String(value);
            }}
          />
        ))}

        <Table.Column
          title="Thao tác"
          dataIndex="actions"
          fixed="right"
          render={(_, record: any) => (
            <Space size="small">
              <ShowButton
                hideText
                size="small"
                recordItemId={record.name}
                onClick={() => navigate(`/app/${encodeURIComponent(doctype || "")}/${encodeURIComponent(record.name)}`)}
              />
              <EditButton
                hideText
                size="small"
                recordItemId={record.name}
                onClick={() => navigate(`/app/${encodeURIComponent(doctype || "")}/${encodeURIComponent(record.name)}`)}
              />
              <DeleteButton
                hideText
                size="small"
                resource={doctype}
                recordItemId={record.name}
              />
            </Space>
          )}
        />
      </Table>
    </List>
  );
};
