// SSE subscription hook. Connects to /notifications/stream, parses each event
// as JSON, fires a toast, and invalidates relevant React Query caches so the
// UI reflects the new state without a manual refresh.
import { useEffect } from "react";
import toast from "react-hot-toast";
import { useQueryClient } from "@tanstack/react-query";
import { API_BASE_URL, tokenStore } from "@/api/client";

interface NotificationMessage {
  type: string;
  payload: Record<string, unknown>;
}

export function useNotifications(enabled: boolean) {
  const qc = useQueryClient();

  useEffect(() => {
    if (!enabled) return;
    const token = tokenStore.access;
    if (!token) return;

    // EventSource can't set headers, so we pass the token as a query param.
    const url = `${API_BASE_URL}/notifications/stream?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);

    es.addEventListener("notification", (ev) => {
      try {
        const data = JSON.parse((ev as MessageEvent).data) as NotificationMessage;
        if (data.type === "order.created") {
          toast.success("New order received");
          void qc.invalidateQueries({ queryKey: ["orders", "mine"] });
        } else if (data.type === "order.status_changed") {
          toast(`Order #${data.payload.order_id} → ${data.payload.new_status}`);
          void qc.invalidateQueries({ queryKey: ["orders"] });
        }
      } catch {
        // Ignore malformed events; the stream itself keeps running.
      }
    });

    es.onerror = () => {
      // Browser will auto-reconnect; we close on logout via the effect cleanup.
    };

    return () => es.close();
  }, [enabled, qc]);
}
