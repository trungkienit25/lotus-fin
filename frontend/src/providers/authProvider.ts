import type { AuthProvider } from "@refinedev/core";
import axios from "axios";
import { bootstrapSession, clearSessionBootstrap, getActiveCsrfToken } from "./sessionBootstrap.ts";

// Đảm bảo mọi request đều gửi kèm cookie session của Frappe (sid)
axios.defaults.withCredentials = true;

// Tự động đính kèm X-Frappe-CSRF-Token cho mọi request nếu có token phiên
axios.interceptors.request.use(async (config) => {
  const url = config.url || "";
  if (!url.includes("/api/method/login") && !url.includes("/copilot/session")) {
    let token = getActiveCsrfToken();
    if (!token) {
      try {
        const session = await bootstrapSession();
        token = session.csrfToken;
      } catch {}
    }
    if (token && !config.headers["X-Frappe-CSRF-Token"]) {
      config.headers["X-Frappe-CSRF-Token"] = token;
    }
  }
  return config;
});


export const authProvider: AuthProvider = {
  login: async ({ email, password }) => {
    clearSessionBootstrap();
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
        clearSessionBootstrap();
        await bootstrapSession();
        return {
          success: true,
          redirectTo: "/copilot",
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
          message: "Không thể xác minh phiên đăng nhập Lotus Fin.",
        },
      };
    }
  },

  logout: async () => {
    clearSessionBootstrap();
    try {
      const session = await bootstrapSession();
      await axios.post("/api/method/logout", undefined, {
        headers: { "X-Frappe-CSRF-Token": session.csrfToken },
      });
    } catch {
      return { success: false, error: { name: "LogoutError",
        message: "Sign out could not be verified. Please retry." } };
    } finally {
      clearSessionBootstrap();
    }
    return {
      success: true,
      redirectTo: "/login",
    };
  },

  check: async () => {
    try {
      await bootstrapSession();
      return { authenticated: true };
    } catch {
      clearSessionBootstrap();
      return { authenticated: false, redirectTo: "/login" };
    }
  },

  getIdentity: async () => {
    try {
      const { user } = await bootstrapSession();
      return { id: user, name: user };
    } catch {
      return null;
    }
  },

  onError: async (error: any) => {
    if (error?.response?.status === 401 || error?.response?.status === 403) {
      clearSessionBootstrap();
      return { logout: true };
    }
    return { error };
  },
};
