import { api } from "./client";
import type { ChatMessage, ChatSession } from "./types";

export interface AskResponse {
  session_id: number;
  assistant_message: ChatMessage;
}

export async function ask(message: string, sessionId?: number): Promise<AskResponse> {
  const r = await api.post<AskResponse>("/chatbot/ask", { message, session_id: sessionId });
  return r.data;
}

export async function listSessions(): Promise<ChatSession[]> {
  return (await api.get<ChatSession[]>("/chatbot/sessions")).data;
}

export async function getSessionMessages(sessionId: number): Promise<ChatMessage[]> {
  return (await api.get<ChatMessage[]>(`/chatbot/sessions/${sessionId}/messages`)).data;
}
