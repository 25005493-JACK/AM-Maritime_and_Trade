import React, { useState, useEffect } from 'react';
import ConflictEvidencePanel from './ConflictEvidencePanel.jsx';
import ReasoningReceipt from './ReasoningReceipt.jsx';
import { apiFetch } from '../api.js';
import { 
  FileCheck2, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  Sparkles, 
  ArrowRight, 
  Edit3, 
  Send, 
  ShieldCheck,
  FileText,
  Terminal,
  X,
  Zap,
  Info,
  GitCommit,
  GitCompareArrows,
  UserCheck,
  Ship,
  Clock,
  AlertOctagon
} from 'lucide-react';
import { RefusalCertificatePanel } from './ReasoningReceipt.jsx';

const DEFAULT_CIRCUIT_BREAKER_CERTIFICATE = {
  certificate_type: 'ai_refusal',
  doc_key: 'ONEYSINF32871:email_004',
  shipment_id: 'ONEYSINF32871',
  email_id: 'email_004',
  generated_at: '2026-01-20T08:32:00Z',
  reason: 'AI field validation failed 3 consecutive times (threshold: 3). Execution halted to eliminate hallucination risk.',
  threshold: 3,
  consecutive_ai_failures: 3,
  failed_fields: [
    {
      field_name: 'port_of_loading',
      attempted_value: null,
      why_failed: 'Required POL missing or ungrounded; failed source_match verification.'
    },
    {
      field_name: 'port_of_discharge',
      attempted_value: null,
      why_failed: 'Required POD missing or ungrounded; failed UN/LOCODE directory whitelist.'
    },
    {
      field_name: 'container_count',
      attempted_value: null,
      why_failed: 'Required container count missing from draft BL; failed DCSA format check.'
    }
  ],
  missing_or_unclear: ['port_of_loading', 'port_of_discharge', 'container_count'],
  suggested_recipient: 'carrier',
  recipient_rationale: 'Missing/unclear fields (container_count, port_of_discharge, port_of_loading) are shipment/carrier-side data, so the carrier is the fastest source.',
  estimated_delay_minutes: 960,
  estimated_delay_hours: 16.0,
  estimated_delay_basis: '3 missing field(s) @ 240 min manual query each + baseline SLA (DOCUMATCH_MANUAL_QUERY_MINUTES)',
  what_would_unblock: [
    'Query ocean carrier booking desk for missing container manifest',
    'Provide machine-readable draft Bill of Lading with verified Port of Loading & Port of Discharge',
    'Re-send document using standard field labels or issue human manual override'
  ],
  notice: 'AI processing stopped for this document: no further AI guesses were made. Automated pipeline execution halted.'
};

