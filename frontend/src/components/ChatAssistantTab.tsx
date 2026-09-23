// frontend/src/components/ChatAssistantTab.tsx
// Grounded IBM Granite Guardian Conversational Assistant interface

import React, { useState } from "react";
import { Bot, Send, Sparkles, User, FileText, RotateCcw, AlertCircle } from "lucide-react";
import { api } from "../lib/api";
import clsx from "clsx";

interface Message {
  id: string;
  sender: "user" | "granite";
  text: string;
  sources?: string[];
  timestamp: string;
}

const SUGGESTIONS = [
  "Why was the last batch flagged for tool wear?",
  "What are the safe operating thresholds for torque and rotational speed?",
  "Explain how heat dissipation failure occurs in CNC machines.",
  "What corrective actions are recommended for high tool wear?",
];

export function ChatAssistantTab() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial",
      sender: "granite",
      text: "Hello! I am your IndustrialGuard AI assistant powered by IBM Granite Guardian and grounded in our 3-tier CNC technical knowledge base. How can I assist you with process quality monitoring or defect investigation today?",
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg: Message = {
      id: `u_${Date.now()}`,
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput("");
    setLoading(true);

    try {
      const res = await api.chat(query);
      const botMsg: Message = {
        id: `g_${Date.now()}`,
        sender: "granite",
        text: res.response,
        sources: res.rag_sources,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e: unknown) {
      const errMsg: Message = {
        id: `err_${Date.now()}`,
        sender: "granite",
        text: `Error connecting to assistant: ${e instanceof Error ? e.message : String(e)}`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: "initial",
        sender: "granite",
        text: "Conversation cleared. Ready for your next query.",
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Bot className="w-5 h-5 text-indigo-400" />
            IBM Granite Grounded Assistant
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Natural-language synthesis strictly grounded in empirical shop telemetry and technical knowledge base
          </p>
        </div>

        <button
          onClick={clearChat}
          className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 font-mono px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60"
        >
          <RotateCcw className="w-3.5 h-3.5" /> Clear History
        </button>
      </div>

      {/* Suggested Prompts */}
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s, i) => (
          <button
            key={i}
            onClick={() => sendMessage(s)}
            disabled={loading}
            className="rounded-lg border border-slate-800 bg-slate-900/40 px-3 py-1.5 text-xs text-slate-400 hover:border-slate-700 hover:text-slate-200 hover:bg-slate-800/40 transition-all text-left font-sans flex items-center gap-1.5"
          >
            <Sparkles className="w-3 h-3 text-blue-400 shrink-0" />
            <span>{s}</span>
          </button>
        ))}
      </div>

      {/* Chat Thread Container */}
      <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 backdrop-blur-md flex flex-col h-[520px]">
        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.map((m) => {
            const isUser = m.sender === "user";
            return (
              <div
                key={m.id}
                className={clsx(
                  "flex gap-3 max-w-3xl",
                  isUser ? "ml-auto flex-row-reverse" : "mr-auto"
                )}
              >
                <div
                  className={clsx(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-xs font-semibold",
                    isUser
                      ? "bg-blue-600 text-white"
                      : "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
                  )}
                >
                  {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div
                  className={clsx(
                    "rounded-2xl p-4 text-xs leading-relaxed space-y-2",
                    isUser
                      ? "bg-blue-600 text-white rounded-tr-none"
                      : "bg-slate-950/70 border border-slate-800 text-slate-200 rounded-tl-none"
                  )}
                >
                  <p className="whitespace-pre-wrap">{m.text}</p>

                  {m.sources && m.sources.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/80 text-[11px] font-mono text-blue-400 space-y-1">
                      <span className="font-semibold block text-slate-400">Grounding Provenance:</span>
                      {m.sources.map((src, i) => (
                        <div key={i} className="flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          <span>{src}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div
                    className={clsx(
                      "text-[10px] font-mono text-right",
                      isUser ? "text-blue-200" : "text-slate-500"
                    )}
                  >
                    {m.timestamp}
                  </div>
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex gap-3 max-w-xl mr-auto">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
                <Bot className="w-4 h-4" />
              </div>
              <div className="rounded-2xl rounded-tl-none bg-slate-950/70 border border-slate-800 p-4 text-xs text-slate-400 flex items-center gap-2">
                <div className="w-3.5 h-3.5 rounded-full border-2 border-indigo-400/30 border-t-indigo-400 animate-spin" />
                <span>Synthesizing grounded response with IBM Granite...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="border-t border-slate-800/80 p-3 bg-slate-950/40 rounded-b-2xl">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              placeholder="Ask Granite about machine diagnostics, root causes, or quality metrics..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-blue-500/60"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="flex items-center justify-center h-10 w-10 rounded-xl bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-40 transition-all cursor-pointer shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <p className="text-[10px] text-slate-500 font-mono text-center mt-2">
            IBM Granite Guardian 8B · Grounded in RAG Knowledge Base · Decision-Support Only
          </p>
        </div>
      </div>
    </div>
  );
}
