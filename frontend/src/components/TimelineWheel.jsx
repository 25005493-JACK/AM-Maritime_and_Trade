import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  AlertTriangle, CheckCircle2, Clock, FileText, Send,
  GitCompare, Cpu, Eye, ChevronDown, ChevronUp,
  Paperclip, AlertCircle, RefreshCw, X, ArrowRight,
  ShieldCheck, Layers, ChevronLeft, ChevronRight, Search,
  ExternalLink, Copy, Check
} from 'lucide-react';

/* ─────────────────────────────────────────────
   STAGE DEFINITIONS & COLOR TOKENS
   BL Draft = blue (#38bdf8)
   AI Draft = purple (#a78bfa)
   Comparison = orange (#fb923c)
   Sent = green (#34d399)
───────────────────────────────────────────── */
const STAGE_CONFIG = {
  all:     { label: 'All',          color: '#94a3b8', dot: '#64748b', bg: 'rgba(148,163,184,0.12)', border: 'rgba(148,163,184,0.3)' },
  si:      { label: 'SI Ingestion', color: '#818cf8', dot: '#6366f1', bg: 'rgba(129,140,248,0.12)', border: 'rgba(129,140,248,0.35)' },
  bl:      { label: 'BL Draft',     color: '#38bdf8', dot: '#0ea5e9', bg: 'rgba(56,189,248,0.12)',  border: 'rgba(56,189,248,0.35)' },
  draft:   { label: 'AI Draft',     color: '#a78bfa', dot: '#8b5cf6', bg: 'rgba(167,139,250,0.12)', border: 'rgba(167,139,250,0.35)' },
  compare: { label: 'Comparison',   color: '#fb923c', dot: '#f97316', bg: 'rgba(251,146,60,0.12)',  border: 'rgba(251,146,60,0.35)' },
  review:  { label: 'Human Review', color: '#fbbf24', dot: '#f59e0b', bg: 'rgba(251,191,36,0.12)',  border: 'rgba(251,191,36,0.35)' },
  sent:    { label: 'Sent',         color: '#34d399', dot: '#10b981', bg: 'rgba(52,211,153,0.12)',  border: 'rgba(52,211,153,0.35)' },
};

const LIGHT_STAGE_COLORS = {
  all: '#475569', si: '#4338ca', bl: '#0369a1', draft: '#6d28d9',
  compare: '#9a3412', review: '#92400e', sent: '#047857'
};

function getStage(key, theme) {
  const stage = STAGE_CONFIG[key] || STAGE_CONFIG.bl;
  return theme === 'light'
    ? { ...stage, color: LIGHT_STAGE_COLORS[key] || LIGHT_STAGE_COLORS.bl }
    : stage;
}

function formatTime(ts) {
  if (!ts) return '—';
  try {
    return new Intl.DateTimeFormat('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    }).format(new Date(ts));
  } catch {
    return ts;
  }
}

/* ─────────────────────────────────────────────
   INLINE DOCUMENT PREVIEW COMPONENT
───────────────────────────────────────────── */
function DocumentPreview({ doc }) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let isMounted = true;
    if (!doc?.file_url) return;

    setLoading(true);
    setError(null);
    fetch(doc.file_url)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.text();
      })
      .then(text => {
        if (isMounted) setContent(text);
      })
      .catch(err => {
        if (isMounted) setError(err.message);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => { isMounted = false; };
  }, [doc]);

  const handleCopy = () => {
    if (content) {
      navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
        <RefreshCw className="w-3.5 h-3.5 animate-spin text-sky-400" />
        <span>Loading document preview…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-3 bg-red-950/30 rounded-lg border border-red-800/40 text-xs text-red-400">
        Failed to preview document: {error}
      </div>
    );
  }

  return (
    <div className="mt-2 bg-slate-950 rounded-lg border border-slate-800/90 overflow-hidden shadow-inner">
      <div className="px-3 py-1.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <span>{doc.name}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 hover:text-slate-200 transition text-slate-400"
          title="Copy text"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <pre className="p-3 text-[11px] font-mono text-slate-300 leading-relaxed max-h-60 overflow-y-auto whitespace-pre-wrap selection:bg-sky-500/30">
        {content || 'Document content is empty or binary.'}
      </pre>
    </div>
  );
}