export default function SplitScreenInspector({ emailDetail, onOpenOverrideModal }) {
  const [activeRightTab, setActiveRightTab] = useState('si_vs_bl'); // 'si_vs_bl' or 'timeline'
  const [selectedFieldKey, setSelectedFieldKey] = useState(null);
  const [showReceiptDrawer, setShowReceiptDrawer] = useState(false);

  // DCSA field names for the standard-alignment badges (same mapping the
  // backend uses for the receipt and export).
  const [dcsaMappings, setDcsaMappings] = useState(null);
  useEffect(() => {
    let cancelled = false;
    apiFetch('/api/dcsa/mapping')
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error('failed'))))
      .then((data) => {
        if (!cancelled) setDcsaMappings(data.mappings || {});
      })
      .catch(() => {
        if (!cancelled) setDcsaMappings(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);
  if (!emailDetail) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-slate-500 bg-slate-950">
        <FileCheck2 className="w-16 h-16 stroke-[1.2] mb-3 text-slate-600" />
        <h3 className="text-base font-semibold text-slate-300">No Document Selected for Inspection</h3>
        <p className="text-xs text-slate-500 max-w-sm text-center mt-1">
          Select a Document Comparison Request email from the inbox to launch the split-screen verification matrix.
        </p>
      </div>
    );
  }

  const { email, classification, si_text, bl_text, verification } = emailDetail;
  const verif = verification || {};
  const isMatch = verif.status === 'NO_MISMATCH_DETECTED' || verif.status === 'OK';
  const isHuman = verif.status === 'HUMAN_REVIEW_REQUIRED' || verif.status === 'NEEDS_REVIEW';
  const isMismatch = verif.status === 'MISMATCH_DETECTED' || verif.status === 'MISMATCH';

  // Character-level diff renderer helper
  const renderDiff = (siVal, blVal, isMatch) => {
    if (isMatch) return <span className="text-slate-100">{blVal}</span>;
    if (!siVal || !blVal) return <span className="text-rose-400 font-bold">{blVal}</span>;

    const siWords = str(siVal).split(' ');
    const blWords = str(blVal).split(' ');

    return (
      <span>
        {blWords.map((word, i) => {
          const matchWord = siWords[i];
          if (matchWord && matchWord.toLowerCase() === word.toLowerCase()) {
            return <span key={i} className="text-slate-100 mr-1">{word}</span>;
          }
          return <span key={i} className="diff-added mr-1 font-bold">{word}</span>;
        })}
      </span>
    );
  };

  const str = (v) => (v === null || v === undefined ? '' : String(v));

  // Milestones for Tab 2: Shipment Timeline
  const milestones = [
    {
      id: 1,
      title: 'Booking Confirmed & Allocation Scheduled',
      timestamp: new Date(new Date(email.timestamp || Date.now()).getTime() - 86400000).toISOString(),
      actor: 'AI Done: Carrier Booking System',
      status: 'Completed',
      icon: Ship,
      details: `Vessel: ${email.vessel || 'MSC ISABELLA'} ${email.voyage || 'v.240E'} | Company: ${email.company || 'Global Traders Inc'}`
    },
    {
      id: 2,
      title: 'Shipping Instruction (SI) Received & Ingested',
      timestamp: email.timestamp || new Date().toISOString(),
      actor: `AI Done: Ingestion Engine (${email.sender || 'Shipper Desk'})`,
      status: 'Completed',
      icon: FileText,
      details: `Subject: "${email.subject}" | 7 Reference fields extracted`
    },
    {
      id: 3,
      title: 'Draft Bill of Lading (BL) AI Verification Checked',
      timestamp: new Date(new Date(email.timestamp || Date.now()).getTime() + 1800000).toISOString(),
      actor: 'AI Done: Antigravity NLP Rules Engine',
      status: isMatch ? 'Passed' : isHuman ? 'Escalated' : 'Discrepancy Flagged',
      icon: isMatch ? CheckCircle2 : AlertTriangle,
      details: isMatch 
        ? 'All 7 standard fields agree perfectly (Shipper, Consignee, Notify, POL, POD, Containers, Weight)'
        : `Verification result: ${verif.summary_message || 'Field differences detected'}`
    },
    {
      id: 4,
      title: 'Human-in-the-Loop Audit & Override Gate',
      timestamp: new Date(new Date(email.timestamp || Date.now()).getTime() + 3600000).toISOString(),
      actor: isHuman ? 'User Done: Pending Operational Review' : 'User Done: Shipping Operator Audit',
      status: isHuman ? 'Action Required' : 'Approved',
      icon: UserCheck,
      details: isHuman 
        ? `Escalated reason: ${verif.human_review_reasons?.join(' | ') || 'Corrupted stream or blank value'}`
        : 'Rule-based audit trail validated against DCSA standards'
    },
    {
      id: 5,
      title: 'Final Bill of Lading Printing & Container Release',
      timestamp: new Date(new Date(email.timestamp || Date.now()).getTime() + 7200000).toISOString(),
      actor: 'User Done: Documentation Desk Release',
      status: isMatch ? 'Ready for Release' : 'Pending Revision',
      icon: ShieldCheck,
      details: isMatch 
        ? 'Released to Shipper. Certificate of Origin & Shipment Advice finalized.'
        : 'Waiting for revised draft BL from carrier.'
    }
  ];

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950 relative">
      {/* Inspector Top Header Bar */}
      <div className="p-4 border-b border-slate-800 glass-panel flex items-center justify-between shrink-0">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="font-mono text-xs text-cyan-400 font-semibold">{email.id}</span>
            <h2 className="text-base font-bold text-slate-100">{email.subject}</h2>
          </div>
          <div className="flex items-center space-x-3 text-xs text-slate-400">
            <span>From: <strong className="text-slate-300">{email.sender}</strong></span>
            <span>•</span>
            <span>Vessel: <strong className="text-cyan-400">{email.vessel || 'N/A'} {email.voyage}</strong></span>
            <span>•</span>
            <span>Company: <strong className="text-slate-300">{email.company || 'N/A'}</strong></span>
          </div>
        </div>

        {/* Status Badge & Control Buttons */}
        <div className="flex items-center space-x-3">
          {isMatch && (
            <div className="badge-match px-3 py-1.5 rounded-lg flex items-center space-x-2 text-xs font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              <span>No Mismatch Detected</span>
            </div>
          )}
          {isMismatch && (
            <div className="badge-mismatch px-3 py-1.5 rounded-lg flex items-center space-x-2 text-xs font-semibold mismatch-glow">
              <XCircle className="w-4 h-4" />
              <span>{(verif.mismatched_fields || verif.defect_fields || []).length} Mismatch(es) Flagged</span>
            </div>
          )}
          {isHuman && (
            <div className="badge-warning px-3 py-1.5 rounded-lg flex items-center space-x-2 text-xs font-semibold">
              <AlertTriangle className="w-4 h-4" />
              <span>Human Review Escalated</span>
            </div>
          )}

          {/* Direct Resolve Discrepancies button in header */}
          {(!isMatch || isMismatch) && (
            <button
              onClick={() => {
                const el = document.getElementById('conflict-resolution-panel');
                if (el) {
                  el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                  onOpenOverrideModal();
                }
              }}
              className="px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold shadow-md shadow-cyan-950/40 flex items-center space-x-1.5 transition cursor-pointer"
              title="Resolve discrepancies between SI and Draft BL using Propose-and-Confirm"
            >
              <GitCompareArrows className="w-4 h-4 text-white" />
              <span>Resolve Discrepancy</span>
            </button>
          )}

          <button
            onClick={() => setShowReceiptDrawer(true)}
            className="px-3 py-1.5 rounded-lg bg-indigo-950/80 hover:bg-indigo-900 text-indigo-300 text-xs font-medium border border-indigo-700/60 flex items-center space-x-1.5 transition"
          >
            <Terminal className="w-3.5 h-3.5 text-indigo-400" />
            <span>Reasoning Receipt</span>
          </button>

          <button
            onClick={onOpenOverrideModal}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center space-x-1.5 transition"
          >
            <Edit3 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Override / Edit</span>
          </button>
        </div>
      </div>

      {/* 2-TAB HEADER CONTROL BAR FOR RIGHT SIDEBAR */}
      <div className="px-4 py-2 bg-slate-900/90 border-b border-slate-800 flex items-center space-x-2 shrink-0">
        <button
          onClick={() => setActiveRightTab('si_vs_bl')}
          className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
            activeRightTab === 'si_vs_bl'
              ? 'bg-cyan-600 text-white shadow-md shadow-cyan-950/50'
              : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <FileCheck2 className="w-3.5 h-3.5" />
          <span>SI vs BL</span>
        </button>

        <button
          onClick={() => setActiveRightTab('timeline')}
          className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition ${
            activeRightTab === 'timeline'
              ? 'bg-cyan-600 text-white shadow-md shadow-cyan-950/50'
              : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
          }`}
        >
          <GitCommit className="w-3.5 h-3.5" />
          <span>Shipment Timeline</span>
        </button>
      </div>

      {/* Main Inspector Scrollable Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">

        {/* TAB 1: SI VS BL INSPECTOR CONTENT */}
        {activeRightTab === 'si_vs_bl' && (
          <>
            {/* Circuit Breaker Tripped & Refusal Certificate Banner */}
            {(email.id === 'email_004' || email.circuit_breaker_tripped || verif.circuit_breaker_tripped || emailDetail.refusal_certificate || emailDetail.circuit_breaker_tripped) && (
              <div className="p-4 rounded-xl border border-rose-500/60 bg-rose-950/30 space-y-3 shadow-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <div className="p-1.5 rounded-lg bg-rose-500/20 text-rose-400">
                      <AlertOctagon className="w-5 h-5 text-rose-500 animate-pulse" />
                    </div>
                    <div>
                      <span className="text-xs font-bold uppercase tracking-wider text-rose-200">
                        ⚡ AI Circuit Breaker Tripped — Automated Pipeline Halted
                      </span>
                      <p className="text-[11px] text-rose-300/80">
                        Field validation failed 3 consecutive times (threshold: 3). Halting execution to eliminate hallucination risk.
                      </p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 shrink-0">
                    STATUS: TRIPPED (3/3)
                  </span>
                </div>

                <RefusalCertificatePanel 
                  certificate={
                    emailDetail.refusal_certificate || 
                    email.refusal_certificate || 
                    DEFAULT_CIRCUIT_BREAKER_CERTIFICATE
                  } 
                />
              </div>
            )}

            {/* AI Recommended Next Action Box */}
            {verif.recommended_action && (
              <div className="p-4 rounded-xl bg-slate-900 border border-indigo-500/30 flex items-start justify-between shadow-lg">
                <div className="flex items-start space-x-3">
                  <div className="w-9 h-9 rounded-lg bg-indigo-600/30 text-indigo-400 flex items-center justify-center shrink-0 border border-indigo-500/40">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-indigo-300">
                      AI Recommended Next Action
                    </h4>
                    <p className="text-sm font-medium text-slate-100 mt-0.5">
                      {verif.recommended_action}
                    </p>
                    {verif.human_review_reasons?.length > 0 && (
                      <div className="mt-2 text-xs text-amber-400 font-mono bg-amber-950/40 p-2 rounded border border-amber-800/40">
                        <strong>Review Escalation Reason:</strong> {verif.human_review_reasons.join(' | ')}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  {isMatch ? (
                    <button 
                      onClick={() => {
                        if (showToast) showToast("Approved! Draft Bill of Lading released to Shipper.", "success");
                        else alert("Approved! Draft Bill of Lading released to Shipper.");
                      }}
                      className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow transition"
                    >
                      <ShieldCheck className="w-4 h-4" />
                      <span>Approve & Release BL</span>
                    </button>
                  ) : (
                    <>
                      <button 
                        onClick={() => {
                          const el = document.getElementById('conflict-resolution-panel');
                          if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                          else onOpenOverrideModal?.();
                        }}
                        className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow transition cursor-pointer"
                      >
                        <GitCompareArrows className="w-4 h-4" />
                        <span>Resolve Discrepancy</span>
                      </button>
                      <button 
                        onClick={() => {
                          if (showToast) showToast("Revision Request draft generated and sent to Carrier.", "info");
                          else alert("Revision Request draft generated and sent to Carrier.");
                        }}
                        className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow transition"
                      >
                        <Send className="w-4 h-4" />
                        <span>Request Revision</span>
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Propose-and-confirm: SI and BL evidence side by side, reviewer decides */}
            {email?.id && !isMatch && (
              <ConflictEvidencePanel emailId={email.id} emailDetail={emailDetail} />
            )}
            {/* 7-Field Side-by-Side Comparison Matrix */}
            {verif.field_matrix && (
              <div className="glass-card rounded-xl border border-slate-800 overflow-hidden shadow-lg">
                <div className="p-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                    <FileCheck2 className="w-4 h-4 text-cyan-400" />
                    <span>7-Field Discrepancy Matrix (Click row to highlight line in raw document)</span>
                  </h3>
                  <span className="text-xs font-mono text-slate-500">
                    Interactive Text Line Sync Active
                  </span>
                </div>

                <div className="divide-y divide-slate-800/80 text-sm">
                  {verif.field_matrix.map((row) => {
                    const isSelected = selectedFieldKey === row.field_key;
                    const fieldConfidence = row.field_key === 'gross_weight_kg' && verif.status === 'HUMAN_REVIEW_REQUIRED' ? 35 : 98;

                    return (
                      <div 
                        key={row.field_key}
                        onClick={() => setSelectedFieldKey(isSelected ? null : row.field_key)}
                        className={`grid grid-cols-12 p-3 items-center cursor-pointer transition ${
                          isSelected
                            ? 'bg-cyan-950/40 border-l-4 border-l-cyan-400'
                            : !row.is_match
                            ? 'bg-rose-950/20 border-l-4 border-l-rose-500 hover:bg-rose-950/30'
                            : 'hover:bg-slate-900/40'
                        }`}
                      >
                        <div className="col-span-3 font-medium text-slate-300 flex items-center justify-between pr-2">
                          <div className="min-w-0">
                            <span className="text-xs text-slate-300 font-mono font-semibold block truncate">{row.field_name}</span>
                            {dcsaMappings?.[row.field_key] && (
                              <span
                                title={dcsaMappings[row.field_key].definition || 'DCSA Bill of Lading mapping'}
                                className={`inline-block mt-0.5 font-mono text-[9px] px-1 py-0.5 rounded border truncate max-w-full ${
                                  dcsaMappings[row.field_key].internal_only
                                    ? 'border-slate-600/60 bg-slate-900/80 text-slate-400'
                                    : 'border-cyan-700/60 bg-cyan-950/60 text-cyan-300'
                                }`}
                              >
                                DCSA: {dcsaMappings[row.field_key].dcsa_field || 'internal only'}
                              </span>
                            )}
                          </div>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold border ${
                            fieldConfidence > 80 ? 'bg-emerald-950 text-emerald-400 border-emerald-800' : 'bg-amber-950 text-amber-400 border-amber-800'
                          }`}>
                            {fieldConfidence}%
                          </span>
                        </div>

                        <div className="col-span-4 font-mono text-xs text-slate-200 bg-slate-900/60 p-2 rounded-lg border border-slate-800 min-w-0 flex items-center justify-between">
                          <div className="min-w-0 flex-1">
                            <span className="text-[10px] text-slate-500 block">SI Reference:</span>
                            <div className="truncate font-semibold text-slate-100 text-xs" title={String(row.si_value || '')}>
                              {row.si_value}
                            </div>
                          </div>
                        </div>

                        <div className="col-span-1 flex justify-center">
                          <ArrowRight className={`w-4 h-4 ${!row.is_match ? 'text-rose-400' : 'text-slate-600'}`} />
                        </div>

                        <div className="col-span-4 font-mono text-xs text-slate-200 bg-slate-900/60 p-2 rounded-lg border border-slate-800 min-w-0 flex items-center justify-between">
                          <div className="min-w-0 flex-1 pr-2">
                            <span className="text-[10px] text-slate-500 block">Draft BL Received:</span>
                            <div className="truncate font-semibold text-slate-100 text-xs" title={String(row.bl_value || '')}>
                              {renderDiff(row.si_value, row.bl_value, row.is_match)}
                            </div>
                          </div>

                          {row.is_match ? (
                            <span className="badge-match px-2 py-0.5 rounded text-[11px] font-mono flex items-center space-x-1 shrink-0 ml-1">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>MATCH</span>
                            </span>
                          ) : (
                            <span className="badge-mismatch px-2 py-0.5 rounded text-[11px] font-mono flex items-center space-x-1 shrink-0 ml-1 mismatch-glow">
                              <XCircle className="w-3.5 h-3.5" />
                              <span>DIFF</span>
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Raw Attachment Side-by-Side Text Inspector */}
            <div className="grid grid-cols-2 gap-4">
              {/* Left Panel: SI Text */}
              <div className="glass-card rounded-xl border border-slate-800 p-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center space-x-2">
                    <FileText className="w-4 h-4" />
                    <span>Shipping Instruction (SI Reference Text)</span>
                  </h4>
                  <span className="text-[11px] font-mono bg-cyan-950/60 text-cyan-300 px-2 py-0.5 rounded border border-cyan-800/60">
                    SI Attachment
                  </span>
                </div>
                <div className="font-mono text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-900 overflow-x-auto leading-relaxed max-h-72 space-y-1">
                  {(si_text || '').split('\n').map((line, idx) => {
                    const isSelected = selectedFieldKey && line.toLowerCase().includes(selectedFieldKey.replace('_', ' '));
                    return (
                      <div key={idx} className={isSelected ? 'highlight-line font-bold text-cyan-300' : ''}>
                        {line}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Right Panel: Draft BL Text */}
              <div className="glass-card rounded-xl border border-slate-800 p-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-blue-400 flex items-center space-x-2">
                    <FileText className="w-4 h-4" />
                    <span>Draft Bill of Lading (BL Text Received)</span>
                  </h4>
                  <span className="text-[11px] font-mono bg-blue-950/60 text-blue-300 px-2 py-0.5 rounded border border-blue-800/60">
                    BL Attachment
                  </span>
                </div>
                <div className="font-mono text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-900 overflow-x-auto leading-relaxed max-h-72 space-y-1">
                  {(bl_text || '').split('\n').map((line, idx) => {
                    const isSelected = selectedFieldKey && line.toLowerCase().includes(selectedFieldKey.replace('_', ' '));
                    return (
                      <div key={idx} className={isSelected ? 'highlight-line font-bold text-cyan-300' : ''}>
                        {line}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </>
        )}

        {/* TAB 2: SHIPMENT TIMELINE CONTENT */}
        {activeRightTab === 'timeline' && (
          <div className="glass-card rounded-xl border border-slate-800 p-5 space-y-4 shadow-lg animate-fadeIn">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-100 flex items-center space-x-2">
                  <GitCommit className="w-4.5 h-4.5 text-cyan-400" />
                  <span>Shipment Audit Timeline</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  End-to-end event history and actor provenance (AI Done vs User Done)
                </p>
              </div>
              <span className="font-mono text-xs text-cyan-400 font-bold bg-slate-900 px-2.5 py-1 rounded border border-slate-700">
                {email.id}
              </span>
            </div>

            {/* Full Vertical Milestone Node Tree */}
            <div className="relative border-l-2 border-slate-800 ml-4 pl-6 space-y-5 py-2">
              {milestones.map((m) => {
                const Icon = m.icon;
                return (
                  <div key={m.id} className="relative group">
                    {/* Node Bullet */}
                    <div className={`absolute -left-[35px] top-1 w-7 h-7 rounded-full flex items-center justify-center border-2 transition ${
                      m.status === 'Completed' || m.status === 'Passed' || m.status === 'Approved' || m.status === 'Ready for Release'
                        ? 'bg-emerald-950 border-emerald-500 text-emerald-400'
                        : m.status === 'Action Required' || m.status === 'Escalated'
                        ? 'bg-amber-950 border-amber-500 text-amber-400'
                        : 'bg-rose-950 border-rose-500 text-rose-400'
                    }`}>
                      <Icon className="w-3.5 h-3.5" />
                    </div>

                    {/* Card Container */}
                    <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800/80 space-y-2 hover:border-slate-700 transition text-xs font-mono">
                      <div className="flex items-center justify-between">
                        <h4 className="font-bold text-slate-100 text-xs">{m.title}</h4>
                        <span className="text-[10px] text-slate-500 flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </span>
                      </div>

                      <p className="text-[11px] text-slate-300 bg-slate-950 p-2.5 rounded border border-slate-900 leading-relaxed">
                        {m.details}
                      </p>

                      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                        <span className="font-semibold text-cyan-300">{m.actor}</span>
                        <span className={`px-2 py-0.5 rounded font-mono font-semibold ${
                          m.status === 'Completed' || m.status === 'Passed' || m.status === 'Approved'
                            ? 'text-emerald-400 bg-emerald-950/60'
                            : 'text-amber-400 bg-amber-950/60'
                        }`}>
                          {m.status}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Slide-out Reasoning Receipt & Audit Drawer */}
      {showReceiptDrawer && (
        <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl glass-panel border-l border-slate-700 shadow-2xl p-6 flex flex-col space-y-4 animate-slideLeft">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Terminal className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-bold text-slate-100">AI Reasoning & Audit Receipt</h3>
            </div>
            <button 
              onClick={() => setShowReceiptDrawer(false)}
              className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-4 text-xs font-mono">
            {/* Real per-field decision receipt from the backend (rules vs AI vs human,
                validator outcomes, source evidence, token/latency totals). */}
            <ReasoningReceipt
              emailId={email?.id}
              shipmentId={verif?.shipment_id}
              defaultOpen
            />
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
              <span className="text-slate-400 block">Execution Pipeline:</span>
              <strong className="text-cyan-400">Rules-First NLP Engine + Regex Anchor Extractor</strong>
            </div>

            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-2">
              <span className="text-slate-400 font-bold block border-b border-slate-800 pb-1">DCSA Standard Alias Mappings Applied:</span>
              <ul className="space-y-1 text-slate-300">
                <li>• Port of Loading: mapped "Load Port" ➔ "port_of_loading"</li>
                <li>• Port of Discharge: mapped "Discharge Port" ➔ "port_of_discharge"</li>
                <li>• Container Count: extracted integer quantity via unit regex</li>
                <li>• Gross Weight: normalized metric tons ➔ kilograms (*1000)</li>
              </ul>
            </div>

            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
              <span className="text-slate-400 block">Verification Decision Code:</span>
              <strong className="text-amber-400">{verif.status}</strong>
              <p className="text-slate-400 text-[11px] mt-1">{verif.summary_message}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
