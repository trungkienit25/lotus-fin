import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useForm, Create, Edit } from "@refinedev/antd";
import { Form, Button, Card, Spin, Alert, Row, Col, Divider, Space, message } from "antd";
import axios from "axios";
import { REFINE_COMPONENT_REGISTRY, FieldMeta } from "../../engine/RefineComponentRegistry";

export const UniversalFormView: React.FC = () => {
  const { doctype, id } = useParams<{ doctype: string; id?: string }>();
  const navigate = useNavigate();
  const isCreate = !id || id === "new";

  const [schema, setSchema] = useState<{ fields: FieldMeta[] } | null>(null);
  const [loadingSchema, setLoadingSchema] = useState(true);
  const [schemaError, setSchemaError] = useState<string | null>(null);

  // Hook Form của Refine quản lý nạp dữ liệu và lưu tự động
  const { formProps, saveButtonProps, formLoading } = useForm({
    resource: doctype || "",
    action: isCreate ? "create" : "edit",
    id: isCreate ? undefined : id,
    redirect: "list",
  });

  // Tải Metadata Schema từ Frappe
  useEffect(() => {
    if (!doctype) return;
    setLoadingSchema(true);
    setSchemaError(null);

    axios
      .get(`/api/method/frappe.desk.form.load.getdoctype?doctype=${encodeURIComponent(doctype)}`)
      .then((res) => {
        const docInfo = res.data?.docs?.[0];
        if (docInfo) {
          setSchema(docInfo);
        } else {
          setSchemaError(`Không tìm thấy định nghĩa DocType cho "${doctype}"`);
        }
      })
      .catch((err) => {
        setSchemaError(err.response?.data?.message || `Lỗi tải schema của DocType "${doctype}"`);
      })
      .finally(() => {
        setLoadingSchema(false);
      });
  }, [doctype]);

  if (loadingSchema || formLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "64px" }}>
        <Spin size="large" tip="Đang chuẩn bị biểu mẫu nhập liệu..." />
      </div>
    );
  }

  if (schemaError) {
    return (
      <Card style={{ margin: "24px" }}>
        <Alert message="Lỗi biểu mẫu" description={schemaError} type="error" showIcon />
      </Card>
    );
  }

  const Wrapper = isCreate ? Create : Edit;

  return (
    <Wrapper
      title={isCreate ? `Tạo mới ${doctype}` : `Chỉnh sửa: ${id} (${doctype})`}
      saveButtonProps={saveButtonProps}
    >
      <Form {...formProps} layout="vertical">
        <Row gutter={[24, 16]}>
          {(schema?.fields || []).map((field) => {
            // Xử lý Section Break
            if (field.fieldtype === "Section Break") {
              return (
                <Col span={24} key={field.fieldname || Math.random()}>
                  <Divider orientation="left">{field.label || ""}</Divider>
                </Col>
              );
            }

            // Bỏ qua layout break khác hoặc trường bị ẩn
            if (field.fieldtype === "Column Break" || field.hidden) {
              return null;
            }

            // Ánh xạ Component từ Registry, fallback về Data (Input text)
            const FieldComponent = REFINE_COMPONENT_REGISTRY[field.fieldtype] || REFINE_COMPONENT_REGISTRY.Data;

            // Tính toán độ rộng cột (mặc định 12 = nửa màn hình; text dài/bảng = 24 full màn hình)
            const isFullWidth = ["Text", "Text Editor", "Small Text", "Table"].includes(field.fieldtype);
            const colSpan = isFullWidth ? 24 : 12;

            return (
              <Col span={colSpan} key={field.fieldname}>
                <Form.Item
                  name={field.fieldname}
                  label={field.label}
                  rules={[
                    {
                      required: !!field.reqd,
                      message: `Vui lòng nhập ${field.label}`,
                    },
                  ]}
                  valuePropName={field.fieldtype === "Check" ? "checked" : "value"}
                  initialValue={field.default}
                >
                  <FieldComponent
                    fieldMeta={field}
                    disabled={!!field.read_only}
                  />
                </Form.Item>
              </Col>
            );
          })}
        </Row>
      </Form>
    </Wrapper>
  );
};

