import { prepareFollowupPreview, normalizeAndValidateUserEdit, type PreviewProvenance, type PrepareRequest } from "./followupPreview.ts";

export type PreviewLifecycle = "EMPTY" | "EDITABLE" | "REVIEWED" | "EXPIRED";
export type ActionNotice = "COPIED" | "COPY_FAILED" | null;
export interface Clock { now(): number; }
export interface ClipboardPort { writeText(text: string): Promise<void>; }
export interface ControllerOptions { clock?: Clock; clipboard?: ClipboardPort; scopeEpoch: string; }
export interface ControllerState {
  lifecycle: PreviewLifecycle; body: string; provenance: PreviewProvenance;
  isReviewed: boolean; isCopying: boolean; lastActionStatus: ActionNotice;
  errorMessage: string | null; generation: number;
}
export const ABSOLUTE_TTL_MS = 600000;

function createDefaultMonotonicClock(): Clock {
  const perf = globalThis.performance;
  if (perf && typeof perf.now === "function") {
    const origin = (typeof perf.timeOrigin === "number") ? perf.timeOrigin : Date.now();
    return { now: () => origin + perf.now() };
  }
  return { now: () => Date.now() };
}

export class FollowupPreviewController {
  private clock: Clock; private clipboard: ClipboardPort; private scopeEpoch: string;
  private createdAt: number | null = null; private generation = 0; private bodyRevision = 0;
  private copyOperationId = 0; private activeCopyLockId: number | null = null;
  private listeners = new Set<(s: ControllerState) => void>(); private disposed = false;
  private state: ControllerState = {
    lifecycle: "EMPTY", body: "", provenance: "SUGGESTED", isReviewed: false,
    isCopying: false, lastActionStatus: null, errorMessage: null, generation: 0,
  };

  constructor(opts: ControllerOptions) {
    this.clock = opts.clock ?? createDefaultMonotonicClock();
    this.clipboard = opts.clipboard ?? {
      writeText: async (t) => {
        if (typeof navigator !== "undefined" && navigator.clipboard) await navigator.clipboard.writeText(t);
        else throw new Error("Clipboard API unavailable");
      },
    };
    this.scopeEpoch = opts.scopeEpoch ?? "";
  }

  private isScopeAvailable(): boolean { return typeof this.scopeEpoch === "string" && this.scopeEpoch.trim().length > 0; }

  public checkExpiry(): boolean {
    if (this.disposed || this.state.lifecycle === "EMPTY" || this.state.lifecycle === "EXPIRED") return true;
    if (this.createdAt !== null && this.clock.now() - this.createdAt >= ABSOLUTE_TTL_MS) {
      this.state = {
        ...this.state, lifecycle: "EXPIRED", body: "", isReviewed: false, isCopying: false,
        errorMessage: "Bản xem trước đã hết hạn (10 phút).",
      };
      this.activeCopyLockId = null;
      this.notify();
      return true;
    }
    return false;
  }

  private notify(): void {
    if (this.disposed) return;
    const s = { ...this.state };
    this.listeners.forEach((fn) => { try { fn(s); } catch {} });
  }

  public subscribe(fn: (s: ControllerState) => void): () => void {
    if (this.disposed) { fn({ ...this.state }); return () => {}; }
    this.listeners.add(fn); fn({ ...this.state });
    return () => this.listeners.delete(fn);
  }

  public getState(): ControllerState { this.checkExpiry(); return { ...this.state }; }

  public setScopeEpoch(epoch: string): void {
    if (this.disposed) return;
    const normalized = epoch ?? "";
    if (this.scopeEpoch !== normalized) { this.scopeEpoch = normalized; this.discard(); }
  }

  public prepare(req: PrepareRequest): void {
    if (this.disposed) return;
    this.generation++; this.bodyRevision++; this.activeCopyLockId = null;
    if (!this.isScopeAvailable()) {
      this.state = {
        lifecycle: "EMPTY", body: "", provenance: "SUGGESTED", isReviewed: false,
        isCopying: false, lastActionStatus: null, errorMessage: "Phạm vi phiên làm việc không khả dụng.",
        generation: this.generation,
      };
      this.createdAt = null; this.notify(); return;
    }
    const res = prepareFollowupPreview(req);
    if (res.status !== "PREVIEW_READY" || !res.preview) {
      this.state = {
        lifecycle: "EMPTY", body: "", provenance: "SUGGESTED", isReviewed: false,
        isCopying: false, lastActionStatus: null, errorMessage: res.user_message, generation: this.generation,
      };
      this.createdAt = null;
    } else {
      this.createdAt = this.clock.now();
      this.state = {
        lifecycle: "EDITABLE", body: res.preview.body, provenance: "SUGGESTED", isReviewed: false,
        isCopying: false, lastActionStatus: null, errorMessage: null, generation: this.generation,
      };
    }
    this.notify();
  }

