"use client";

import { useEffect, useMemo, useState } from "react";

type ConversationSummary = {
  id: string;
  current_state: string;
  asker_id: string;
  current_responder_id: string | null;
  escalation_level: number;
  question_type: string;
  created_at: string | null;
  timeout_at: string | null;
};

type ConversationEvent = {
  id: string;
  event_type: string;
  created_at: string;
  payload: Record<string, unknown>;
};

type ConversationTimeline = {
  conversation: {
    id: string;
    current_state: string;
    question_type: string;
    escalation_level: number;
    created_at: string | null;
    resolved_at: string | null;
    timeout_at: string | null;
  };
  events: ConversationEvent[];
};

type FetchState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

const defaultApiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function SquadDashboardPage() {
  const [apiUrl, setApiUrl] = useState(defaultApiUrl);
  const [token, setToken] = useState("");
  const [squadId, setSquadId] = useState("");
  const [conversations, setConversations] = useState<FetchState<ConversationSummary[]>>({
    data: null,
    loading: false,
    error: null,
  });
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<FetchState<ConversationTimeline>>({
    data: null,
    loading: false,
    error: null,
  });

  const isAuthenticated = token.trim().length > 0;
  const hasSquadId = squadId.trim().length > 0;

  const sortedConversations = useMemo(() => {
    if (!conversations.data) return [] as ConversationSummary[];
    return [...conversations.data].sort((a, b) => {
      const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
      const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
      return timeB - timeA;
    });
  }, [conversations.data]);

  useEffect(() => {
    if (!selectedConversation || !isAuthenticated || !hasSquadId) {
      setTimeline({ data: null, loading: false, error: null });
      return;
    }

    const fetchTimeline = async () => {
      setTimeline({ data: null, loading: true, error: null });

      try {
        const response = await fetch(
          `${apiUrl}/api/v1/conversations/${selectedConversation}/timeline`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            cache: "no-store",
          }
        );

        if (!response.ok) {
          const message = await response.text();
          throw new Error(message || `Failed to load timeline (${response.status})`);
        }

        const data = (await response.json()) as ConversationTimeline;
        setTimeline({ data, loading: false, error: null });
      } catch (error) {
        setTimeline({
          data: null,
          loading: false,
          error: error instanceof Error ? error.message : "Unknown error",
        });
      }
    };

    void fetchTimeline();
  }, [apiUrl, selectedConversation, token, isAuthenticated, hasSquadId]);

  const handleLoadConversations = async () => {
    if (!isAuthenticated || !hasSquadId) {
      setConversations((prev) => ({
        ...prev,
        error: "API token and squad ID are required",
      }));
      return;
    }

    setConversations({ data: null, loading: true, error: null });

    try {
      const response = await fetch(
        `${apiUrl}/api/v1/conversations/squads/${squadId}/conversations`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          cache: "no-store",
        }
      );

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Failed to load conversations (${response.status})`);
      }

      const data = (await response.json()) as ConversationSummary[];
      setConversations({ data, loading: false, error: null });

      if (data.length > 0) {
        setSelectedConversation(data[0].id);
      } else {
        setSelectedConversation(null);
        setTimeline({ data: null, loading: false, error: null });
      }
    } catch (error) {
      setConversations({
        data: null,
        loading: false,
        error: error instanceof Error ? error.message : "Unknown error",
      });
    }
  };

  const formatDate = (value: string | null) => {
    if (!value) return "—";
    const date = new Date(value);
    return date.toLocaleString();
  };

  const renderConversationCard = (conversation: ConversationSummary) => {
    const isSelected = conversation.id === selectedConversation;
    return (
      <button
        key={conversation.id}
        onClick={() => setSelectedConversation(conversation.id)}
        className={`rounded-lg border p-4 text-left transition-colors ${
          isSelected
            ? "border-blue-500 bg-blue-50 dark:bg-slate-800"
            : "border-gray-200 hover:border-blue-400"
        }`}
      >
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
            {conversation.question_type.toUpperCase()}
          </h3>
          <span
            className={`rounded-full px-2 py-1 text-xs font-medium ${stateBadgeClass(
              conversation.current_state
            )}`}
          >
            {conversation.current_state}
          </span>
        </div>
        <dl className="mt-3 space-y-2 text-xs text-gray-600 dark:text-gray-300">
          <div className="flex justify-between">
            <dt>Created</dt>
            <dd>{formatDate(conversation.created_at)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Escalation</dt>
            <dd>Level {conversation.escalation_level}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Responder</dt>
            <dd>{conversation.current_responder_id ?? "—"}</dd>
          </div>
        </dl>
      </button>
    );
  };

  const renderTimeline = () => {
    if (timeline.loading) {
      return <p className="text-sm text-gray-500">Loading timeline…</p>;
    }

    if (timeline.error) {
      return (
        <p className="text-sm text-red-600 dark:text-red-400">Timeline error: {timeline.error}</p>
      );
    }

    if (!timeline.data) {
      return <p className="text-sm text-gray-500">Select a conversation to view its timeline.</p>;
    }

    return (
      <div className="space-y-6">
        <section className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Conversation Details</h2>
          <dl className="mt-3 grid grid-cols-1 gap-3 text-sm text-gray-600 dark:text-gray-300 md:grid-cols-2">
            <div>
              <dt className="font-medium text-gray-500 dark:text-gray-400">State</dt>
              <dd>{timeline.data.conversation.current_state}</dd>
            </div>
            <div>
              <dt className="font-medium text-gray-500 dark:text-gray-400">Question Type</dt>
              <dd>{timeline.data.conversation.question_type}</dd>
            </div>
            <div>
              <dt className="font-medium text-gray-500 dark:text-gray-400">Escalation Level</dt>
              <dd>{timeline.data.conversation.escalation_level}</dd>
            </div>
            <div>
              <dt className="font-medium text-gray-500 dark:text-gray-400">Created</dt>
              <dd>{formatDate(timeline.data.conversation.created_at)}</dd>
            </div>
            <div>
              <dt className="font-medium text-gray-500 dark:text-gray-400">Resolved</dt>
              <dd>{formatDate(timeline.data.conversation.resolved_at)}</dd>
            </div>
            <div>
              <dt className="font-medium text-gray-500 dark:text-gray-400">Timeout At</dt>
              <dd>{formatDate(timeline.data.conversation.timeout_at)}</dd>
            </div>
          </dl>
        </section>

        <section className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Timeline</h2>
          <ol className="mt-4 space-y-4">
            {timeline.data.events.length === 0 && (
              <li className="text-sm text-gray-500">No events recorded yet.</li>
            )}
            {timeline.data.events.map((event) => (
              <li key={event.id} className="border-l-2 border-blue-200 pl-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-blue-600 dark:text-blue-300">
                    {event.event_type}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(event.created_at).toLocaleString()}
                  </span>
                </div>
                <pre className="mt-2 rounded bg-slate-900/80 p-3 text-xs text-slate-100 shadow-inner">
                  {JSON.stringify(event.payload, null, 2)}
                </pre>
              </li>
            ))}
          </ol>
        </section>
      </div>
    );
  };

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 text-gray-900 dark:bg-slate-950 dark:text-slate-50">
      <header className="border-b border-gray-200 bg-white/90 backdrop-blur shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Squad Collaboration Dashboard</h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
              Monitor live agent conversations, escalation levels, and timelines.
            </p>
          </div>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-blue-500 hover:text-blue-600 dark:border-slate-700 dark:text-gray-200"
          >
            ← Back to landing
          </a>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-8">
        <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Connection Settings</h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
            Provide the backend API URL, your API token, and the squad ID you want to monitor. These
            values are stored only in memory for this session.
          </p>

          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                API URL
              </label>
              <input
                value={apiUrl}
                onChange={(event) => setApiUrl(event.target.value)}
                placeholder="http://localhost:8000"
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-slate-700 dark:bg-slate-950"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                API Token
              </label>
              <input
                value={token}
                onChange={(event) => setToken(event.target.value)}
                placeholder="Paste bearer token"
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-slate-700 dark:bg-slate-950"
                type="password"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Squad ID
              </label>
              <input
                value={squadId}
                onChange={(event) => setSquadId(event.target.value)}
                placeholder="UUID of the squad"
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 dark:border-slate-700 dark:bg-slate-950"
              />
            </div>
          </div>

          <div className="mt-4 flex items-center gap-3">
            <button
              type="button"
              onClick={() => void handleLoadConversations()}
              className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
              disabled={conversations.loading}
            >
              {conversations.loading ? "Loading…" : "Load Conversations"}
            </button>
            {conversations.error && (
              <span className="text-sm text-red-600 dark:text-red-400">
                {conversations.error}
              </span>
            )}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-[320px,1fr]">
          <div className="flex h-full flex-col gap-4">
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
                Active Conversations
              </h2>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {conversations.data ? conversations.data.length : 0} total
              </p>
            </div>

            <div className="flex-1 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="max-h-[480px] space-y-3 overflow-y-auto p-4">
                {conversations.loading && (
                  <p className="text-sm text-gray-500">Fetching conversations…</p>
                )}

                {!conversations.loading && conversations.data?.length === 0 && (
                  <p className="text-sm text-gray-500">
                    No conversations found. Trigger a question in the squad to see live activity.
                  </p>
                )}

                {sortedConversations.map(renderConversationCard)}
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">Conversation Timeline</h2>
            <div className="mt-4 min-h-[320px]">
              {renderTimeline()}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function stateBadgeClass(state: string): string {
  switch (state.toLowerCase()) {
    case "pending":
      return "bg-yellow-100 text-yellow-800";
    case "waiting":
      return "bg-blue-100 text-blue-800";
    case "answered":
      return "bg-green-100 text-green-800";
    case "escalated":
      return "bg-purple-100 text-purple-800";
    case "cancelled":
      return "bg-gray-200 text-gray-700";
    case "timeout":
      return "bg-red-100 text-red-700";
    default:
      return "bg-gray-100 text-gray-700";
  }
}

