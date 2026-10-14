import type { AuthProvider } from "@refinedev/core";
import axios from "axios";
import { bootstrapSession, clearSessionBootstrap } from "./sessionBootstrap.ts";

// Đảm bảo mọi request đều gửi kèm cookie session của Frappe (sid)
axios.defaults.withCredentials = true;

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
