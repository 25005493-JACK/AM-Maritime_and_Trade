import React, { useState } from 'react';
import { 
  AlertTriangle, 
  CheckCircle2, 
  ChevronDown, 
  ChevronUp, 
  FileText, 
  ShieldCheck, 
  UserCheck, 
  AlertOctagon, 
  Terminal,
  Paperclip,
  HelpCircle,
  Sparkles
} from 'lucide-react';
import { ReflectionsPanel } from './AgentLearningDashboard.jsx';

export default function HumanReviewQueue({ 
  emails, 
  onReviewEmail, 
  onApproveEmail,
  reflectionsData, 
  onRefreshReflections 
}) {
  const [expandedId, setExpandedId] = useState(null);

  // Filter emails requiring human review (exclude already approved items)
  const reviewEmails = emails.filter((e) => {
    const status = e.verification?.status;
    if (status === 'OK' || status === 'Approved' || status === 'Passed' || status === 'Completed') {
      return false;
    }
    const hasReason = e.verification?.review_reason || (e.verification?.human_review_reasons && e.verification.human_review_reasons.length > 0);
    return status === 'HUMAN_REVIEW_REQUIRED' || status === 'NEEDS_REVIEW' || hasReason;
  });

  const getReasonExplanation = (reason) => {
    switch (reason) {
      case 'missing_attachment':
        return 'Both Shipping Instruction (SI) and draft Bill of Lading (BL) are required for automated comparison. One or both attachments were missing from the incoming email stream.';
      case 'missing_value':
        return 'Critical mandatory shipping fields (e.g., Port of Loading, Port of Discharge, Container Count) could not be extracted from the provided documents with sufficient confidence.';
      case 'unreadable':
        return 'The attached PDF document contained corrupted text streams or low-resolution image scans that failed standard OCR parsing thresholds.';
      case 'wrong_doc_type':
        return 'The document attached does not match expected Maritime SI or BL formats (e.g., received a booking confirmation or invoice instead of a Bill of Lading).';
      case 'scanned_not_processed':
        return 'Document requires advanced optical character recognition (OCR) and human validation due to non-standard layout formatting.';
      case 'term_unresolved':
        return 'Commercial trade terms (Incoterrms or vessel ports) could not be resolved against official UN/LOCODE registries.';
      default:
        return 'This document was flagged by the verification engine safety rules to eliminate hallucination risk and ensure 100% data fidelity before carrier release.';
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* HEADER BAR */}
      <div className="p-4 border-b border-blue-900/60 bg-slate-950 flex items-center justify-between shrink-0 shadow-md">
        <div>
          <h2 className="text-base font-extrabold text-slate-100 flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <span>Human-in-the-Loop Review Queue</span>
            <span className="h-6 inline-flex items-center px-2.5 text-xs bg-amber-950/80 text-amber-300 font-mono font-semibold rounded-md border border-amber-800">
              {reviewEmails.length} Items Requiring Human Review
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Inspecting escalated messages. Review SI & BL evidence, inspect triggered error logic, and approve to advance to next step.
          </p>
        </div>
      </div>

      {/* MAIN CARDS LIST */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {reviewEmails.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <CheckCircle2 className="w-16 h-16 stroke-[1.2] mb-3 text-emerald-400" />
            <h3 className="text-base font-bold text-slate-200">Review Queue Clear!</h3>
            <p className="text-xs text-slate-400 max-w-sm text-center mt-1">
              All incoming shipping documents have been automatically processed or verified.
            </p>
          </div>
        ) : (
          reviewEmails.map((email) => {
            const isExpanded = expandedId === email.id;
            const verif = email.verification || {};
            const reasons = verif.human_review_reasons || (verif.review_reason ? [verif.review_reason] : ['Safety Guardrail Flagged']);
            const primaryReason = verif.review_reason || (reasons.length > 0 ? reasons[0] : 'missing_value');

            return (
              <div 
                key={email.id} 
                className="rounded-2xl border border-amber-500/40 bg-slate-900/90 shadow-xl overflow-hidden transition-all duration-200"
              >
                {/* CARD HEADER (Click to Expand / Collapse) */}
                <div 
                  onClick={() => setExpandedId(isExpanded ? null : email.id)}
                  className="p-4 bg-slate-900 flex items-center justify-between cursor-pointer hover:bg-slate-800 transition"
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/40 flex items-center justify-center shrink-0">
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="h-6 inline-flex items-center px-2.5 text-xs bg-amber-950/40 text-amber-400 font-mono font-semibold rounded-md border border-amber-500/40 shrink-0">{email.id}</span>
                        <span className="text-xs font-bold text-slate-200 truncate">{email.sender}</span>
                        {email.company && (
                          <span className="h-6 inline-flex items-center px-2.5 text-xs bg-slate-800 text-slate-300 font-mono font-semibold rounded-md border border-slate-700 shrink-0">
                            {email.company}
                          </span>
                        )}
                      </div>
                      <h3 className="text-sm font-semibold text-slate-100 mt-0.5 truncate">{email.subject}</h3>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 shrink-0">
                    <span className="w-56 h-7 inline-flex items-center justify-center space-x-1 px-3 text-xs bg-amber-950 text-amber-300 font-mono font-semibold rounded-md border border-amber-800 shrink-0 truncate">
                      <HelpCircle className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">Reason: {primaryReason}</span>
                    </span>

                    <button className="p-1 rounded-lg bg-slate-800 text-slate-300 hover:text-white">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* EXPANDED CONTENT AREA */}
                {isExpanded && (
                  <div className="p-5 border-t border-amber-500/30 bg-slate-950 space-y-4 animate-fadeIn">
                    {/* EXPLANATION & LOGIC BOX */}
                    <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/30 space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-amber-300 flex items-center space-x-2">
                        <Sparkles className="w-4 h-4" />
                        <span>System Error Logic & Escalation Rationale</span>
                      </h4>
                      <p className="text-xs font-mono text-slate-200 leading-relaxed">
                        {getReasonExplanation(primaryReason)}
                      </p>
                      <div className="text-[11px] font-mono text-amber-400 pt-1 flex items-center space-x-2">
                        <strong>Triggered Reason Code:</strong> <code className="h-6 inline-flex items-center px-2.5 text-xs bg-slate-900 text-amber-300 font-mono font-semibold rounded-md border border-amber-900">{primaryReason}</code>
                      </div>
                    </div>

                    {/* SI & BL INFORMATION PREVIEW */}
                    <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                      {/* SI Information */}
                      <div className="p-3 rounded-xl bg-slate-900 border border-blue-900/60 space-y-2">
                        <span className="text-cyan-400 font-bold block border-b border-slate-800 pb-1 flex items-center justify-between">
                          <span>Shipping Instruction (SI Reference)</span>
                          <Paperclip className="w-3.5 h-3.5" />
                        </span>
                        <div className="text-slate-300 space-y-1">
                          <div>• Sender: {email.sender}</div>
                          <div>• Vessel/Voyage: {email.vessel || 'Commercial Carrier'} {email.voyage}</div>
                          <div>• Attachments: {email.attachments?.length || 1} file(s)</div>
                          <div>• Booking Ref: {email.subject?.split(' ')[1] || email.id}</div>
                        </div>
                      </div>

                      {/* BL Information */}
                      <div className="p-3 rounded-xl bg-slate-900 border border-blue-900/60 space-y-2">
                        <span className="text-indigo-400 font-bold block border-b border-slate-800 pb-1 flex items-center justify-between">
                          <span>Draft Bill of Lading (BL Data)</span>
                          <FileText className="w-3.5 h-3.5" />
                        </span>
                        <div className="text-slate-300 space-y-1">
                          <div>• Status: {verif.status || 'NEEDS_REVIEW'}</div>
                          <div>• Defect Fields: {(verif.defect_fields || []).join(', ') || 'None (Escalated Safety Guardrail)'}</div>
                          <div>• Summary: {verif.summary_message || 'Verification halted for human sign-off.'}</div>
                        </div>
                      </div>
                    </div>

                    {/* ACTION BUTTONS: INSPECT / OVERRIDE & APPROVE & ADVANCE TO NEXT STEP */}
                    <div className="flex items-center justify-between pt-3 border-t border-slate-800">
                      <span className="text-xs text-slate-400 font-mono">
                        Reviewer action will advance document status to OK and release for dispatch.
                      </span>

                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onReviewEmail(email.id);
                          }}
                          className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs flex items-center space-x-1.5 border border-slate-700 transition active:scale-95"
                        >
                          <FileText className="w-4 h-4 text-cyan-400" />
                          <span>Inspect & Override</span>
                        </button>

                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onApproveEmail) {
                              onApproveEmail(email.id);
                            } else {
                              onReviewEmail(email.id);
                            }
                          }}
                          className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold text-xs flex items-center space-x-2 shadow-lg shadow-emerald-950/60 transition active:scale-95"
                        >
                          <UserCheck className="w-4 h-4" />
                          <span>Approve & Advance to Next Step</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Embedded Reflexion Panel */}
        <div className="mt-8">
          <ReflectionsPanel
            reflectionsBySender={reflectionsData?.by_sender}
            onRefresh={onRefreshReflections}
          />
        </div>
      </div>
    </div>
  );
}
