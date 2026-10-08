import { DataProvider, CrudFilters } from "@refinedev/core";
import axios from "axios";

// Hàm chuyển đổi Refine CrudFilters sang cấu trúc Filter của Frappe
const transformFilters = (filters?: CrudFilters) => {
  if (!filters || filters.length === 0) return undefined;

  const frappeFilters: any[] = [];
  filters.forEach((filter) => {
    if ("field" in filter) {
      let operator = "=";
      if (filter.operator === "eq") operator = "=";
      else if (filter.operator === "ne") operator = "!=";
      else if (filter.operator === "lt") operator = "<";
      else if (filter.operator === "lte") operator = "<=";
      else if (filter.operator === "gt") operator = ">";
      else if (filter.operator === "gte") operator = ">=";
      else if (filter.operator === "contains") operator = "like";
      else if (filter.operator === "in") operator = "in";

      const val = filter.operator === "contains" ? `%${filter.value}%` : filter.value;
      frappeFilters.push([filter.field, operator, val]);
    }
  });

  return frappeFilters.length > 0 ? JSON.stringify(frappeFilters) : undefined;
};

export const dataProvider: DataProvider = {
  // 1. Lấy danh sách bản ghi đầy đủ các trường (Full Data Record)
  getList: async ({ resource, pagination, filters, sorters }: any) => {
    const current = pagination?.current || 1;
    const pageSize = pagination?.pageSize || 20;
    const start = (current - 1) * pageSize;

    // Dùng endpoint RPC frappe.client.get_list với fields=* để trả về toàn bộ dữ liệu cột
    const params = new URLSearchParams();
    params.append("doctype", resource);
    params.append("fields", "*");
    params.append("limit_start", String(start));
    params.append("limit_page_length", String(pageSize));

    const frappeFilters = transformFilters(filters);
    if (frappeFilters) {
      params.append("filters", frappeFilters);
    }

    if (sorters && sorters.length > 0) {
      const sortField = sorters[0].field;
      const sortOrder = sorters[0].order === "asc" ? "asc" : "desc";
      params.append("order_by", `${sortField} ${sortOrder}`);
    }

    const { data } = await axios.post("/api/method/frappe.client.get_list", params, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    const items = data.message || [];

    return {
      data: items,
      total: items.length < pageSize ? start + items.length : start + pageSize + 1,
    };
  },

  // 2. Lấy chi tiết 1 bản ghi
  getOne: async ({ resource, id }) => {
    const { data } = await axios.get(`/api/resource/${encodeURIComponent(resource)}/${encodeURIComponent(String(id))}`);
    return {
      data: data.data || {},
    };
  },

  // 3. Tạo mới bản ghi
  create: async ({ resource, variables }) => {
    const { data } = await axios.post(`/api/resource/${encodeURIComponent(resource)}`, variables);
    return {
      data: data.data || {},
    };
  },

  // 4. Cập nhật bản ghi
  update: async ({ resource, id, variables }) => {
    const { data } = await axios.put(`/api/resource/${encodeURIComponent(resource)}/${encodeURIComponent(String(id))}`, variables);
    return {
      data: data.data || {},
    };
  },

  // 5. Xóa bản ghi
  deleteOne: async ({ resource, id }) => {
    await axios.delete(`/api/resource/${encodeURIComponent(resource)}/${encodeURIComponent(String(id))}`);
    return {
      data: { id } as any,
    };
  },

  getApiUrl: () => "/api/resource",
};
