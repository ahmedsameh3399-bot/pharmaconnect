import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { ask, getSessionMessages, listSessions } from "@/api/chatbot";
import type { ChatMessage } from "@/api/types";

// Chat UI for the grounded RAG assistant. Left pane lists previous sessions,
// right pane is the conversation. We deliberately show a disclaimer banner
// at the top and inline citation IDs on assistant replies, so the user (and
// the defense committee) sees exactly which DB rows grounded each answer.
export default function ChatbotPage() {
  const [sessionId, setSessionId] = useState<number | undefined>(undefined);
  const [draft, setDraft] = useState("");
  const qc = useQueryClient();
  const endRef = useRef<HTMLDivElement>(null);

  const sessions = useQuery({ queryKey: ["chat", "sessions"], queryFn: listSessions });
  const messages = useQuery({
    queryKey: ["chat", "messages", sessionId],
    queryFn: () => (sessionId ? getSessionMessages(sessionId) : Promise.resolve([] as ChatMessage[])),
    enabled: !!sessionId,
  });

  const sendMutation = useMutation({
    mutationFn: () => ask(draft.trim(), sessionId),
    onSuccess: (r) => {
      setDraft("");
      setSessionId(r.session_id);
      void qc.invalidateQueries({ queryKey: ["chat"] });
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Chatbot unavailable";
      toast.error(msg);
    },
  });

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.data, sendMutation.isPending]);

  const send = (e: React.FormEvent) => {
    e.preventDefault();
    if (!draft.trim()) return;
    sendMutation.mutate();
  };

  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">Medication assistant</h1>
      <p className="text-xs text-slate-500 bg-amber-50 border border-amber-200 rounded-md p-2">
        Informational only — based on our medication catalog. Not medical advice.
        For prescribing decisions consult a licensed professional.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-[200px_1fr] gap-4">
        <aside className="card max-h-64 md:max-h-[70vh] overflow-y-auto">
          <button
            className="btn-secondary w-full text-xs mb-2"
            onClick={() => setSessionId(undefined)}
          >
            + New chat
          </button>
          <ul className="space-y-1 text-sm">
            {sessions.data?.map((s) => (
              <li key={s.id}>
                <button
                  onClick={() => setSessionId(s.id)}
                  className={`w-full text-left px-2 py-1 rounded truncate ${
                    sessionId === s.id ? "bg-brand-50 text-brand-700" : "hover:bg-slate-50"
                  }`}
                >
                  {s.title}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <div className="card flex flex-col h-[70vh]">
          <div className="flex-1 overflow-y-auto space-y-3 pr-2">
            {(!messages.data || messages.data.length === 0) && (
              <p className="text-sm text-slate-500">
                Try: "What alternatives to Panadol have the same active ingredient?"
              </p>
            )}
            {messages.data?.map((m) => (
              <div
                key={m.id}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                    m.role === "user"
                      ? "bg-brand-600 text-white"
                      : "bg-slate-100 text-slate-800"
                  }`}
                >
                  {m.content}
                  {m.role === "assistant" && m.citations && (
                    <p className="mt-1 text-[10px] text-slate-500">
                      Grounded in medication IDs: {m.citations}
                    </p>
                  )}
                </div>
              </div>
            ))}
            {sendMutation.isPending && (
              <p className="text-xs text-slate-400 italic">Assistant is typing…</p>
            )}
            <div ref={endRef} />
          </div>
          <form onSubmit={send} className="mt-3 flex gap-2">
            <input
              className="input flex-1"
              placeholder="Ask about a medication…"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              disabled={sendMutation.isPending}
            />
            <button className="btn-primary" disabled={sendMutation.isPending || !draft.trim()}>
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
