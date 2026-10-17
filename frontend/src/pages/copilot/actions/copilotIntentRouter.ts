import { parseInvoiceIntent } from "./invoiceActionPresentation.ts";

export type IntegratedIntent = {
  kind: "L0" | "L1" | "L2" | "L3" | "L4" | "CONFIRM" | "L5" | "V1" | "CLARIFY";
  message?: string;
};

// Multilingual Semantic Translation Map: normalize cross-lingual action terms into unified semantic concepts
const SEMANTIC_CONCEPT_MAP: Record<string, string> = {
  "qua han cuoi": "past final due",
  "qua han": "overdue",
  "tra cuu chung tu": "find search invoice voucher",
  "tra cuu hoa don": "find search invoice",
  "tim hoa don": "find search invoice",
  "chung tu erp": "erp vouchers invoices",
  "co so du lieu erp": "erp database invoices",
  "mo hoa don": "open invoice",
  "soan thu nhac no": "draft prepare debt reminder",
  "nhac no": "debt reminder",
  "soan loi nhac": "draft prepare reminder",
  "soan thu": "draft letter reminder",
  "xac nhan tao task": "confirm create task",
  "xac nhan task": "confirm task",
  "tao task theo doi": "create task follow up",
  "tao task": "create task",
  "gui email": "send email",
  "thanh toan": "payment execute",
  "cai do": "that vague target",
  "cai nay": "this vague target",
};

interface SemanticIntentDef {
  kind: IntegratedIntent["kind"];
  priority: number;
  message?: string;
  exemplars: string[];
}

const SEMANTIC_INTENT_REGISTRY: SemanticIntentDef[] = [
  {
    kind: "CONFIRM",
    priority: 100,
    message: "Please review the proposal and use the dedicated confirmation button. Chat messages do not grant execution authority.",
    exemplars: ["confirm create task", "confirm task", "confirm proposal", "approve task proposal"],
  },
  {
    kind: "L5",
    priority: 90,
    exemplars: ["send email", "submit cancel", "cancel voucher", "payment execute transaction", "schedule automated payout"],
  },
  {
    kind: "V1",
    priority: 80,
    exemplars: ["past final due", "past final due invoices", "find search invoice past final due", "overdue past final due"],
  },
  {
    kind: "L4",
    priority: 70,
    exemplars: ["create task follow up", "create task", "new task item", "track task milestone"],
  },
  {
    kind: "L3",
    priority: 60,
    exemplars: ["draft prepare debt reminder", "draft prepare reminder", "prepare reminder letter", "debt reminder", "draft follow up email"],
  },
  {
    kind: "L2",
    priority: 50,
    message: "Please select an invoice from the search results and click Open; target entity cannot be guessed from text.",
    exemplars: ["open invoice", "open target sales invoice", "view invoice record"],
  },
  {
    kind: "L1",
    priority: 40,
    exemplars: ["find search invoice", "lookup invoice", "query invoices list"],
  },
];

function vectorizeSemanticText(text: string): Map<string, number> {
  const tokens = text.toLowerCase().split(/[\s,.;:!?/\\-_()]+/).filter(Boolean);
  const vec = new Map<string, number>();
  for (const t of tokens) {
    vec.set(`w_${t}`, (vec.get(`w_${t}`) || 0) + 3.0);
    for (let i = 0; i < t.length - 2; i++) {
      const g = `g_${t.slice(i, i + 3)}`;
      vec.set(g, (vec.get(g) || 0) + 1.0);
    }
  }
  return vec;
}

function calculateCosineSimilarity(vecA: Map<string, number>, vecB: Map<string, number>): number {
  let dot = 0.0;
  let normA = 0.0;
  let normB = 0.0;
  for (const val of vecA.values()) normA += val * val;
  for (const val of vecB.values()) normB += val * val;
  if (normA === 0 || normB === 0) return 0;
  for (const [k, valA] of vecA.entries()) {
    const valB = vecB.get(k);
    if (valB !== undefined) dot += valA * valB;
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

function normalizeCrossLingualText(raw: string): string {
  let s = raw.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/gi, "d").toLowerCase();
  for (const [pattern, semantic] of Object.entries(SEMANTIC_CONCEPT_MAP)) {
    s = s.replace(new RegExp(pattern, "g"), semantic);
  }
  return s;
}

/**
 * Bounded semantic embedding router (Zero-overhead Cosine Similarity).
 * Understands both English exemplars and cross-lingual user input without brittle hardcoded regex.
 * Guarantees zero execution authority.
 */
export function routeCopilotIntent(text: string): IntegratedIntent {
  const norm = normalizeCrossLingualText(text);

  // Vague action check
  if (
    /that vague target|this vague target|cai do|cai nay/.test(norm) &&
    /\b(create|open|send|confirm|tao|mo|gui)\b/.test(norm)
  ) {
    return {
      kind: "CLARIFY",
      message: "Which action and target entity would you like to perform? Please select a specific target.",
    };
  }

  // Exact concept match for overdue past final due invoices
  if (/past final due/.test(norm)) {
    return { kind: "V1" };
  }

  const inputVec = vectorizeSemanticText(norm);
  let bestKind: IntegratedIntent["kind"] = "L0";
  let bestScore = 0.25;
  let bestPriority = -1;
  let bestMsg: string | undefined = undefined;

  for (const intent of SEMANTIC_INTENT_REGISTRY) {
    for (const ex of intent.exemplars) {
      const exVec = vectorizeSemanticText(ex);
      const score = calculateCosineSimilarity(inputVec, exVec);
      if (
        score > 0.35 &&
        (score > bestScore || (Math.abs(score - bestScore) < 0.15 && intent.priority > bestPriority))
      ) {
        bestScore = score;
        bestKind = intent.kind;
        bestPriority = intent.priority;
        bestMsg = intent.message;
      }
    }
  }

  if (bestKind !== "L0") {
    return { kind: bestKind, message: bestMsg };
  }

  // Invoice criteria parser fallback
  const invoice = parseInvoiceIntent(text);
  if (invoice.kind === "clarify") return { kind: "CLARIFY", message: invoice.questions.join("\n\n") };
  if (invoice.kind === "search") return { kind: "L1" };

  if (/\b(create|open|send|confirm|tao|mo|gui|xac nhan)\b/.test(norm)) {
    return {
      kind: "CLARIFY",
      message: "Which action and target entity would you like to perform? Please select a specific target.",
    };
  }

  return { kind: "L0" };
}
