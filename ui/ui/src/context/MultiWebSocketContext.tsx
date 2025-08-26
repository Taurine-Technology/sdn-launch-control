"use client";
import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from "react";
import { useAuth } from "@/context/authContext";
import { WebSocketMessage, WebSocketChannel } from "@/lib/types";

const WS_URLS = {
  openflow: process.env.NEXT_PUBLIC_WS_OPENFLOW,
  deviceStats: process.env.NEXT_PUBLIC_WS_DEVICESTATS,
  classifications: process.env.NEXT_PUBLIC_WS_CLASIFICATIONS,
};

type MessageHandler = (data: WebSocketMessage) => void;

interface WebSocketContextType {
  subscribe: (key: WebSocketChannel, handler: MessageHandler) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(
  undefined
);

export const MultiWebSocketProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const { token, logout } = useAuth();
  const connectionsRef = useRef<Record<string, WebSocket | null>>({});
  const subscribersRef = useRef<Record<string, Set<MessageHandler>>>({
    openflow: new Set(),
    deviceStats: new Set(),
    classifications: new Set(),
  });

  useEffect(() => {
    // Close all existing connections
    Object.values(connectionsRef.current).forEach((ws) => ws?.close(1000));
    connectionsRef.current = {};

    // Only connect if token is available
    if (!token) return;

    Object.entries(WS_URLS).forEach(([key, url]) => {
      if (!url) return;
      const fullUrl = `${url}?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(fullUrl);

      ws.onmessage = (event) => {
        let data;
        try {
          data = JSON.parse(event.data);
        } catch {
          data = event.data;
        }
        subscribersRef.current[key].forEach((handler) => handler(data));
      };

      ws.onclose = (event) => {
        if ([4001, 4003].includes(event.code)) {
          logout();
        }
      };

      connectionsRef.current[key] = ws;
    });

    return () => {
      Object.values(connectionsRef.current).forEach((ws) => ws?.close(1000));
      connectionsRef.current = {};
    };
  }, [token, logout]);

  const subscribe = useCallback(
    (key: WebSocketChannel, handler: MessageHandler) => {
      subscribersRef.current[key].add(handler);
      return () => {
        subscribersRef.current[key].delete(handler);
      };
    },
    []
  );

  const contextValue = useMemo(() => ({ subscribe }), [subscribe]);

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};

export function useMultiWebSocket() {
  const ctx = useContext(WebSocketContext);
  if (!ctx)
    throw new Error(
      "useMultiWebSocket must be used within MultiWebSocketProvider"
    );
  return ctx;
}