  public updateBody(text: string): boolean {
    if (this.disposed || !this.isScopeAvailable() || this.checkExpiry() || this.state.lifecycle === "EMPTY") return false;
    const v = normalizeAndValidateUserEdit(text);
    if (!v.valid) {
      let err = "Nội dung không hợp lệ.";
      if (v.errorCode === "EMPTY_TEXT") err = "Nội dung không được để trống.";
      else if (v.errorCode === "EXCEEDS_MAX_SCALARS") err = "Nội dung vượt quá 2000 ký tự Unicode.";
      else if (v.errorCode === "EXCEEDS_MAX_BYTES") err = "Nội dung vượt quá giới hạn dung lượng (8192 bytes).";
      else if (v.errorCode === "FORBIDDEN_CONTROL_CHAR" || v.errorCode === "FORBIDDEN_BIDI_CONTROL") {
        err = "Nội dung chứa ký tự điều khiển không được phép.";
      }
      this.state = { ...this.state, errorMessage: err, isReviewed: false, lifecycle: "EDITABLE" };
      this.notify(); return false;
    }
    this.bodyRevision++;
    this.state = {
      ...this.state, body: v.normalizedText, provenance: "USER_ENTERED",
      isReviewed: false, lifecycle: "EDITABLE", errorMessage: null, lastActionStatus: null,
    };
    this.notify(); return true;
  }

  public setReviewed(reviewed: boolean): void {
    if (this.disposed || !this.isScopeAvailable() || this.checkExpiry() || this.state.lifecycle === "EMPTY") return;
    if (reviewed) {
      if (this.state.body.trim().length === 0) this.state = { ...this.state, errorMessage: "Chưa có nội dung để xác nhận." };
      else this.state = { ...this.state, isReviewed: true, lifecycle: "REVIEWED", errorMessage: null };
    } else {
      this.state = { ...this.state, isReviewed: false, lifecycle: "EDITABLE" };
    }
    this.notify();
  }

  public resetTemplate(): void {
    if (this.disposed) return;
    this.prepare({
      contract_version: "l3.followup.local.v0.1", capability: "followup.prepare_text",
      template_id: "followup.neutral.vi.v1", locale: "vi-VN",
    });
  }

  public async copy(): Promise<boolean> {
    if (
      this.disposed || !this.isScopeAvailable() || this.checkExpiry() ||
      !this.state.isReviewed || this.state.lifecycle !== "REVIEWED" || this.activeCopyLockId !== null
    ) return false;

    const opId = ++this.copyOperationId, opGen = this.generation, opRev = this.bodyRevision, opText = this.state.body;
    this.activeCopyLockId = opId;
    this.state = { ...this.state, isCopying: true, lastActionStatus: null };
    this.notify();

    try {
      await this.clipboard.writeText(opText);
      if (
        this.disposed || !this.isScopeAvailable() || this.checkExpiry() ||
        this.state.lifecycle === "EMPTY" || this.generation !== opGen ||
        this.bodyRevision !== opRev || this.activeCopyLockId !== opId
      ) return false;

      this.state = { ...this.state, isCopying: false, lastActionStatus: "COPIED" };
      this.notify(); return true;
    } catch {
      if (
        this.disposed || !this.isScopeAvailable() || this.checkExpiry() ||
        this.state.lifecycle === "EMPTY" || this.generation !== opGen ||
        this.bodyRevision !== opRev || this.activeCopyLockId !== opId
      ) return false;

      this.state = {
        ...this.state, isCopying: false, lastActionStatus: "COPY_FAILED",
        errorMessage: "Không thể sao chép vào bộ nhớ tạm.",
      };
      this.notify(); return false;
    } finally {
      if (this.activeCopyLockId === opId) {
        this.activeCopyLockId = null;
        if (!this.disposed && this.state.isCopying) { this.state = { ...this.state, isCopying: false }; this.notify(); }
      }
    }
  }

  public discard(): void {
    this.generation++; this.bodyRevision++; this.createdAt = null; this.activeCopyLockId = null;
    this.state = {
      lifecycle: "EMPTY", body: "", provenance: "SUGGESTED", isReviewed: false,
      isCopying: false, lastActionStatus: null, errorMessage: null, generation: this.generation,
    };
    this.notify();
  }

  public dispose(): void {
    if (this.disposed) return;
    this.disposed = true; this.discard(); this.listeners.clear();
  }
}
