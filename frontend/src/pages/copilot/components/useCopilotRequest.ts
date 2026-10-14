import { useState, useRef, useEffect, useCallback } from "react";
import axios, { AxiosRequestConfig } from "axios";
import { normalizeCopilotResponse, SafePresentationResult } from "./copilotPresentation";

export interface CopilotRequestOptions {
  company: string;
  contextKey?: string;
  hasQualifiedContext?: boolean; // Defaults to false under CURRENT_UNQUALIFIED
  transportFn?: (payload: unknown, config?: AxiosRequestConfig) => Promise<{ data: unknown; status?: number; headers?: Record<string, unknown> }>;
}

export interface UseCopilotRequestReturn {
  loading: boolean;
  activeGeneration: number;
  sendRequest: (query: string, attachedFileNames?: string[]) => Promise<SafePresentationResult>;
  resetRequest: () => void;
}

export function useCopilotRequest(options: CopilotRequestOptions): UseCopilotRequestReturn {
  const { company, contextKey, hasQualifiedContext = false, transportFn } = options;

  const [loading, setLoading] = useState(false);
  const generationRef = useRef(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  const resetRequest = useCallback(() => {
    generationRef.current += 1;
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
  }, []);

  // Reset when company or presentation contextKey changes
  useEffect(() => {
    resetRequest();
  }, [company, contextKey, resetRequest]);

  // Clean up on component unmount: invalidate generation and abort
  useEffect(() => {
    return () => {
      generationRef.current += 1; // Invalidate active generation so late completions are discarded
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, []);

  const sendRequest = useCallback(
    async (query: string, attachedFileNames: string[] = []): Promise<SafePresentationResult> => {
      // Step 1: Enforce current financial context restriction (FR5, F08)
      // Only permit remote call if synthetic transportFn is injected (for tests) with hasQualifiedContext
      if (!hasQualifiedContext || !transportFn) {
        return normalizeCopilotResponse(null); // Yields safe NOT_AVAILABLE without remote call
      }

      // Step 2: Manage lifecycle, generation, and abort controller (FR4, F04)
      generationRef.current += 1;
      const thisGeneration = generationRef.current;

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setLoading(true);

      try {
        const payload = {
          query: query + (attachedFileNames.length > 0 ? ` (Attached files: ${attachedFileNames.join(", ")})` : ""),
          company,
          as_of_date: "2026-09-26",
        };

        const config: AxiosRequestConfig = {
          signal: controller.signal,
          timeout: 15000,
        };

        const res = await transportFn(payload, config);
        const resData = res.data;
        const resStatus = res.status ?? 200;
        const correlationIdHeader = res.headers?.["x-correlation-id"];

        // Stale generation check
        if (generationRef.current !== thisGeneration) {
          return {
            status: "TIMEOUT",
            userFacingText: "",
            sourceLabel: "Stale",
            allowFinancialWidgets: false,
          };
        }

        return normalizeCopilotResponse(resData, resStatus, correlationIdHeader);
      } catch (err: unknown) {
        if (generationRef.current !== thisGeneration) {
          return {
            status: "TIMEOUT",
            userFacingText: "",
            sourceLabel: "Stale",
            allowFinancialWidgets: false,
          };
        }

        const isAbort = axios.isCancel(err) || (err instanceof Error && err.name === "CanceledError");
        if (isAbort) {
          return {
            status: "TIMEOUT",
            userFacingText: "",
            sourceLabel: "Cancelled",
            allowFinancialWidgets: false,
          };
        }

        // 1. Extract response details if available
        let errStatus = 500;
        let errData: unknown = null;
        let cidHeader: unknown;

        if (axios.isAxiosError(err) || (err && typeof err === "object" && "response" in err)) {
          const resp = (err as { response?: { status?: number; data?: unknown; headers?: Record<string, unknown> } }).response;
          if (resp) {
            errStatus = resp.status || 500;
            errData = resp.data;
            cidHeader = resp.headers?.["x-correlation-id"];

            // 2. Recognized denial (HTTP 401/403 or body FORBIDDEN) takes absolute precedence
            const pres = normalizeCopilotResponse(errData, errStatus, cidHeader);
            if (pres.status === "FORBIDDEN") {
              return pres;
            }
          }
        }

        // 3. Strict timeout classification (ETIMEDOUT or ECONNABORTED or TimeoutError)
        const errCode = (err && typeof err === "object" && "code" in err) ? (err as { code?: string }).code : undefined;
        const isTimeout =
          errCode === "ECONNABORTED" ||
          errCode === "ETIMEDOUT" ||
          (err instanceof Error && err.name === "TimeoutError");

        if (isTimeout) {
          return {
            status: "TIMEOUT",
            userFacingText: "Yêu cầu đã hết thời gian chờ.",
            sourceLabel: "Hết thời gian chờ",
            allowFinancialWidgets: false,
          };
        }

        // 4. Other transport failures -> approved mapping
        return normalizeCopilotResponse(errData, errStatus, cidHeader);
      } finally {
        if (generationRef.current === thisGeneration) {
          setLoading(false);
          abortControllerRef.current = null;
        }
      }
    },
    [company, hasQualifiedContext, transportFn]
  );

  return {
    loading,
    activeGeneration: generationRef.current,
    sendRequest,
    resetRequest,
  };
}
