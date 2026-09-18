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
  FileText
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
  const isComparison = classification?.is_comparison_request;
  const verif = verification || {};

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950">
      {/* Inspector Top Header Bar */}
      <div className="p-4 border-b border-slate-800 glass-panel flex items-center justify-between">
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

        {/* Verification Overall Status Badge */}
        <div className="flex items-center space-x-3">
          {verif.status === 'NO_MISMATCH_DETECTED' && (
            <div className="badge-match px-3 py-1.5 rounded-lg flex items-center space-x-2 text-xs font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              <span>No Mismatch Detected</span>
            </div>
          )}
          {verif.status === 'MISMATCH_DETECTED' && (
            <div className="badge-mismatch px-3 py-1.5 rounded-lg flex items-center space-x-2 text-xs font-semibold mismatch-glow">
              <XCircle className="w-4 h-4" />
              <span>{verif.mismatched_fields.length} Mismatch(es) Flagged</span>
            </div>
          )}
          {verif.status === 'HUMAN_REVIEW_REQUIRED' && (
            <div className="badge-warning px-3 py-1.5 rounded-lg flex items-center space-x-2 text-xs font-semibold">
              <AlertTriangle className="w-4 h-4" />
              <span>Human Review Escalated</span>
            </div>
          )}

          <button
            onClick={onOpenOverrideModal}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center space-x-1.5 transition"
          >
            <Edit3 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Override / Edit Values</span>
          </button>
        </div>
      </div>

      {/* Main Split Inspector Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* AI Recommended Next Action Box */}
        {verif.recommended_action && (
          <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/30 flex items-start justify-between shadow-lg">
            <div className="flex items-start space-x-3">
              <div className="w-9 h-9 rounded-lg bg-indigo-600/30 text-indigo-400 flex items-center justify-center shrink-0 border border-indigo-500/40">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-indigo-300">
                  AI Recommended Action
                </h4>
                <p className="text-sm font-medium text-slate-100 mt-0.5">
                  {verif.recommended_action}
                </p>
                {verif.human_review_reasons?.length > 0 && (
                  <div className="mt-2 text-xs text-amber-400 font-mono bg-amber-950/40 p-2 rounded border border-amber-800/40">
                    <strong>Review Escalation Context:</strong> {verif.human_review_reasons.join(' | ')}
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-2 shrink-0">
              {verif.status === 'NO_MISMATCH_DETECTED' ? (
                <button 
                  onClick={() => {
                    if (onShowToast) onShowToast("✅ Approved! Draft Bill of Lading released to Shipper.", "success");
                  }}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow-lg shadow-emerald-950/40 transition active:scale-95"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>Approve & Release BL</span>
                </button>
              ) : (
                <button 
                  onClick={() => {
                    if (onShowToast) onShowToast("📩 Revision Request draft generated & sent to Carrier.", "warning");
                  }}
                  className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow-lg shadow-rose-950/40 transition active:scale-95"
                >
                  <Send className="w-4 h-4" />
                  <span>Request Revision</span>
                </button>
              )}
            </div>
          </div>
        )}

        {/* 7-Field Side-by-Side Comparison Matrix */}
        {verif.field_matrix && (
          <div className="glass-card rounded-xl border border-slate-800 overflow-hidden shadow-lg">
            <div className="p-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                <FileCheck2 className="w-4 h-4 text-cyan-400" />
                <span>7-Field Discrepancy Matrix (SI Reference vs Draft BL)</span>
              </h3>
              <span className="text-xs font-mono text-slate-500">
                SI Reference Standard = Baseline
              </span>
            </div>

            <div className="divide-y divide-slate-800/80 text-sm">
              {verif.field_matrix.map((row) => (
                <div 
                  key={row.field_key}
                  className={`grid grid-cols-12 p-3 items-center transition ${
                    !row.is_match ? 'bg-rose-950/20 border-l-4 border-l-rose-500' : 'hover:bg-slate-900/40'
                  }`}
                >
                  <div className="col-span-3 font-medium text-slate-300 flex items-center space-x-2">
                    <span className="text-xs text-slate-400 font-mono">{row.field_name}</span>
                  </div>

                  <div className="col-span-4 font-mono text-xs text-slate-200 bg-slate-900/60 p-2 rounded border border-slate-800 truncate">
                    <span className="text-[10px] text-slate-500 block">SI Reference:</span>
                    <strong className="text-slate-100">{row.si_value}</strong>
                  </div>

                  <div className="col-span-1 flex justify-center">
                    <ArrowRight className={`w-4 h-4 ${!row.is_match ? 'text-rose-400' : 'text-slate-600'}`} />
                  </div>

                  <div className="col-span-4 font-mono text-xs text-slate-200 bg-slate-900/60 p-2 rounded border border-slate-800 truncate flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-slate-500 block">Draft BL Received:</span>
                      <strong className={!row.is_match ? 'text-rose-400 font-bold' : 'text-slate-100'}>
                        {row.bl_value}
                      </strong>
                    </div>

                    {row.is_match ? (
                      <span className="badge-match px-2 py-0.5 rounded text-[11px] font-mono flex items-center space-x-1 shrink-0 ml-2">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>MATCH</span>
                      </span>
                    ) : (
                      <span className="badge-mismatch px-2 py-0.5 rounded text-[11px] font-mono flex items-center space-x-1 shrink-0 ml-2 mismatch-glow">
                        <XCircle className="w-3.5 h-3.5" />
                        <span>DIFF</span>
                      </span>
                    )}
                  </div>
                </div>
              ))}
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
            <pre className="font-mono text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-900 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-72">
              {si_text || 'No SI Attachment text available'}
            </pre>
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
            <pre className="font-mono text-xs text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-900 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-72">
              {bl_text || 'No Draft BL Attachment text available'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
