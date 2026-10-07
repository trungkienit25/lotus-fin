import React from "react";
import { Select } from "antd";
import { useSelect } from "@refinedev/antd";

interface RefineLinkControlProps {
  targetDocType: string;
  value?: string;
  onChange?: (val: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const RefineLinkControl: React.FC<RefineLinkControlProps> = ({
  targetDocType,
  value,
  onChange,
  disabled,
  placeholder,
}) => {
  const { selectProps } = useSelect({
    resource: targetDocType,
    optionLabel: "name",
    optionValue: "name",
    debounce: 300,
    pagination: {
      pageSize: 20,
    },
    onSearch: (searchTerm) => [
      {
        field: "name",
        operator: "contains",
        value: searchTerm,
      },
    ],
  });

  return (
    <Select
      {...(selectProps as any)}
      showSearch
      allowClear
      value={value}
      onChange={onChange}
      disabled={disabled}
      placeholder={placeholder || `Chọn ${targetDocType}...`}
      style={{ width: "100%" }}
    />
  );
};

