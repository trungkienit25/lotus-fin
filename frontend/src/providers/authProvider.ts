import { AuthProvider } from "@refinedev/core";
import axios from "axios";

// Đảm bảo mọi request đều gửi kèm cookie session của Frappe (sid)
axios.defaults.withCredentials = true;

export const authProvider: AuthProvider = {
  login: async ({ email, password }) => {
    try {
      // Frappe endpoint /api/method/login yêu cầu application/x-www-form-urlencoded
      const params = new URLSearchParams();
      params.append("usr", email || "");
      params.append("pwd", password || "");

      const response = await axios.post("/api/method/login", params, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      if (response.data?.message === "Logged In") {
        return {
          success: true,
          redirectTo: "/",
        };
      }

      return {
        success: false,
        error: {
          name: "LoginError",
          message: "Đăng nhập thất bại. Vui lòng kiểm tra lại tài khoản hoặc mật khẩu.",
        },
      };
    } catch (error: any) {
      return {
        success: false,
        error: {
          name: "LoginError",
          message: error.response?.data?.message || "Không thể kết nối đến máy chủ ERPNext.",
        },
      };
    }
  },

  logout: async () => {
    try {
      await axios.post("/api/method/logout");
    } catch (e) {
      console.warn("Logout error:", e);
    }
    return {
      success: true,
      redirectTo: "/login",
    };
  },

  check: async () => {
    try {
      const response = await axios.get("/api/method/frappe.auth.get_logged_user");
      if (response.data?.message && response.data.message !== "Guest") {
        return { authenticated: true };
      }
      return { authenticated: false, redirectTo: "/login" };
    } catch {
      return { authenticated: false, redirectTo: "/login" };
    }
  },

  getIdentity: async () => {
    try {
      const userRes = await axios.get("/api/method/frappe.auth.get_logged_user");
      const username = userRes.data?.message;
      if (username && username !== "Guest") {
        return {
          id: username,
          name: username,
        };
      }
      return null;
    } catch {
      return null;
    }
  },

  onError: async (error: any) => {
    if (error?.response?.status === 401 || error?.response?.status === 403) {
      return { logout: true };
    }
    return { error };
  },
};
