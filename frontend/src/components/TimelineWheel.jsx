import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  AlertTriangle, CheckCircle2, Clock, FileText,
  GitCompare, Eye, ChevronDown, ChevronUp,
  AlertCircle, RefreshCw, X,
  ChevronLeft, ChevronRight, Search,
  Copy, Check, User, Bot, Zap
} from 'lucide-react';

const STAGE_CONFIG = {
  all:     { label: 'All',          color: '#94a3b8', bg: 'rgba(148,163,184,0.12)', border: 'rgba(148,163,184,0.3)' },
  si:      { label: 'SI Ingestion', color: '#818cf8', bg: 'rgba(129,140,248,0.12)', border: 'rgba(129,140,248,0.35)' },
  bl:      { label: 'BL Draft',     color: '#38bdf8', bg: 'rgba(56,189,248,0.12)',  border: 'rgba(56,189,248,0.35)' },
  draft:   { label: 'AI Draft',     color: '#a78bfa', bg: 'rgba(167,139,250,0.12)', border: 'rgba(167,139,250,0.35)' },
  compare: { label: 'Comparison',   color: '#fb923c', bg: 'rgba(251,146,60,0.12)',  border: 'rgba(251,146,60,0.35)' },
  review:  { label: 'Human Review', color: '#fbbf24', bg: 'rgba(251,191,36,0.12)',  border: 'rgba(251,191,36,0.35)' },
  sent:    { label: 'Sent',         color: '#34d399', bg: 'rgba(52,211,153,0.12)',  border: 'rgba(52,211,153,0.35)' },
};
function getStage(key) { return STAGE_CONFIG[key] || STAGE_CONFIG.bl; }
function formatTime(ts) {
  if (!ts) return '-';
  try {
    return new Intl.DateTimeFormat('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    }).format(new Date(ts));
  } catch { return ts; }
}

function ActorBadge({ actor, name }) {
  if (actor === 'human') return (
    <div className="flex items-center gap-1.5">
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider font-mono bg-amber-500/15 text-amber-300 border border-amber-500/35">
        <User className="w-2.5 h-2.5" />Human
      </span>
      <span className="text-xs text-slate-300 truncate max-w-[110px]">{name}</span>
    </div>
  );
  if (actor === 'ai') return (
    <div className="flex items-center gap-1.5">
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider font-mono bg-violet-500/15 text-violet-300 border border-violet-500/35">
        <Bot className="w-2.5 h-2.5" />AI Agent
      </span>
      <span className="text-xs text-slate-400 truncate max-w-[110px]">{name}</span>
    </div>
  );
  return (
    <div className="flex items-center gap-1.5">
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider font-mono bg-sky-500/15 text-sky-300 border border-sky-500/35">
        <Zap className="w-2.5 h-2.5" />System
      </span>
      <span className="text-xs text-slate-400 truncate max-w-[110px]">{name}</span>
    </div>
  );
}

function StagePill({ stage }) {
  const cfg = getStage(stage);
  return (
    <span style={{ color: cfg.color, background: cfg.bg, borderColor: cfg.border }}
      className="inline-block text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border font-mono whitespace-nowrap">
      {cfg.label}
    </span>
  );
}

function DocStatusBadge({ status }) {
  if (status === 'verified') return (
    <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
      <CheckCircle2 className="w-2.5 h-2.5" />Verified
    </span>
  );
  if (status === 'mismatch') return (
    <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/30">
      <AlertTriangle className="w-2.5 h-2.5" />Mismatch
    </span>
  );
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
      <Clock className="w-2.5 h-2.5" />Pending
    </span>
  );
}

function DocumentPreview({ doc }) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    let ok = true;
    if (!doc?.file_url) return;
    setLoading(true); setError(null);
    fetch(doc.file_url)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.text(); })
      .then(t => { if (ok) setContent(t); })
      .catch(e => { if (ok) setError(e.message); })
      .finally(() => { if (ok) setLoading(false); });
    return () => { ok = false; };
  }, [doc]);
  const handleCopy = () => {
    if (content) { navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 2000); }
  };
  if (loading) return <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 text-xs text-slate-400 flex items-center gap-2"><RefreshCw className="w-3.5 h-3.5 animate-spin text-sky-400" /><span>Loading preview...</span></div>;
  if (error) return <div className="p-3 bg-red-950/30 rounded-lg border border-red-800/40 text-xs text-red-400">Failed: {error}</div>;
  return (
    <div className="mt-1 bg-slate-950 rounded-lg border border-slate-800/90 overflow-hidden shadow-inner">
      <div className="px-3 py-1.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <span>{doc.name}</span>
        <button onClick={handleCopy} className="flex items-center gap-1 hover:text-slate-200 transition">
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <pre className="p-3 text-[11px] font-mono text-slate-300 leading-relaxed max-h-52 overflow-y-auto whitespace-pre-wrap">
        {content || 'Empty or binary.'}
      </pre>
    </div>
  );
}

