import React, { useEffect, useState } from "react";
import { Table, Button, Space, Popconfirm } from "antd";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import axios from "axios";
import { REFINE_COMPONENT_REGISTRY, FieldMeta } from "../RefineComponentRegistry";

interface SubTableControlProps {
  value?: any[];
  onChange?: (val: any[]) => void;
  disabled?: boolean;
  fieldMeta: FieldMeta;
}

export const SubTableControl: React.FC<SubTableControlProps> = ({
  value = [],
  onChange,
  disabled,
  fieldMeta,
}) => {
  const childDocType = fieldMeta.options || "";
  const [childSchema, setChildSchema] = useState<FieldMeta[]>([]);
  const [loading, setLoading] = useState(false);

  // Nạp Metadata của DocType con (Child DocType)
  useEffect(() => {
    if (!childDocType) return;
    setLoading(true);
    axios
      .get(`/api/method/frappe.desk.form.load.getdoctype?doctype=${encodeURIComponent(childDocType)}`)
      .then((res) => {
        const childFields: FieldMeta[] = res.data?.docs?.[0]?.fields || [];
        // Lấy các trường có hiển thị in_list_view hoặc in_grid
        const visibleFields = childFields.filter(
          (f: any) =>
            !f.hidden &&
            !["Section Break", "Column Break"].includes(f.fieldtype) &&
            (f.in_list_view || f.reqd)
        );
        setChildSchema(visibleFields.length > 0 ? visibleFields : childFields.slice(0, 5));
      })
      .catch((err) => {
        console.error("Lỗi nạp child doctype:", err);
      })
      .finally(() => setLoading(false));
  }, [childDocType]);

  const handleCellChange = (rowIndex: number, fieldname: string, cellVal: any) => {
    const updated = [...value];
    updated[rowIndex] = {
      ...updated[rowIndex],
      [fieldname]: cellVal,
    };
    onChange?.(updated);
  };

  const handleAddRow = () => {
    const newRow: any = { idx: value.length + 1 };
    onChange?.([...value, newRow]);
  };

  const handleDeleteRow = (rowIndex: number) => {
    const updated = value.filter((_, idx) => idx !== rowIndex);
    onChange?.(updated);
  };

  const columns = childSchema.map((field) => {
    const Comp = REFINE_COMPONENT_REGISTRY[field.fieldtype] || REFINE_COMPONENT_REGISTRY.Data;

    return {
      title: field.label,
      dataIndex: field.fieldname,
      key: field.fieldname,
      render: (cellVal: any, _: any, rowIndex: number) => (
        <Comp
          value={cellVal}
          onChange={(val) => handleCellChange(rowIndex, field.fieldname, val)}
          disabled={disabled || !!field.read_only}
          fieldMeta={field}
        />
      ),
    };
  });

  return (
    <div style={{ border: "1px solid #f0f0f0", borderRadius: 8, padding: 12, background: "#fafafa" }}>
      <Table
        dataSource={value}
        columns={[
          ...columns,
          {
            title: "",
            key: "actions",
            width: 60,
            render: (_, __, rowIndex) =>
              !disabled && (
                <Popconfirm title="Xóa dòng này?" onConfirm={() => handleDeleteRow(rowIndex)}>
                  <Button type="text" danger icon={<DeleteOutlined />} size="small" />
                </Popconfirm>
              ),
          },
        ]}
        rowKey={(_, idx) => String(idx)}
        pagination={false}
        loading={loading}
        size="small"
        scroll={{ x: true }}
      />
      {!disabled && (
        <Button
          type="dashed"
          onClick={handleAddRow}
          icon={<PlusOutlined />}
          style={{ marginTop: 8, width: "100%" }}
        >
          Thêm dòng mới vào {fieldMeta.label}
        </Button>
      )}
    </div>
  );
};

