export interface AttachedFile {
  name: string;
  size: number;
  type: string;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  content: string;
  timestamp: string;
  attachments?: AttachedFile[];
  sourceLabel?: string;
  correlationId?: string;
}

export type ChatPanelMode = "chat" | "invoices" | "followup";

export interface StarterCard {
  title: string;
  description: string;
  query: string;
  inspectorTab: string;
  tag: string;
}