export default function TimelineWheel() {
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
  const [historySearch, setHistorySearch] = useState('');
  const [historyActorFilter, setHistoryActorFilter] = useState('all');
  const railScrollRef = useRef(null);

  const fetchShipments = useCallback(async () => {
    setLoadingShipments(true); setShipmentError(null);
    try {
      let res = await fetch('/shipments');
      if (!res.ok) res = await fetch('/api/shipments');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const list = Array.isArray(data) ? data : (data.shipments || []);
      setShipments(list); return list;
    } catch (err) { setShipmentError(err.message); return []; }
    finally { setLoadingShipments(false); }
  }, []);

  const fetchShipmentTimeline = useCallback(async (sid) => {
    if (!sid) return;
    setLoadingTimeline(true); setTimelineError(null);
    setExpandedDoc(null); setHistorySearch(''); setHistoryActorFilter('all');
    try {
      let res = await fetch(`/shipments/${encodeURIComponent(sid)}/timeline`);
      if (!res.ok) res = await fetch(`/api/shipments/${encodeURIComponent(sid)}/timeline`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setTimelineData(await res.json());
    } catch (err) { setTimelineError(err.message); }
    finally { setLoadingTimeline(false); }
  }, []);

  useEffect(() => {
    fetchShipments().then(list => {
      if (list && list.length > 0) {
        const preferred = list.find(s => s.shipment_id === '5RSG-79970') || list.find(s => s.needs_review) || list[0];
        if (preferred) setSelectedShipmentId(preferred.shipment_id);
      }
    });
  }, [fetchShipments]);

  useEffect(() => {
    if (selectedShipmentId) fetchShipmentTimeline(selectedShipmentId);
  }, [selectedShipmentId, fetchShipmentTimeline]);

  const clients = useMemo(() => {
    const set = new Set();
    shipments.forEach(s => { if (s.client && s.client !== 'Unknown') set.add(s.client); });
    return ['All', ...Array.from(set).sort()];
  }, [shipments]);

  const filteredShipments = useMemo(() => {
    return shipments.filter(s => {
      if (activeClient !== 'All' && s.client !== activeClient) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        return ['shipment_id', 'title', 'client', 'port', 'destination', 'carrier', 'consignee']
          .some(k => (s[k] || '').toLowerCase().includes(q));
      }
      return true;
    });
  }, [shipments, activeClient, searchQuery]);

  const filteredHistory = useMemo(() => {
    if (!timelineData?.history) return [];
    return timelineData.history.filter(ev => {
      if (historyActorFilter !== 'all' && ev.actor !== historyActorFilter) return false;
      if (historySearch.trim()) {
        const q = historySearch.toLowerCase();
        return ['action_text', 'actor_name', 'related_field', 'stage'].some(k => (ev[k] || '').toLowerCase().includes(q));
      }
      return true;
    });
  }, [timelineData, historySearch, historyActorFilter]);

  const selectedShipment = useMemo(() =>
    shipments.find(s => s.shipment_id === selectedShipmentId) || null,
    [shipments, selectedShipmentId]
  );

  const scrollRail = dir => {
    if (railScrollRef.current)
      railScrollRef.current.scrollBy({ left: dir === 'left' ? -360 : 360, behavior: 'smooth' });
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#070a12] text-slate-100 font-sans overflow-hidden">

      {/* HEADER */}
      <div className="px-6 py-4 border-b border-slate-800/80 bg-slate-900/40 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            Shipment Timeline
            <span className="text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold bg-violet-500/20 text-violet-300 border border-violet-500/30">
              Grouped by Shipment
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Pick a shipment to inspect its audit log, comparison matrix, and documents.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input type="text" placeholder="Search shipment ID, port..."
              value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition" />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
          <button onClick={() => { fetchShipments(); if (selectedShipmentId) fetchShipmentTimeline(selectedShipmentId); }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-800/80 border border-slate-700 hover:bg-slate-700 transition">
            <RefreshCw className={`w-3.5 h-3.5 ${(loadingShipments || loadingTimeline) ? 'animate-spin text-sky-400' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* CLIENT FILTER CHIPS */}
      <div className="px-6 py-2.5 bg-slate-900/20 border-b border-slate-800/60 flex items-center gap-2 overflow-x-auto no-scrollbar">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mr-1 shrink-0">Client:</span>
        {clients.slice(0, 15).map(c => (
          <button key={c} onClick={() => setActiveClient(c)}
            className={`shrink-0 text-xs px-3 py-1 rounded-full font-medium transition cursor-pointer ${
              activeClient === c
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/50 font-semibold'
                : 'bg-slate-900/80 text-slate-400 border border-slate-800 hover:bg-slate-800 hover:text-slate-200'
            }`}>
            {c}
          </button>
        ))}
      </div>

      {/* SHIPMENT RAIL */}
      <div className="relative px-6 py-3.5 border-b border-slate-800/80 bg-slate-950/60">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              Shipments Rail
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                {filteredShipments.length} found
              </span>
            </span>
            {activeClient !== 'All' && (
              <span className="text-[11px] text-sky-400 font-medium">- Filtered: {activeClient}</span>
            )}
          </div>
          <div className="flex items-center gap-1">
            <button onClick={() => scrollRail('left')} className="p-1.5 rounded-md bg-slate-900/90 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button onClick={() => scrollRail('right')} className="p-1.5 rounded-md bg-slate-900/90 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {loadingShipments ? (
          <div className="py-6 flex items-center justify-center gap-2 text-xs text-slate-400">
            <RefreshCw className="w-4 h-4 animate-spin text-sky-400" /><span>Loading rail...</span>
          </div>
        ) : filteredShipments.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-500 italic">
            No shipments found. Try "All" or clear search.
          </div>
        ) : (
          <div ref={railScrollRef} className="flex gap-3 overflow-x-auto pb-2 scroll-smooth no-scrollbar">
            {filteredShipments.map(s => {
              const isSelected = s.shipment_id === selectedShipmentId;
              const stage = getStage(s.latest_stage);
              const needsYou = Boolean(s.needs_review);
              return (
                <div key={s.shipment_id} onClick={() => setSelectedShipmentId(s.shipment_id)}
                  style={{ borderColor: isSelected ? stage.color : (needsYou ? 'rgba(245,158,11,0.45)' : undefined) }}
                  className={`shrink-0 w-56 p-3 rounded-xl cursor-pointer transition-all duration-200 select-none relative border ${
                    isSelected
                      ? 'bg-slate-900 shadow-lg ring-2 ring-offset-1 ring-offset-slate-950 ring-sky-500/50'
                      : 'bg-slate-900/70 border-slate-800/80 hover:bg-slate-800/80 hover:border-slate-700'
                  }`}>
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="font-mono text-xs font-bold text-white flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full shrink-0"
                        style={{ background: stage.color, boxShadow: `0 0 6px ${stage.color}` }} />
                      {s.shipment_id}
                    </span>
                    <span style={{ color: stage.color, background: stage.bg, borderColor: stage.border }}
                      className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border shrink-0 tracking-wider">
                      {stage.label}
                    </span>
                  </div>
                  {needsYou && (
                    <div className="mb-1.5">
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
                        <AlertTriangle className="w-2.5 h-2.5 shrink-0" />Needs you
                      </span>
                    </div>
                  )}
                  <p className="text-xs font-medium text-slate-200 line-clamp-1 mb-1">{s.title || s.shipment_id}</p>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 pt-2 border-t border-slate-800/60 font-mono">
                    <span className="truncate max-w-[100px]">{s.client || 'Shipper'}</span>
                    <span className="text-[10px]">{formatTime(s.latest_stage_timestamp || s.latest_timestamp)}</span>
                  </div>
                  {isSelected && (
                    <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-3 h-3 bg-slate-900 border-r border-b border-sky-500 rotate-45" />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* DETAIL PANEL */}
      <div className="flex-1 overflow-y-auto p-6 flex flex-col min-h-0 bg-[#070a12] gap-5">

        {!selectedShipmentId && (
          <div className="p-8 text-center text-slate-500 text-sm">
            Select a shipment from the rail above.
          </div>
        )}

        {selectedShipmentId && (
          <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 flex flex-wrap items-center justify-between gap-4 shadow-md">
            <div>
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-bold text-white font-mono">Shipment {selectedShipmentId}</h3>
                {selectedShipment?.needs_review && (
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
                    <AlertTriangle className="w-3.5 h-3.5" />Unresolved Discrepancy
                  </span>
                )}
                {!selectedShipment?.needs_review && timelineData && (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                    <CheckCircle2 className="w-3.5 h-3.5" />Verified
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-300 mt-1 flex flex-wrap items-center gap-2">
                <span className="font-semibold text-slate-200">{timelineData?.title || selectedShipment?.title || 'Shipment Records'}</span>
                {timelineData?.carrier && <><span className="text-slate-600">|</span><span className="text-sky-400 font-medium">Carrier: {timelineData.carrier}</span></>}
                {timelineData?.booking_ref && <><span className="text-slate-600">|</span><span className="text-slate-400 font-mono text-[11px]">Booking: {timelineData.booking_ref}</span></>}
              </p>
            </div>
            <button onClick={() => fetchShipmentTimeline(selectedShipmentId)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition">
              <RefreshCw className={`w-3.5 h-3.5 ${loadingTimeline ? 'animate-spin' : ''}`} />
              Reload History
            </button>
          </div>
        )}

        {loadingTimeline && (
          <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-3">
            <RefreshCw className="w-5 h-5 animate-spin text-sky-400" />
            <span>Loading timeline for {selectedShipmentId}...</span>
          </div>
        )}

        {timelineError && (
          <div className="p-4 rounded-xl bg-red-950/30 border border-red-800/40 text-red-400 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>Error: {timelineError}</span>
          </div>
        )}

        {!loadingTimeline && !timelineError && timelineData && (
          <>
            {/* TABLE 1: AUDIT LOG */}
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden shadow-md">
              <div className="px-5 py-3 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-900/60">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-sky-400" />
                  <h4 className="text-sm font-bold text-white uppercase tracking-wider">Shipment Audit Log</h4>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                    {timelineData.history?.length || 0} events
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-0.5">
                    {[{id:'all',label:'All'},{id:'system',label:'System'},{id:'ai',label:'AI'},{id:'human',label:'Human'}].map(f => (
                      <button key={f.id} onClick={() => setHistoryActorFilter(f.id)}
                        className={`px-2.5 py-1 rounded text-[11px] font-semibold font-mono transition ${
                          historyActorFilter === f.id
                            ? 'bg-slate-700 text-slate-100 border border-slate-500'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-transparent'
                        }`}>
                        {f.label}
                      </button>
                    ))}
                  </div>
                  <div className="relative w-44">
                    <Search className="w-3 h-3 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input type="text" placeholder="Filter log..." value={historySearch}
                      onChange={e => setHistorySearch(e.target.value)}
                      className="w-full bg-slate-900/80 border border-slate-700/80 rounded-lg pl-7 pr-3 py-1 text-[11px] text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition" />
                    {historySearch && (
                      <button onClick={() => setHistorySearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200">
                        <X className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-900/80 border-b border-slate-800">
                      <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider w-8">#</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider min-w-[180px]">Actor</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">Stage</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">Action / Description</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">Field</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredHistory.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-4 py-10 text-center text-slate-500 italic">
                          No events match the current filter.
                        </td>
                      </tr>
                    ) : filteredHistory.map((ev, idx) => {
                      const isHuman = ev.actor === 'human';
                      const isAI    = ev.actor === 'ai';
                      const rowCls  = isHuman
                        ? 'bg-amber-950/10 hover:bg-amber-950/20 border-amber-700/20'
                        : isAI
                        ? 'bg-violet-950/10 hover:bg-violet-950/20 border-violet-800/20'
                        : 'hover:bg-slate-900/60 border-slate-800/40';
                      return (
                        <tr key={ev.event_id || idx} className={`border-b transition-colors ${rowCls}`}>
                          <td className="px-4 py-3 font-mono text-slate-500 text-[11px] align-top">{idx + 1}</td>
                          <td className="px-4 py-3 align-top">
                            <ActorBadge actor={ev.actor} name={ev.actor_name} />
                          </td>
                          <td className="px-4 py-3 align-top">
                            <StagePill stage={ev.stage} />
                          </td>
                          <td className="px-4 py-3 align-top max-w-[380px]">
                            <p className="text-slate-200 leading-relaxed">{ev.action_text}</p>
                            {isHuman && (
                              <div className="mt-1.5 flex items-center gap-1.5 text-[10px] text-amber-400 font-semibold">
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping shrink-0" />
                                Flagged by AI comparison - Feedback link saved
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3 align-top">
                            {ev.related_field
                              ? <code className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-sky-300 border border-slate-700 whitespace-nowrap">{ev.related_field}</code>
                              : <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3 align-top font-mono text-[11px] text-slate-400 whitespace-nowrap">
                            {formatTime(ev.timestamp)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* TABLE 2: FIELD COMPARISON MATRIX */}
            {timelineData.field_matrix && timelineData.field_matrix.length > 0 && (
              <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden shadow-md">
                <div className="px-5 py-3 border-b border-slate-800 flex items-center gap-2 bg-slate-900/60">
                  <GitCompare className="w-4 h-4 text-orange-400" />
                  <h4 className="text-sm font-bold text-white uppercase tracking-wider">AI Field Comparison Matrix</h4>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                    {timelineData.field_matrix.filter(r => !r.is_match).length} discrepancies
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-900/80 border-b border-slate-800">
                        <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">Field</th>
                        <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">SI Value</th>
                        <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">BL Value</th>
                        <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">Result</th>
                        <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">Summary</th>
                      </tr>
                    </thead>
                    <tbody>
                      {timelineData.field_matrix.map((row, idx) => (
                        <tr key={row.field_key || idx}
                          className={`border-b transition-colors ${row.is_match ? 'border-slate-800/40 hover:bg-slate-900/40' : 'bg-red-950/10 border-red-800/20 hover:bg-red-950/20'}`}>
                          <td className="px-4 py-3 align-top">
                            <code className="font-mono text-[11px] text-sky-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                              {row.field_key}
                            </code>
                          </td>
                          <td className="px-4 py-3 align-top font-mono text-slate-200">
                            {row.si_value != null ? row.si_value : <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3 align-top font-mono text-slate-200">
                            {row.bl_value != null ? row.bl_value : <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3 align-top">
                            {row.is_match
                              ? <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"><CheckCircle2 className="w-2.5 h-2.5" />Match</span>
                              : <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/30"><AlertTriangle className="w-2.5 h-2.5" />Mismatch</span>}
                          </td>
                          <td className="px-4 py-3 align-top text-slate-400">{row.diff_summary || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TABLE 3: DOCUMENTS */}
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden shadow-md">
              <div className="px-5 py-3 border-b border-slate-800 flex items-center gap-2 bg-slate-900/60">
                <FileText className="w-4 h-4 text-emerald-400" />
                <h4 className="text-sm font-bold text-white uppercase tracking-wider">Shipment Documents</h4>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {timelineData.documents?.length || 0} attached
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-900/80 border-b border-slate-800">
                      <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">Document</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">Type</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">Linked Event</th>
                      <th className="text-left px-4 py-2.5 font-semibold text-slate-400 uppercase tracking-wider">Preview</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(!timelineData.documents || timelineData.documents.length === 0) ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-10 text-center text-slate-500 italic">No documents attached.</td>
                      </tr>
                    ) : timelineData.documents.map((doc, i) => {
                      const isExpanded = expandedDoc === doc.name;
                      return (
                        <React.Fragment key={doc.name || i}>
                          <tr className="border-b border-slate-800/40 hover:bg-slate-900/50 transition-colors">
                            <td className="px-4 py-3 align-top">
                              <div className="flex items-center gap-2">
                                <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
                                  <FileText className="w-3.5 h-3.5 text-sky-400" />
                                </div>
                                <span className="font-mono text-slate-200 text-[11px] font-semibold">{doc.name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 align-top">
                              <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">{doc.type}</span>
                            </td>
                            <td className="px-4 py-3 align-top">
                              <DocStatusBadge status={doc.status} />
                            </td>
                            <td className="px-4 py-3 align-top font-mono text-[11px] text-slate-400">
                              {doc.linked_event_id || '-'}
                            </td>
                            <td className="px-4 py-3 align-top">
                              <button onClick={() => setExpandedDoc(isExpanded ? null : doc.name)}
                                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium text-slate-300 bg-slate-800/80 hover:bg-slate-700 border border-slate-700 transition">
                                <Eye className="w-3 h-3 text-sky-400" />
                                {isExpanded ? 'Collapse' : 'Preview'}
                                {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                              </button>
                            </td>
                          </tr>
                          {isExpanded && (
                            <tr className="border-b border-slate-800/40 bg-slate-950/60">
                              <td colSpan={5} className="px-4 py-3">
                                <DocumentPreview doc={doc} />
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
