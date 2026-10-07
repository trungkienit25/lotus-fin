import React from "react";
import { Input, InputNumber, Select, Checkbox, DatePicker } from "antd";
import dayjs from "dayjs";
import { RefineLinkControl } from "./controls/RefineLinkControl";
import { SubTableControl } from "./controls/SubTableControl";

export interface FieldMeta {
  fieldname: string;
  fieldtype: string;
  label: string;
  options?: string;
  reqd?: number;
  read_only?: number;
  description?: string;
  default?: any;
  hidden?: number | boolean;
  in_list_view?: number;
}

export interface FieldComponentProps {
  value?: any;
  onChange?: (val: any) => void;
  disabled?: boolean;
  fieldMeta: FieldMeta;
}

export const REFINE_COMPONENT_REGISTRY: Record<string, React.FC<FieldComponentProps>> = {
  // 1. Text thông thường
  Data: ({ value, onChange, disabled, fieldMeta }) => (
    <Input
      placeholder={`Nhập ${fieldMeta.label}...`}
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
    />
  ),

  SmallText: ({ value, onChange, disabled, fieldMeta }) => (
    <Input.TextArea
      placeholder={`Nhập ${fieldMeta.label}...`}
      rows={2}
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
    />
  ),

  Text: ({ value, onChange, disabled, fieldMeta }) => (
    <Input.TextArea
      placeholder={`Nhập ${fieldMeta.label}...`}
      rows={4}
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
    />
  ),

  "Text Editor": ({ value, onChange, disabled, fieldMeta }) => (
    <Input.TextArea
      placeholder={`Soạn thảo ${fieldMeta.label}...`}
      rows={5}
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
    />
  ),

  // 2. Số và Tiền tệ
  Currency: ({ value, onChange, disabled, fieldMeta }) => (
    <InputNumber
      style={{ width: "100%" }}
      placeholder={`Nhập ${fieldMeta.label}...`}
      value={value}
      onChange={onChange}
      formatter={(val) => `${val}`.replace(/\B(?=(\d{3})+(?!\d))/g, ",")}
      disabled={disabled}
    />
  ),

  Int: ({ value, onChange, disabled, fieldMeta }) => (
    <InputNumber
      style={{ width: "100%" }}
      placeholder={`Nhập ${fieldMeta.label}...`}
      precision={0}
      value={value}
      onChange={onChange}
      disabled={disabled}
    />
  ),

  Float: ({ value, onChange, disabled, fieldMeta }) => (
    <InputNumber
      style={{ width: "100%" }}
      placeholder={`Nhập ${fieldMeta.label}...`}
      precision={2}
      value={value}
      onChange={onChange}
      disabled={disabled}
    />
  ),

  Percent: ({ value, onChange, disabled, fieldMeta }) => (
    <InputNumber
      style={{ width: "100%" }}
      placeholder={`Nhập ${fieldMeta.label}...`}
      addonAfter="%"
      value={value}
      onChange={onChange}
      disabled={disabled}
    />
  ),

  // 3. Dropdown cố định (Select)
  Select: ({ value, onChange, disabled, fieldMeta }) => {
    const rawOptions = fieldMeta.options || "";
    const options = rawOptions
      .split("\n")
      .map((opt) => opt.trim())
      .filter(Boolean)
      .map((opt) => ({ label: opt, value: opt }));

    return (
      <Select
        style={{ width: "100%" }}
        placeholder={`Chọn ${fieldMeta.label}...`}
        allowClear
        value={value}
        onChange={onChange}
        options={options}
        disabled={disabled}
      />
    );
  },

  // 4. Boolean / Checkbox
  Check: ({ value, onChange, disabled }) => (
    <Checkbox
      checked={!!value}
      onChange={(e) => onChange?.(e.target.checked ? 1 : 0)}
      disabled={disabled}
    />
  ),

  // 5. Ngày giờ
  Date: ({ value, onChange, disabled }) => (
    <DatePicker
      style={{ width: "100%" }}
      value={value ? dayjs(value) : null}
      onChange={(date) => onChange?.(date ? date.format("YYYY-MM-DD") : null)}
      disabled={disabled}
    />
  ),

  Datetime: ({ value, onChange, disabled }) => (
    <DatePicker
      showTime
      style={{ width: "100%" }}
      value={value ? dayjs(value) : null}
      onChange={(date) => onChange?.(date ? date.format("YYYY-MM-DD HH:mm:ss") : null)}
      disabled={disabled}
    />
  ),

  // 6. Khóa ngoại Link
  Link: ({ value, onChange, disabled, fieldMeta }) => (
    <RefineLinkControl
      targetDocType={fieldMeta.options || ""}
      value={value}
      onChange={onChange}
      disabled={disabled}
      placeholder={`Chọn ${fieldMeta.label}...`}
    />
  ),

  // 7. Bảng dữ liệu con (Child Table)
  Table: ({ value, onChange, disabled, fieldMeta }) => (
    <SubTableControl
      value={value}
      onChange={onChange}
      disabled={disabled}
      fieldMeta={fieldMeta}
    />
  ),
};
