import React from 'react';
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
  ShieldAlert,
  FileText,
  Download,
  ExternalLink,
  Tag,
  Copy,
  Paperclip
} from 'lucide-react';

export default function SplitScreenInspector({ emailDetail, onOpenOverrideModal, onShowToast }) {
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

  const { email, classification, si_text, bl_text, verification, overrides } = emailDetail;
  const isComparison = classification?.is_comparison_request || classification?.category === 'BL_COMPARISON';
  const verif = verification || {};
  const status = verif.status || 'PROCESSED';
  const attachments = email?.attachments || [];

  const gateInfo = verif.pre_comparison_gate || {
    passed: verif.review_reason !== 'missing_attachment',
    si_attached: attachments.some((a) => {
      const p = typeof a === 'string' ? a : a.path || a.filename || '';
      return p.toLowerCase().includes('_si.') || a.doc_type === 'SI';
    }),
    bl_attached: attachments.some((a) => {
      const p = typeof a === 'string' ? a : a.path || a.filename || '';
      return p.toLowerCase().includes('_bl.') || a.doc_type === 'BL';
    }),
    attachment_count: attachments.length,
    comparison_possible: verif.review_reason !== 'missing_attachment',
    escalation_reason: verif.review_reason,
    recommended_action: verif.recommended_action || 'Request/re-send documents',
    operational_response_draft: verif.recommended_action,
    reference_no: email?.id
  };

  const isMissingAttachment = verif.review_reason === 'missing_attachment' || (!gateInfo.passed && isComparison);

  const siAtt = attachments.find((a) => {
    const p = typeof a === 'string' ? a : a.path || a.filename || '';
    return p.toLowerCase().includes('_si.') || a.doc_type === 'SI';
  });

  const blAtt = attachments.find((a) => {
    const p = typeof a === 'string' ? a : a.path || a.filename || '';
    return p.toLowerCase().includes('_bl.') || a.doc_type === 'BL';
  });

  const getAttPath = (att) => {
    if (!att) return '';
    return typeof att === 'string' ? att : att.path || att.filename || '';
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950">
      {/* Inspector Top Header Bar */}
      <div className="p-4 border-b border-slate-800 glass-panel flex items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="font-mono text-xs text-cyan-400 font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/60">
              {email.id}
            </span>
            <span className="font-mono text-xs bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded border border-indigo-700">
              {classification?.category || 'BL_COMPARISON'}
            </span>
            <h2 className="text-base font-bold text-slate-100 truncate max-w-xl">{email.subject}</h2>
          </div>
          <div className="flex items-center space-x-3 text-xs text-slate-400 font-mono">
            <span>From: <strong className="text-slate-300">{email.sender}</strong></span>
            <span>•</span>
            <span>Vessel: <strong className="text-cyan-400">{email.vessel || 'Commercial Carrier'}</strong> {email.voyage}</span>
            <span>•</span>
            <span>Company: <strong className="text-slate-300">{email.company || 'Maritime Shipper'}</strong></span>
          </div>
        </div>

        {/* Verification Overall Status Badge */}
        <div className="flex items-center space-x-3 shrink-0">
          {status === 'OK' && (
            <div className="badge-match px-3.5 py-1.5 rounded-lg flex items-center space-x-2 text-xs font-semibold shadow-sm">
              <CheckCircle2 className="w-4 h-4" />
              <span>OK — All 7 Fields Matched</span>
            </div>
          )}
          {status === 'MISMATCH' && (
            <div className="badge-mismatch px-3.5 py-1.5 rounded-lg flex items-center space-x-2 text-xs font-semibold mismatch-glow shadow-sm">
              <XCircle className="w-4 h-4" />
              <span>MISMATCH ({verif.defect_fields?.length || 0} Defect{verif.defect_fields?.length === 1 ? '' : 's'})</span>
            </div>
          )}
          {status === 'NEEDS_REVIEW' && (
            <div className={`px-3.5 py-1.5 rounded-lg flex items-center space-x-2 text-xs font-semibold shadow-sm ${
              verif.review_reason === 'scanned_not_processed'
                ? 'bg-purple-950/80 text-purple-300 border border-purple-600'
                : verif.review_reason === 'corrupted_file'
                ? 'bg-rose-950/80 text-rose-300 border border-rose-600'
                : verif.review_reason === 'term_unresolved'
                ? 'bg-indigo-950/80 text-indigo-300 border border-indigo-600'
                : 'badge-warning'
            }`}>
              <AlertTriangle className="w-4 h-4" />
              <span>
                {verif.review_reason === 'scanned_not_processed' && 'NEEDS REVIEW: Scanned PDF (No OCR)'}
                {verif.review_reason === 'corrupted_file' && 'NEEDS REVIEW: Corrupted File'}
                {verif.review_reason === 'term_unresolved' && 'NEEDS REVIEW: Unresolved Term'}
                {!['scanned_not_processed', 'corrupted_file', 'term_unresolved'].includes(verif.review_reason) && `NEEDS REVIEW: ${verif.review_reason}`}
              </span>
            </div>
          )}

          <button
            onClick={onOpenOverrideModal}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center space-x-1.5 transition active:scale-95"
          >
            <Edit3 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Human Override</span>
          </button>
        </div>
      </div>

      {/* Main Split Inspector Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Defect Chips Summary (If MISMATCH) */}
        {verif.defect_fields && verif.defect_fields.length > 0 && (
          <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-500/40 flex items-center justify-between">
            <div className="flex items-center space-x-2 flex-wrap">
              <span className="text-xs font-bold text-rose-300 uppercase tracking-wider flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Mismatched Fields:</span>
              </span>
              {verif.defect_fields.map((field) => (
                <span key={field} className="px-2 py-0.5 rounded-md bg-rose-900/60 text-rose-200 font-mono text-xs font-bold border border-rose-700">
                  {field}
                </span>
              ))}
            </div>
            <span className="text-xs font-mono text-rose-400">
              Discrepancy detected vs SI baseline
            </span>
          </div>
        )}

        {/* Pre-Comparison Attachment Gate Card (When missing_attachment) */}
        {isMissingAttachment && (
          <div className="glass-card rounded-2xl border-2 border-amber-500/50 p-5 bg-gradient-to-b from-amber-950/40 via-slate-900/90 to-slate-950 shadow-2xl shadow-amber-950/40 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-amber-500/30">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/40 shadow-inner">
                  <ShieldAlert className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-amber-300">
                      BL Comparison Request — Pre-Comparison Attachment Gate
                    </h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-900/80 text-amber-200 border border-amber-600">
                      GATE HALTED
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mt-0.5">
                    <strong className="text-amber-300">Defensive AI Safety Protocol:</strong> Required documents validated before comparison. Verification halted to prevent ungrounded decisions on missing files.
                  </p>
                </div>
              </div>
              <span className="text-xs font-mono bg-slate-900 text-amber-400 px-3 py-1 rounded-lg border border-amber-500/40 font-semibold">
                Attachments: {gateInfo.attachment_count ?? (email.attachments?.length || 0)} received
              </span>
            </div>

            {/* Gate Verification Table */}
            <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-950/80">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-900/90 text-slate-400 font-mono text-[11px] uppercase border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-4">Validation Check</th>
                    <th className="py-2.5 px-4">Gate Result</th>
                    <th className="py-2.5 px-4">Audit Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/70 font-mono">
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-4 font-sans font-medium text-slate-200">Email Classification</td>
                    <td className="py-2.5 px-4">
                      <span className="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700 font-bold">
                        BL_COMPARISON
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-400 font-sans">Draft BL comparison request identified from email context</td>
                  </tr>

                  <tr className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-4 font-sans font-medium text-slate-200">SI Attached</td>
                    <td className="py-2.5 px-4">
                      {gateInfo.si_attached ? (
                        <span className="badge-match px-2 py-0.5 rounded text-[11px] flex items-center space-x-1 w-fit">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>✅ Received</span>
                        </span>
                      ) : (
                        <span className="badge-mismatch px-2 py-0.5 rounded text-[11px] flex items-center space-x-1 w-fit font-bold">
                          <XCircle className="w-3.5 h-3.5" />
                          <span>❌ Missing</span>
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-slate-400 font-sans">Customer Shipping Instruction document</td>
                  </tr>

                  <tr className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-4 font-sans font-medium text-slate-200">Draft BL Attached</td>
                    <td className="py-2.5 px-4">
                      {gateInfo.bl_attached ? (
                        <span className="badge-match px-2 py-0.5 rounded text-[11px] flex items-center space-x-1 w-fit">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>✅ Received</span>
                        </span>
                      ) : (
                        <span className="badge-mismatch px-2 py-0.5 rounded text-[11px] flex items-center space-x-1 w-fit font-bold">
                          <XCircle className="w-3.5 h-3.5" />
                          <span>❌ Missing</span>
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-slate-400 font-sans">Carrier Draft Bill of Lading document</td>
                  </tr>

                  <tr className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-4 font-sans font-medium text-slate-200">Comparison Possible</td>
                    <td className="py-2.5 px-4">
                      <span className="bg-rose-950/80 text-rose-300 px-2 py-0.5 rounded border border-rose-700 font-bold flex items-center space-x-1 w-fit">
                        <XCircle className="w-3.5 h-3.5" />
                        <span>❌ No (Halted before comparison)</span>
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-rose-300 font-sans font-medium">Comparison matrix halted; will not guess on missing input</td>
                  </tr>

                  <tr className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-4 font-sans font-medium text-slate-200">Escalation Reason</td>
                    <td className="py-2.5 px-4">
                      <span className="bg-amber-950/80 text-amber-300 px-2 py-0.5 rounded border border-amber-600 font-bold">
                        MISSING_ATTACHMENT
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-400 font-sans">Reliability escalation protocol triggered</td>
                  </tr>

                  <tr className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-4 font-sans font-medium text-slate-200">Recommended Action</td>
                    <td className="py-2.5 px-4 text-cyan-300 font-sans font-semibold">
                      Request/re-send documents
                    </td>
                    <td className="py-2.5 px-4 text-slate-400 font-sans">Automated operational response generated below</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Ready-to-send Operational Response Box */}
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-700/80 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Automated Operational Dispatch Draft
                  </span>
                </div>
                <span className="text-[11px] font-mono text-cyan-400">Target: {email.sender}</span>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-amber-200/95 leading-relaxed select-all">
                "{gateInfo.operational_response_draft || verif.recommended_action || `Action required: Please resend the SI and draft BL for ${email.id}. The attachments were not received with the email.`}"
              </div>

              <div className="flex items-center justify-end space-x-3 pt-1">
                <button
                  onClick={() => {
                    const text = gateInfo.operational_response_draft || verif.recommended_action;
                    if (navigator.clipboard) {
                      navigator.clipboard.writeText(text);
                    }
                    if (onShowToast) onShowToast("📋 Copied operational response to clipboard!", "info");
                  }}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center space-x-1.5 transition active:scale-95"
                >
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  <span>Copy Response</span>
                </button>

                <button
                  onClick={() => {
                    if (onShowToast) onShowToast(`📩 Re-request email dispatched to ${email.sender}!`, "success");
                  }}
                  className="px-3.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow-lg shadow-amber-950/40 transition active:scale-95"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Dispatch Re-Request to Sender</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Needs Review Reason Box (For other NEEDS_REVIEW reasons) */}
        {status === 'NEEDS_REVIEW' && !isMissingAttachment && (
          <div className={`p-4 rounded-xl flex items-start justify-between shadow-lg ${
            verif.review_reason === 'scanned_not_processed'
              ? 'bg-purple-950/30 border border-purple-500/40'
              : verif.review_reason === 'corrupted_file'
              ? 'bg-rose-950/30 border border-rose-500/40'
              : verif.review_reason === 'term_unresolved'
              ? 'bg-indigo-950/30 border border-indigo-500/40'
              : 'bg-amber-950/30 border border-amber-500/40'
          }`}>
            <div className="flex items-start space-x-3">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${
                verif.review_reason === 'scanned_not_processed'
                  ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                  : verif.review_reason === 'corrupted_file'
                  ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                  : verif.review_reason === 'term_unresolved'
                  ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
                  : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
              }`}>
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <h4 className={`text-xs font-bold uppercase tracking-wider ${
                  verif.review_reason === 'scanned_not_processed'
                    ? 'text-purple-300'
                    : verif.review_reason === 'corrupted_file'
                    ? 'text-rose-300'
                    : verif.review_reason === 'term_unresolved'
                    ? 'text-indigo-300'
                    : 'text-amber-300'
                }`}>
                  Human Escalation Required — Trigger: {verif.review_reason}
                </h4>
                <p className="text-xs font-medium text-slate-200 mt-1">
                  {verif.summary_message || 'Document requires human review before release.'}
                </p>
                <p className={`text-xs font-mono mt-1 ${
                  verif.review_reason === 'scanned_not_processed'
                    ? 'text-purple-400'
                    : verif.review_reason === 'corrupted_file'
                    ? 'text-rose-400'
                    : verif.review_reason === 'term_unresolved'
                    ? 'text-indigo-400'
                    : 'text-amber-400'
                }`}>
                  Recommended Action: {verif.recommended_action}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* AI Action Header */}
        {verif.recommended_action && status !== 'NEEDS_REVIEW' && (
          <div className="p-3.5 rounded-xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/30 flex items-center justify-between shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-600/30 text-indigo-400 flex items-center justify-center shrink-0 border border-indigo-500/40">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-indigo-300">
                  Operations Next Step
                </h4>
                <p className="text-xs font-medium text-slate-100 mt-0.5">
                  {verif.recommended_action}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2 shrink-0">
              {status === 'OK' ? (
                <button 
                  onClick={() => {
                    if (onShowToast) onShowToast("✅ Approved! Draft Bill of Lading released to Shipper.", "success");
                  }}
                  className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow-lg shadow-emerald-950/40 transition active:scale-95"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>Approve & Release BL</span>
                </button>
              ) : (
                <button 
                  onClick={() => {
                    if (onShowToast) onShowToast("📩 Revision Request draft generated & sent to Carrier.", "warning");
                  }}
                  className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow-lg shadow-rose-950/40 transition active:scale-95"
                >
                  <Send className="w-4 h-4" />
                  <span>Request Carrier Revision</span>
                </button>
              )}
            </div>
          </div>
        )}

        {/* 7-Field Side-by-Side Comparison Matrix */}
        {verif.field_matrix && (
          <div className="glass-card rounded-xl border border-slate-800 overflow-hidden shadow-lg">
            <div className="p-3 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2">
                <FileCheck2 className="w-4 h-4 text-cyan-400" />
                <span>
                  {isMissingAttachment 
                    ? "7-Field Comparison Matrix — Halted (Pre-Comparison Gate)" 
                    : "7-Field Comparison Matrix (SI Reference vs Draft BL)"}
                </span>
              </h3>
              <span className="text-xs font-mono text-slate-400">
                {isMissingAttachment ? "Comparison Halted • Safety Guard" : "SI Reference Standard = Baseline"}
              </span>
            </div>

            <div className="divide-y divide-slate-800/80 text-xs">
              {verif.field_matrix.map((row) => (
                <div 
                  key={row.field_key}
                  className={`grid grid-cols-12 p-3 items-center transition ${
                    !row.is_match && status === 'MISMATCH' 
                      ? 'bg-rose-950/20 border-l-4 border-l-rose-500' 
                      : !row.is_match && status === 'NEEDS_REVIEW'
                      ? 'bg-amber-950/15 border-l-4 border-l-amber-500'
                      : 'hover:bg-slate-900/40'
                  }`}
                >
                  <div className="col-span-3 font-semibold text-slate-300 flex items-center space-x-2">
                    <span className="text-xs text-slate-300">{row.field_name}</span>
                  </div>

                  <div className="col-span-4 font-mono text-xs text-slate-200 bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 truncate">
                    <span className="text-[10px] text-slate-500 block uppercase font-sans font-bold">SI Reference Value</span>
                    <strong className="text-slate-100">{row.si_value}</strong>
                  </div>

                  <div className="col-span-1 flex justify-center">
                    <ArrowRight className={`w-4 h-4 ${!row.is_match ? 'text-rose-400' : 'text-slate-600'}`} />
                  </div>

                  <div className="col-span-4 font-mono text-xs text-slate-200 bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 truncate flex items-center justify-between">
                    <div className="truncate mr-2">
                      <span className="text-[10px] text-slate-500 block uppercase font-sans font-bold">Draft BL Value</span>
                      <strong className={!row.is_match && status === 'MISMATCH' ? 'text-rose-400 font-bold' : 'text-slate-100'}>
                        {row.bl_value}
                      </strong>
                    </div>

                    {row.is_match ? (
                      <span className="badge-match px-2 py-0.5 rounded text-[11px] font-mono flex items-center space-x-1 shrink-0">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>MATCH</span>
                      </span>
                    ) : status === 'NEEDS_REVIEW' ? (
                      <span className="badge-warning px-2 py-0.5 rounded text-[11px] font-mono flex items-center space-x-1 shrink-0">
                        <HelpCircle className="w-3 h-3" />
                        <span>REVIEW</span>
                      </span>
                    ) : (
                      <span className="badge-mismatch px-2 py-0.5 rounded text-[11px] font-mono flex items-center space-x-1 shrink-0 mismatch-glow">
                        <XCircle className="w-3 h-3" />
                        <span>DIFF</span>
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Multi-Format Document Inspector Panels */}
        <div className="grid grid-cols-2 gap-4">
          {/* Left Panel: Shipping Instruction (SI) */}
          <div className="glass-card rounded-xl border border-slate-800 p-4 flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-cyan-400" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                  Shipping Instruction (SI Attachment)
                </h4>
              </div>
              <div className="flex items-center space-x-2">
                {siAtt && (
                  <a
                    href={`/api/attachments/${getAttPath(siAtt)}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] font-mono bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded border border-slate-700 flex items-center space-x-1 transition"
                  >
                    <Download className="w-3 h-3" />
                    <span>Download Original</span>
                  </a>
                )}
                <span className="text-[11px] font-mono bg-cyan-950/80 text-cyan-300 px-2 py-0.5 rounded border border-cyan-800/60 font-semibold">
                  SI Baseline
                </span>
              </div>
            </div>
            <pre className="font-mono text-xs text-slate-300 bg-slate-950 p-3.5 rounded-lg border border-slate-900 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-80 flex-1">
              {si_text || 'No SI Attachment text available'}
            </pre>
          </div>

          {/* Right Panel: Draft Bill of Lading (BL) */}
          <div className="glass-card rounded-xl border border-slate-800 p-4 flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-blue-400" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-blue-400">
                  Draft Bill of Lading (BL Attachment)
                </h4>
              </div>
              <div className="flex items-center space-x-2">
                {blAtt && (
                  <a
                    href={`/api/attachments/${getAttPath(blAtt)}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] font-mono bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded border border-slate-700 flex items-center space-x-1 transition"
                  >
                    <Download className="w-3 h-3" />
                    <span>Download Original</span>
                  </a>
                )}
                <span className="text-[11px] font-mono bg-blue-950/80 text-blue-300 px-2 py-0.5 rounded border border-blue-800/60 font-semibold">
                  Draft BL
                </span>
              </div>
            </div>
            <pre className="font-mono text-xs text-slate-300 bg-slate-950 p-3.5 rounded-lg border border-slate-900 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-80 flex-1">
              {bl_text || 'No Draft BL Attachment text available'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
