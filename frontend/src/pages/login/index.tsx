import React, { useState } from "react";
import { useLogin } from "@refinedev/core";
import { useTranslation } from "../../i18n";
import Button from "../../components/ui/button/Button";

export const LoginPage: React.FC = () => {
  const { t } = useTranslation();
  const { mutate: login, isPending } = useLogin();
  const [email, setEmail] = useState("Administrator");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    login(
      { email, password },
      {
        onError: (error: any) => {
          setErrorMessage(error?.message || t("auth.loginFailed"));
        },
      }
    );
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F4F7FB] px-4 py-12">
      <div className="w-full max-w-md rounded-3xl border border-gray-200 bg-white p-8 shadow-theme-lg">
        {/* Brand Logo & Wordmark */}
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-3 flex size-14 items-center justify-center rounded-2xl bg-white border border-gray-100 p-2 shadow-theme-xs">
            <img
              src={`${import.meta.env.BASE_URL}brand/favicon.jpg`}
              alt="Lotus Fin"
              className="size-10 object-contain"
            />
          </div>
          <img
            src={`${import.meta.env.BASE_URL}brand/text.jpg`}
            alt="Lotus Fin — Intelligence In Bloom"
            className="h-10 object-contain"
          />
          <p className="mt-2 text-xs font-medium text-gray-500">
            {t("auth.enterCredentials")}
          </p>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-5 flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-xs text-rose-700">
            <svg className="size-4 shrink-0 text-rose-500 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div className="flex-1 font-medium">{errorMessage}</div>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-[#2E3A59]">
              {t("auth.email")} / Username
            </label>
            <div className="relative">
              <input
                type="text"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. Administrator"
                required
                className="h-11 w-full rounded-xl border border-gray-200 bg-gray-50/70 px-3.5 pl-10 text-xs text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none transition shadow-theme-xs"
              />
              <span className="pointer-events-none absolute left-3.5 top-3.5 text-gray-400">
                <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                </svg>
              </span>
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-[#2E3A59]">
              {t("auth.password")}
            </label>
            <div className="relative">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="h-11 w-full rounded-xl border border-gray-200 bg-gray-50/70 px-3.5 pl-10 text-xs text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none transition shadow-theme-xs"
              />
              <span className="pointer-events-none absolute left-3.5 top-3.5 text-gray-400">
                <svg className="size-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
              </span>
            </div>
          </div>

          <div className="pt-2">
            <Button
              type="submit"
              size="lg"
              variant="primary"
              disabled={isPending}
              className="w-full h-11 justify-center rounded-xl"
            >
              {isPending ? (
                <div className="flex items-center gap-2">
                  <svg className="size-4 animate-spin text-white" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>{t("auth.loggingIn")}...</span>
                </div>
              ) : (
                t("auth.login")
              )}
            </Button>
          </div>
        </form>

        <div className="mt-6 border-t border-gray-100 pt-4 text-center">
          <p className="text-[11px] font-medium text-gray-400">
            Lotus Fin Intelligent ERP Desk © 2026
          </p>
        </div>
      </div>
    </div>
  );
};