/* ─────────────────────────────────────────────
   MAIN COMPONENT: TimelineWheel
───────────────────────────────────────────── */
export default function TimelineWheel({ theme }) {
  const [shipments, setShipments] = useState([]);
  const [loadingShipments, setLoadingShipments] = useState(true);
  const [shipmentError, setShipmentError] = useState(null);

  const [activeClient, setActiveClient] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedShipmentId, setSelectedShipmentId] = useState(null);

  const [timelineData, setTimelineData] = useState(null);
  const [loadingTimeline, setLoadingTimeline] = useState(false);
  const [timelineError, setTimelineError] = useState(null);

  const [expandedDoc, setExpandedDoc] = useState(null);
  const railScrollRef = useRef(null);

  /* ── 1. Fetch all shipments ── */
  const fetchShipments = useCallback(async () => {
    setLoadingShipments(true);
    setShipmentError(null);
    try {
      const res = await fetch('/shipments');
      if (!res.ok) {
        // Fallback to /api/shipments
        const alt = await fetch('/api/shipments');
        if (!alt.ok) throw new Error(`HTTP ${res.status}`);
        const data = await alt.json();
        const list = Array.isArray(data) ? data : (data.shipments || []);
        setShipments(list);
        return list;
      }
      const data = await res.json();
      const list = Array.isArray(data) ? data : (data.shipments || []);
      setShipments(list);
      return list;
    } catch (err) {
      setShipmentError(err.message);
      return [];
    } finally {
      setLoadingShipments(false);
    }
  }, []);

  /* ── 2. Fetch timeline for selected shipment ── */
  const fetchShipmentTimeline = useCallback(async (sid) => {
    if (!sid) return;
    setLoadingTimeline(true);
    setTimelineError(null);
    setExpandedDoc(null);
    try {
      let res = await fetch(`/shipments/${encodeURIComponent(sid)}/timeline`);
      if (!res.ok) {
        res = await fetch(`/api/shipments/${encodeURIComponent(sid)}/timeline`);
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setTimelineData(json);
    } catch (err) {
      setTimelineError(err.message);
    } finally {
      setLoadingTimeline(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchShipments().then(list => {
      if (list && list.length > 0) {
        // Pick 5RSG-79970 if available, else first shipment needing review, else first shipment
        const preferred = list.find(s => s.shipment_id === '5RSG-79970')
          || list.find(s => s.needs_review)
          || list[0];
        if (preferred) {
          setSelectedShipmentId(preferred.shipment_id);
        }
      }
    });
  }, [fetchShipments]);

  // Load timeline when selectedShipmentId changes
  useEffect(() => {
    if (selectedShipmentId) {
      fetchShipmentTimeline(selectedShipmentId);
    }
  }, [selectedShipmentId, fetchShipmentTimeline]);

  /* ── Derived: Unique Clients for Filter Chips ── */
  const clients = useMemo(() => {
    const set = new Set();
    shipments.forEach(s => {
      if (s.client && s.client !== 'Unknown') {
        set.add(s.client);
      }
    });
    return ['All', ...Array.from(set).sort()];
  }, [shipments]);

  /* ── Derived: Filtered Shipments for the Rail ── */
  const filteredShipments = useMemo(() => {
    return shipments.filter(s => {
      // 1. Client filter chip
      if (activeClient !== 'All' && s.client !== activeClient) {
        return false;
      }
      // 2. Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const sid = (s.shipment_id || '').toLowerCase();
        const title = (s.title || '').toLowerCase();
        const client = (s.client || '').toLowerCase();
        const port = (s.port || s.destination || '').toLowerCase();
        const carrier = (s.carrier || '').toLowerCase();
        const consignee = (s.consignee || '').toLowerCase();
        return sid.includes(q) || title.includes(q) || client.includes(q)
          || port.includes(q) || carrier.includes(q) || consignee.includes(q);
      }
      return true;
    });
  }, [shipments, activeClient, searchQuery]);

  /* ── Rail scroll buttons ── */
  const scrollRail = (direction) => {
    if (railScrollRef.current) {
      const offset = direction === 'left' ? -360 : 360;
      railScrollRef.current.scrollBy({ left: offset, behavior: 'smooth' });
    }
  };

  /* ── Selected shipment summary object ── */
  const selectedShipment = useMemo(() => {
    return shipments.find(s => s.shipment_id === selectedShipmentId) || null;
  }, [shipments, selectedShipmentId]);

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* ══ HEADER ══ */}
      <div className="px-6 py-4 border-b border-slate-800/80 bg-slate-900/40 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <span>Shipment Timeline</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold bg-violet-500/20 text-violet-300 border border-violet-500/30">
                Grouped by Shipment
              </span>
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Pick a shipment node from the rail to inspect its dedicated lifecycle, human corrections, and verified documents.
          </p>
        </div>

        {/* Search bar & Refresh */}
        <div className="flex items-center gap-3">
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search shipment (e.g. 79970, port)…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <button
            onClick={() => {
              fetchShipments();
              if (selectedShipmentId) fetchShipmentTimeline(selectedShipmentId);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-800/80 border border-slate-700 hover:bg-slate-700 transition"
            title="Refresh shipments"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingShipments || loadingTimeline ? 'animate-spin text-sky-400' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* ══ CARRIER / CLIENT FILTER CHIPS ══ */}
      <div className="px-6 py-2.5 bg-slate-900/20 border-b border-slate-800/60 flex items-center gap-2 overflow-x-auto no-scrollbar">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mr-1 shrink-0">
          Client Filter:
        </span>
        {clients.slice(0, 15).map(client => {
          const isActive = activeClient === client;
          return (
            <button
              key={client}
              onClick={() => setActiveClient(client)}
              className={`shrink-0 text-xs px-3 py-1 rounded-full font-medium transition cursor-pointer ${
                isActive
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/50 shadow-sm shadow-sky-500/20 font-semibold'
                  : 'bg-slate-900/80 text-slate-400 border border-slate-800 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              {client}
            </button>
          );
        })}
      </div>

      {/* ══ HORIZONTAL RAIL OF SHIPMENT NODES ══ */}
      <div className="relative px-6 py-3.5 border-b border-slate-800/80 bg-slate-950/60">
        {/* Rail Header with count and navigation controls */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <span>Shipments Rail</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                {filteredShipments.length} found
              </span>
            </span>
            {activeClient !== 'All' && (
              <span className="text-[11px] text-sky-400 font-medium">
                · Filtered by {activeClient}
              </span>
            )}
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => scrollRail('left')}
              className="p-1.5 rounded-md bg-slate-900/90 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition"
              title="Scroll left"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => scrollRail('right')}
              className="p-1.5 rounded-md bg-slate-900/90 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition"
              title="Scroll right"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Scrollable track of nodes */}
        {loadingShipments ? (
          <div className="py-6 flex items-center justify-center gap-2 text-xs text-slate-400">
            <RefreshCw className="w-4 h-4 animate-spin text-sky-400" />
            <span>Loading shipment rail…</span>
          </div>
        ) : filteredShipments.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-500 italic">
            No shipments match the selected filter. Try choosing "All" or clearing the search.
          </div>
        ) : (
          <div
            ref={railScrollRef}
            className="flex gap-3 overflow-x-auto pb-2 scroll-smooth no-scrollbar"
          >
            {filteredShipments.map(s => {
              const isSelected = s.shipment_id === selectedShipmentId;
              const stage = getStage(s.latest_stage, theme);
              const needsYou = Boolean(s.needs_review);

              return (
                <div
                  key={s.shipment_id}
                  onClick={() => setSelectedShipmentId(s.shipment_id)}
                  style={{
                    borderColor: isSelected ? stage.color : (needsYou ? 'rgba(245, 158, 11, 0.45)' : undefined)
                  }}
                  className={`shrink-0 w-64 p-3 rounded-xl cursor-pointer transition-all duration-200 select-none relative group border ${
                    isSelected
                      ? 'bg-slate-900 shadow-lg shadow-sky-950/50 ring-2 ring-offset-1 ring-offset-slate-950'
                      : 'bg-slate-900/70 border-slate-800/80 hover:bg-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  {/* Top row: ID + Stage Badge */}
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="font-mono text-xs font-bold text-white tracking-tight flex items-center gap-1.5">
                      <span
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{ background: stage.color, boxShadow: `0 0 6px ${stage.color}` }}
                      />
                      {s.shipment_id}
                    </span>

                    <span
                      style={{
                        color: stage.color,
                        background: stage.bg,
                        borderColor: stage.border
                      }}
                      className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border shrink-0 tracking-wider"
                    >
                      {stage.label}
                    </span>
                  </div>

                  {/* "Needs you" badge on unresolved mismatches */}
                  {needsYou && (
                    <div className="mb-2">
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
                        <AlertTriangle className="w-2.5 h-2.5 shrink-0" />
                        <span>Needs you</span>
                      </span>
                    </div>
                  )}

                  {/* Title (Port, Carrier, Consignee) */}
                  <p className="text-xs font-medium text-slate-200 line-clamp-1 mb-1" title={s.title}>
                    {s.title || s.shipment_id}
                  </p>

                  {/* Bottom meta row */}
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 pt-2 border-t border-slate-800/60 font-mono">
                    <span className="truncate max-w-[120px] text-slate-400" title={s.client}>
                      {s.client || 'Shipper'}
                    </span>
                    <span className="text-slate-400 text-[10px]">
                      {formatTime(s.latest_stage_timestamp || s.latest_timestamp)}
                    </span>
                  </div>

                  {/* Selected indicator triangle */}
                  {isSelected && (
                    <div
                      className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-3 h-3 bg-slate-900 border-r border-b border-sky-500 rotate-45"
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ══ DETAIL PANEL BELOW ══ */}
      <div className="flex-1 overflow-y-auto p-6 flex flex-col min-h-0 bg-slate-950">
        {/* Detail Panel Header */}
        {selectedShipmentId ? (
          <div className="mb-6 p-4 rounded-2xl bg-slate-900/70 border border-slate-800 flex flex-wrap items-center justify-between gap-4 shadow-md">
            <div>
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-bold text-white font-mono flex items-center gap-2">
                  <span>Shipment {selectedShipmentId}</span>
                </h3>
                {selectedShipment?.needs_review && (
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Unresolved Discrepancy — Needs Review</span>
                  </span>
                )}
                {!selectedShipment?.needs_review && timelineData && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Verified</span>
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-300 mt-1 flex items-center gap-2">
                <span className="font-semibold text-slate-200">
                  {timelineData?.title || selectedShipment?.title || 'Shipment Records'}
                </span>
                {timelineData?.carrier && (
                  <>
                    <span className="text-slate-600">•</span>
                    <span className="text-sky-400 font-medium">Carrier: {timelineData.carrier}</span>
                  </>
                )}
                {timelineData?.booking_ref && (
                  <>
                    <span className="text-slate-600">•</span>
                    <span className="text-slate-400 font-mono text-[11px]">Booking: {timelineData.booking_ref}</span>
                  </>
                )}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => fetchShipmentTimeline(selectedShipmentId)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingTimeline ? 'animate-spin' : ''}`} />
                <span>Reload History</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-slate-500 text-sm">
            Select a shipment from the rail above to inspect its history and documents.
          </div>
        )}

        {/* Two-Column Detail Grid: Left = History, Right = Documents */}
        {loadingTimeline ? (
          <div className="flex-1 flex items-center justify-center py-16 text-slate-400 text-sm gap-3">
            <RefreshCw className="w-5 h-5 animate-spin text-sky-400" />
            <span>Loading timeline for shipment {selectedShipmentId}…</span>
          </div>
        ) : timelineError ? (
          <div className="p-4 rounded-xl bg-red-950/30 border border-red-800/40 text-red-400 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>Failed to load timeline: {timelineError}</span>
          </div>
        ) : timelineData ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
            {/* ── COLUMN 1: HISTORY (Vertical Log, oldest to newest) ── */}
            <div className="lg:col-span-7 flex flex-col min-h-0 bg-slate-900/40 rounded-2xl border border-slate-800/80 p-5">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-sky-400" />
                  <h4 className="text-sm font-bold text-white uppercase tracking-wider">
                    Shipment History & Audit Log
                  </h4>
                </div>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {timelineData.history?.length || 0} events
                </span>
              </div>

              {/* Chronological Vertical Event Log */}
              <div className="flex-1 overflow-y-auto pr-2 space-y-4">
                {(!timelineData.history || timelineData.history.length === 0) ? (
                  <p className="text-xs text-slate-500 italic py-8 text-center">
                    No historical events recorded for this shipment.
                  </p>
                ) : (
                  timelineData.history.map((event, idx) => {
                    const actorType = event.actor; // "system" | "ai" | "human"
                    const isHuman = actorType === 'human';
                    const isAI = actorType === 'ai';
                    const isSystem = actorType === 'system';

                    return (
                      <div
                        key={event.event_id || idx}
                        className={`relative pl-8 pb-2 group ${
                          idx !== timelineData.history.length - 1 ? 'before:absolute before:left-3.5 before:top-8 before:bottom-0 before:w-0.5 before:bg-slate-800 group-hover:before:bg-slate-700' : ''
                        }`}
                      >
                        {/* Node Icon on vertical rail */}
                        <div
                          className={`absolute left-0 top-1.5 w-7 h-7 rounded-full flex items-center justify-center border shadow-sm ${
                            isHuman
                              ? 'bg-amber-500/20 border-amber-500 text-amber-300'
                              : isAI
                              ? 'bg-purple-500/20 border-purple-500 text-purple-300'
                              : 'bg-sky-500/20 border-sky-500 text-sky-300'
                          }`}
                        >
                          {isHuman && <ShieldCheck className="w-3.5 h-3.5" />}
                          {isAI && <Cpu className="w-3.5 h-3.5" />}
                          {isSystem && <Layers className="w-3.5 h-3.5" />}
                        </div>

                        {/* Event Card */}
                        <div
                          className={`p-4 rounded-xl border transition ${
                            isHuman
                              ? 'bg-amber-950/15 border-amber-500/40 shadow-sm shadow-amber-950/30'
                              : isAI
                              ? 'bg-purple-950/15 border-purple-500/30 shadow-sm shadow-purple-950/20'
                              : 'bg-slate-900/70 border-slate-800'
                          }`}
                        >
                          {/* Header: Actor Badge + Name + Timestamp */}
                          <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                            <div className="flex items-center gap-2">
                              {/* Distinct Actor Tag */}
                              <span
                                className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border font-mono ${
                                  isHuman
                                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                                    : isAI
                                    ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                                    : 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                                }`}
                              >
                                {isHuman ? 'Human Actor' : isAI ? 'AI Agent' : 'System Engine'}
                              </span>

                              <span className="text-xs font-semibold text-slate-200">
                                {event.actor_name}
                              </span>
                            </div>

                            <span className="text-[11px] text-slate-400 font-mono">
                              {formatTime(event.timestamp)}
                            </span>
                          </div>

                          {/* Action Description */}
                          <p className="text-xs text-slate-200 leading-relaxed font-sans">
                            {event.action_text}
                          </p>

                          {/* Human Correction Link Back to AI Action */}
                          {isHuman && (
                            <div className="mt-3 p-2.5 rounded-lg bg-amber-950/30 border border-amber-700/50 flex flex-wrap items-center justify-between gap-2 text-xs">
                              <div className="flex items-center gap-2 text-amber-200">
                                <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                                <span className="font-semibold">Flagged by AI comparison</span>
                                {event.related_field && (
                                  <>
                                    <span className="text-amber-500">•</span>
                                    <span>
                                      Field: <code className="font-mono text-amber-300 bg-amber-950 px-1.5 py-0.5 rounded border border-amber-700/60 font-semibold">{event.related_field}</code>
                                    </span>
                                  </>
                                )}
                              </div>
                              <span className="text-[10px] font-mono text-amber-400/90 font-medium">
                                Feedback Link Saved
                              </span>
                            </div>
                          )}

                          {/* Field Tag for AI discrepancies */}
                          {!isHuman && event.related_field && (
                            <div className="mt-2 flex items-center gap-2">
                              <span className="text-[11px] text-slate-400">Target Field:</span>
                              <code className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-sky-300 border border-slate-700">
                                {event.related_field}
                              </code>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* ── COLUMN 2: DOCUMENTS (List with status badges & inline preview) ── */}
            <div className="lg:col-span-5 flex flex-col min-h-0 bg-slate-900/40 rounded-2xl border border-slate-800/80 p-5">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-emerald-400" />
                  <h4 className="text-sm font-bold text-white uppercase tracking-wider">
                    Shipment Documents
                  </h4>
                </div>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {timelineData.documents?.length || 0} attached
                </span>
              </div>

              {/* Documents List */}
              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {(!timelineData.documents || timelineData.documents.length === 0) ? (
                  <p className="text-xs text-slate-500 italic py-8 text-center">
                    No documents attached to this shipment.
                  </p>
                ) : (
                  timelineData.documents.map((doc, i) => {
                    const isExpanded = expandedDoc === doc.name;
                    const isVerified = doc.status === 'verified';
                    const isMismatch = doc.status === 'mismatch';

                    return (
                      <div
                        key={doc.name || i}
                        className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-300 shrink-0 border border-slate-700">
                              <FileText className="w-4 h-4 text-sky-400" />
                            </div>
                            <div className="min-w-0">
                              <p className="text-xs font-semibold text-slate-200 truncate font-mono" title={doc.name}>
                                {doc.name}
                              </p>
                              <div className="flex items-center gap-2 mt-0.5">
                                <span className="text-[10px] font-bold font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                                  {doc.type}
                                </span>
                                {doc.linked_event_id && (
                                  <span className="text-[10px] text-slate-400 font-mono truncate">
                                    ref: {doc.linked_event_id}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Status Badge */}
                          <div className="flex items-center gap-2 shrink-0">
                            {isVerified && (
                              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                                <CheckCircle2 className="w-2.5 h-2.5" />
                                Verified
                              </span>
                            )}
                            {isMismatch && (
                              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/30 flex items-center gap-1">
                                <AlertTriangle className="w-2.5 h-2.5" />
                                Mismatch
                              </span>
                            )}
                            {!isVerified && !isMismatch && (
                              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1">
                                <Clock className="w-2.5 h-2.5" />
                                Pending
                              </span>
                            )}

                            {/* Toggle inline preview */}
                            <button
                              onClick={() => setExpandedDoc(isExpanded ? null : doc.name)}
                              className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition"
                              title={isExpanded ? 'Collapse preview' : 'Expand inline preview'}
                            >
                              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>
                          </div>
                        </div>

                        {/* Expandable Inline Preview */}
                        {isExpanded && (
                          <div className="mt-3 pt-3 border-t border-slate-800 animate-fadeIn">
                            <DocumentPreview doc={doc} />
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
