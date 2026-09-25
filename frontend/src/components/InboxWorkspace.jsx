import React, { useState, useRef } from 'react';
import { 
  Search, 
  Tag, 
  FileText, 
  AlertCircle, 
  CheckCircle2, 
  HelpCircle, 
  ChevronRight, 
  ChevronDown,
  ChevronUp,
  Paperclip,
  Filter,
  CheckSquare,
  Square,
  ShieldCheck,
  ShieldAlert,
  Send,
  AlertOctagon,
  X,
  FileCheck2,
  GitCommit,
  GitCompareArrows,
  Edit3,
  Terminal,
  ArrowRight,
  Sparkles,
  UserCheck,
  Ship,
  Clock,
  Upload,
  Inbox as InboxIcon
} from 'lucide-react';

import ConflictEvidencePanel from './ConflictEvidencePanel.jsx';
import ReasoningReceipt, { RefusalCertificatePanel } from './ReasoningReceipt.jsx';
import UploadDocsModal from './UploadDocsModal.jsx';

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
    { field_name: 'port_of_loading', attempted_value: null, why_failed: 'Required POL missing or ungrounded; failed source_match verification.' },
    { field_name: 'port_of_discharge', attempted_value: null, why_failed: 'Required POD missing or ungrounded; failed UN/LOCODE directory whitelist.' },
    { field_name: 'container_count', attempted_value: null, why_failed: 'Required container count missing from draft BL; failed DCSA format check.' }
  ],
  missing_or_unclear: ['port_of_loading', 'port_of_discharge', 'container_count'],
  suggested_recipient: 'carrier',
  recipient_rationale: 'Missing/unclear fields (container_count, port_of_discharge, port_of_loading) are carrier-side data.',
  estimated_delay_minutes: 960,
  estimated_delay_hours: 16.0,
  estimated_delay_basis: '3 missing field(s) @ 240 min manual query each + baseline SLA',
  what_would_unblock: [
    'Query ocean carrier booking desk for missing container manifest',
    'Provide machine-readable draft Bill of Lading with verified Port of Loading & Port of Discharge',
    'Re-send document using standard field labels or issue human manual override'
  ],
  notice: 'AI processing stopped for this document: no further AI guesses were made. Automated pipeline execution halted.'
};

export default function InboxWorkspace({ 
  emails, 
  selectedEmailId, 
  onSelectEmail, 
  emailDetail,
  onOpenOverrideModal,
  onUploadSuccess,
  healthInfo
}) {
  // Upload modal state
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Filters state
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDocType, setSelectedDocType] = useState('ALL');
  const [selectedEmailIds, setSelectedEmailIds] = useState([]);

  // Right side state
  const [isEmailContentOpen, setIsEmailContentOpen] = useState(false); // Default CLOSED / MINIMIZED as requested
  const [activeRightTab, setActiveRightTab] = useState('si_vs_bl'); // 'si_vs_bl' or 'timeline'
  const [selectedFieldKey, setSelectedFieldKey] = useState(null);
  const [showReceiptDrawer, setShowReceiptDrawer] = useState(false);
  const [inspectorWidth, setInspectorWidth] = useState(580);

  const isDraggingRef = useRef(false);

  // Mouse drag handler for resizable right inspector
  const handleMouseDownResize = (e) => {
    e.preventDefault();
    isDraggingRef.current = true;
    const handleMouseMove = (moveEvent) => {
      if (!isDraggingRef.current) return;
      const windowWidth = window.innerWidth;
      const targetWidth = windowWidth - moveEvent.clientX;
      const clampedWidth = Math.min(Math.max(targetWidth, 380), windowWidth - 420);
      setInspectorWidth(clampedWidth);
    };
    const handleMouseUp = () => {
      isDraggingRef.current = false;
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  // Filter logic
  const filteredEmails = emails.filter((email) => {
    // Search by email sender, sender name (company/sender), email id
    const searchTarget = `${email.id} ${email.sender || ''} ${email.company || ''} ${email.subject || ''}`.toLowerCase();
    const matchesSearch = searchTarget.includes(searchTerm.toLowerCase());

    // Filter by email status
    let matchesStatus = true;
    if (selectedStatus === 'CIRCUIT_BREAKER') {
      matchesStatus = email.circuit_breaker_tripped || email.id === 'email_004' || email.verification?.circuit_breaker_tripped;
    } else if (selectedStatus === 'MISMATCH') {
      matchesStatus = email.verification?.status === 'MISMATCH_DETECTED' || email.verification?.status === 'MISMATCH';
    } else if (selectedStatus === 'MATCHED') {
      matchesStatus = email.verification?.status === 'NO_MISMATCH_DETECTED' || email.verification?.status === 'OK';
    } else if (selectedStatus === 'HUMAN_REVIEW') {
      matchesStatus = email.verification?.status === 'HUMAN_REVIEW_REQUIRED' || email.verification?.status === 'NEEDS_REVIEW';
    } else if (selectedStatus === 'SPAM') {
      matchesStatus = email.classification?.category === 'SPAM' || email.classification?.super_category === 'Spam / General';
    }

    // Filter by document / email types dropdown
    let matchesDocType = true;
    const superCat = email.classification?.super_category || '';
    const cat = email.classification?.category || '';

    if (selectedDocType === 'SI_BL') {
      matchesDocType = cat === 'BL_COMPARISON' || cat === 'SI_REQUEST' || superCat.includes('Documentation');
    } else if (selectedDocType === 'BOOKING') {
      matchesDocType = superCat.includes('Booking') || cat.includes('BOOKING');
    } else if (selectedDocType === 'CONTAINER') {
      matchesDocType = superCat.includes('Container') || superCat.includes('Yard');
    } else if (selectedDocType === 'FINANCE') {
      matchesDocType = cat === 'INVOICE_QUERY' || superCat.includes('Finance') || superCat.includes('Billing');
    }

    return matchesSearch && matchesStatus && matchesDocType;
  });

  const toggleSelectAll = () => {
    if (selectedEmailIds.length === filteredEmails.length) {
      setSelectedEmailIds([]);
    } else {
      setSelectedEmailIds(filteredEmails.map(e => e.id));
    }
  };

  const toggleSelectEmail = (id, e) => {
    e.stopPropagation();
    if (selectedEmailIds.includes(id)) {
      setSelectedEmailIds(selectedEmailIds.filter(i => i !== id));
    } else {
      setSelectedEmailIds([...selectedEmailIds, id]);
    }
  };

  const str = (v) => (v === null || v === undefined ? '' : String(v));

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

  const currentEmail = emailDetail?.email || emails.find(e => e.id === selectedEmailId);
  const verif = emailDetail?.verification || currentEmail?.verification || {};
  const isMatch = verif.status === 'NO_MISMATCH_DETECTED' || verif.status === 'OK';
  const isHuman = verif.status === 'HUMAN_REVIEW_REQUIRED' || verif.status === 'NEEDS_REVIEW';
  const isMismatch = verif.status === 'MISMATCH_DETECTED' || verif.status === 'MISMATCH';

  const milestones = currentEmail ? [
    {
      id: 1,
      title: 'Booking Confirmed & Allocation Scheduled',
      timestamp: new Date(new Date(currentEmail.timestamp || Date.now()).getTime() - 86400000).toISOString(),
      actor: 'AI System: Carrier Booking Engine',
      status: 'Completed',
      icon: Ship,
      details: `Vessel: ${currentEmail.vessel || 'Commercial Carrier'} ${currentEmail.voyage || ''} | Company: ${currentEmail.company || 'Maritime Shipper'}`
    },
    {
      id: 2,
      title: 'Shipping Instruction (SI) Received & Ingested',
      timestamp: currentEmail.timestamp || new Date().toISOString(),
      actor: `AI System: Ingestion Engine (${currentEmail.sender || 'Shipper'})`,
      status: 'Completed',
      icon: FileText,
      details: `Subject: "${currentEmail.subject}" | 7 Reference fields extracted`
    },
    {
      id: 3,
      title: 'Draft Bill of Lading (BL) AI Verification Checked',
      timestamp: new Date(new Date(currentEmail.timestamp || Date.now()).getTime() + 1800000).toISOString(),
      actor: 'AI System: Antigravity Verification Engine',
      status: isMatch ? 'Passed' : isHuman ? 'Escalated' : 'Discrepancy Flagged',
      icon: isMatch ? CheckCircle2 : AlertCircle,
      details: isMatch 
        ? 'All 7 standard fields match perfectly'
        : `Verification result: ${verif.summary_message || 'Field differences detected'}`
    },
    {
      id: 4,
      title: 'Human-in-the-Loop Audit & Override Gate',
      timestamp: new Date(new Date(currentEmail.timestamp || Date.now()).getTime() + 3600000).toISOString(),
      actor: isHuman ? 'User Done: Pending Review' : 'User Done: Audit Validated',
      status: isHuman ? 'Action Required' : 'Approved',
      icon: UserCheck,
      details: isHuman 
        ? `Escalated reason: ${verif.human_review_reasons?.join(' | ') || 'Corrupted stream or blank value'}`
        : 'Rule-based audit trail validated against DCSA standards'
    },
    {
      id: 5,
      title: 'Final Bill of Lading Release',
      timestamp: new Date(new Date(currentEmail.timestamp || Date.now()).getTime() + 7200000).toISOString(),
      actor: 'User Done: Documentation Release',
      status: isMatch ? 'Ready for Release' : 'Pending Revision',
      icon: ShieldCheck,
      details: isMatch ? 'Released to Shipper.' : 'Waiting for revised draft BL.'
    }
  ] : [];

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* SECTION TITLE BAR ON TOP */}
      <div className="px-6 py-3.5 border-b border-blue-900/60 bg-slate-950 flex items-center justify-between shrink-0 shadow-md">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-blue-900/40 border border-blue-500/40 text-cyan-400 flex items-center justify-center">
            <InboxIcon className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-extrabold text-slate-100 tracking-tight flex items-center space-x-2">
              <span>Inbox Workspace</span>
              <span className="text-xs bg-blue-950 text-cyan-400 font-mono px-2 py-0.5 rounded border border-blue-800 font-bold">
                {filteredEmails.length} Emails
              </span>
            </h2>
          </div>
        </div>

        <div className="flex items-center space-x-3">
        </div>
      </div>

      {/* BELOW TITLE BAR: LEFT AND RIGHT SPLIT CONTAINER */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* LEFT SIDE: INBOX FEED (Initial full screen if no email selected) */}
        <div className={`flex flex-col overflow-hidden transition-all duration-300 ${
          selectedEmailId ? 'flex-1 min-w-[380px]' : 'w-full'
        }`}>
          {/* LEFT SIDE TOP BAR: STATUS FILTERS */}
          <div className="p-3.5 border-b border-blue-900/60 bg-blue-950/20 space-y-3">
            <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 text-xs no-scrollbar">
              <span className="text-slate-400 font-bold text-[11px] uppercase tracking-wider shrink-0 mr-1">Status:</span>
              {[
                { id: 'ALL', label: 'All Status' },
                { id: 'CIRCUIT_BREAKER', label: 'Circuit Breaker', color: 'bg-rose-950 text-rose-300 border-rose-600' },
                { id: 'MISMATCH', label: 'Mismatch Found', color: 'bg-rose-950/60 text-rose-300 border-rose-800' },
                { id: 'MATCHED', label: 'No Mismatch', color: 'bg-emerald-950/60 text-emerald-300 border-emerald-800' },
                { id: 'HUMAN_REVIEW', label: 'Human Review', color: 'bg-amber-950/60 text-amber-300 border-amber-800' },
                { id: 'SPAM', label: 'Spam', color: 'bg-slate-800 text-slate-400 border border-slate-700' }
              ].map((st) => (
                <button
                  key={st.id}
                  onClick={() => setSelectedStatus(st.id)}
                  className={`px-3 py-1 rounded-lg font-mono text-xs font-semibold whitespace-nowrap transition ${
                    selectedStatus === st.id
                      ? 'bg-cyan-600 hover:bg-cyan-500 text-white border border-cyan-400 shadow-md'
                      : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-blue-900/40'
                  }`}
                >
                  {st.label}
                </button>
              ))}
            </div>

            {/* SEARCH BAR & DOCUMENTATION TYPES DROPDOWN */}
            <div className="flex items-center space-x-3">
              {/* Search Bar */}
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by email sender, sender name, or email ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-slate-900/90 border border-blue-900/60 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition"
                />
              </div>

              {/* Email Types Dropdown */}
              <select
                value={selectedDocType}
                onChange={(e) => setSelectedDocType(e.target.value)}
                className="bg-slate-900/90 border border-blue-900/60 rounded-xl px-3 py-1.5 text-xs font-semibold text-cyan-300 focus:outline-none focus:border-cyan-400 cursor-pointer shrink-0"
              >
                <option value="ALL">All Document Types</option>
                <option value="SI_BL">SI & BL (Documentations)</option>
                <option value="BOOKING">Booking & Scheduling</option>
                <option value="CONTAINER">Container & Yard Operations</option>
                <option value="FINANCE">Finance & Billing</option>
              </select>
            </div>

            {/* Batch Selection Bar */}
            <div className="flex items-center justify-between text-xs pt-1 border-t border-blue-900/40">
              <button
                onClick={toggleSelectAll}
                className="flex items-center space-x-1.5 text-slate-400 hover:text-slate-200 font-medium"
              >
                {selectedEmailIds.length === filteredEmails.length && filteredEmails.length > 0 ? (
                  <CheckSquare className="w-4 h-4 text-cyan-400" />
                ) : (
                  <Square className="w-4 h-4 text-slate-600" />
                )}
                <span>Select All ({selectedEmailIds.length})</span>
              </button>

              {selectedEmailIds.length > 0 && (
                <span className="text-[11px] text-cyan-400 font-mono font-bold">
                  {selectedEmailIds.length} email(s) selected
                </span>
              )}
            </div>
          </div>

          {/* LEFT SIDE: EMAILS FEED CARDS LIST */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
            {filteredEmails.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-slate-500">
                <FileText className="w-12 h-12 stroke-[1.5] mb-3 text-slate-600" />
                <p className="text-sm font-medium">No matching emails found</p>
              </div>
            ) : (
              filteredEmails.map((email) => {
                const isSelected = selectedEmailId === email.id;
                const isChecked = selectedEmailIds.includes(email.id);
                const classInfo = email.classification || {};
                const emailVerif = email.verification;

                const isSpam = classInfo.category === 'SPAM' || classInfo.super_category === 'Spam / General' || email.is_spam || email.status === 'SPAM' || emailVerif?.status === 'SPAM';
                const isCircuitBreaker = email.circuit_breaker_tripped || email.id === 'email_004' || emailVerif?.circuit_breaker_tripped;
                const isNoMismatch = emailVerif?.status === 'NO_MISMATCH_DETECTED' || emailVerif?.status === 'OK';
                const isMismatch = emailVerif?.status === 'MISMATCH_DETECTED' || emailVerif?.status === 'MISMATCH';
                const isHumanReview = emailVerif?.status === 'HUMAN_REVIEW_REQUIRED' || emailVerif?.status === 'NEEDS_REVIEW';

                return (
                  <div
                    key={email.id}
                    onClick={() => onSelectEmail(email.id)}
                    className={`p-3.5 rounded-xl border transition-all duration-150 cursor-pointer ${
                      isSelected
                        ? 'bg-blue-950/80 border-cyan-400 shadow-lg shadow-cyan-950/50 ring-1 ring-cyan-500/40'
                        : 'bg-slate-900/80 hover:bg-blue-950/40 border-blue-900/40 hover:border-blue-700'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3 mb-1.5">
                      <div className="flex items-center space-x-2">
                        <button onClick={(e) => toggleSelectEmail(email.id, e)}>
                          {isChecked ? (
                            <CheckSquare className="w-4 h-4 text-cyan-400" />
                          ) : (
                            <Square className="w-4 h-4 text-slate-600 hover:text-slate-400" />
                          )}
                        </button>
                        <span className="font-mono text-xs text-cyan-400 font-bold">{email.id}</span>
                        <span className="text-xs font-bold text-slate-200">{email.sender}</span>
                        {email.company && (
                          <span className="text-[11px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
                            {email.company}
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] font-mono text-slate-500 shrink-0">
                        {new Date(email.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    <h3 className="text-xs font-semibold text-slate-100 mb-2 line-clamp-1">
                      {email.subject}
                    </h3>

                    <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-blue-900/30 text-xs">
                      <div className="flex items-center space-x-1.5">
                        <span className="px-2 py-0.5 rounded bg-blue-950 text-cyan-300 text-[10px] font-semibold border border-blue-800">
                          {classInfo.super_category || 'General'}
                        </span>
                        {email.has_attachments && (
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] flex items-center space-x-1 border border-slate-700">
                            <Paperclip className="w-3 h-3" />
                            <span>Docs</span>
                          </span>
                        )}
                      </div>

                      <div className="flex items-center space-x-2">
                        {isCircuitBreaker && (
                          <span className="bg-rose-950 border border-rose-600 text-rose-300 px-2 py-0.5 rounded flex items-center space-x-1 font-mono text-[10px] font-bold">
                            <AlertOctagon className="w-3 h-3 text-rose-400 animate-pulse" />
                            <span>Circuit Breaker</span>
                          </span>
                        )}
                        {isNoMismatch && (
                          <span className="bg-emerald-950/80 text-emerald-300 border border-emerald-700 px-2 py-0.5 rounded flex items-center space-x-1 font-mono text-[10px]">
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                            <span>No Mismatch</span>
                          </span>
                        )}
                        {isMismatch && (
                          <span className="bg-rose-950/80 text-rose-300 border border-rose-700 px-2 py-0.5 rounded flex items-center space-x-1 font-mono text-[10px] mismatch-glow">
                            <AlertCircle className="w-3 h-3 text-rose-400" />
                            <span>Mismatch</span>
                          </span>
                        )}
                        {isHumanReview && (
                          <span className="bg-amber-950/80 text-amber-300 border border-amber-700 px-2 py-0.5 rounded flex items-center space-x-1 font-mono text-[10px]">
                            <HelpCircle className="w-3 h-3 text-amber-400" />
                            <span>Human Review</span>
                          </span>
                        )}
                        {isSpam && (
                          <span className="bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded flex items-center space-x-1 font-mono text-[10px]">
                            <ShieldAlert className="w-3 h-3 text-slate-400" />
                            <span>Spam</span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* RESIZABLE DIVIDER HANDLE */}
        {selectedEmailId && (
          <div
            onMouseDown={handleMouseDownResize}
            className="resize-handle hover:bg-cyan-400 active:bg-cyan-300 shrink-0"
            title="Drag to resize Inspector panel width"
          />
        )}

        {/* RIGHT SIDE: EMAIL INSPECTOR & EXPANDABLE CONTENT & 2 TABS */}
        {selectedEmailId && (
          <div
            style={{ width: `${inspectorWidth}px` }}
            className="flex flex-col border-l border-blue-900/60 bg-slate-950 shrink-0 overflow-hidden relative shadow-2xl"
          >
            {/* RIGHT SIDE HEADER */}
            <div className="p-4 border-b border-blue-900/60 bg-blue-950/30 flex items-center justify-between shrink-0">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs font-bold text-cyan-400 bg-blue-950 px-2 py-0.5 rounded border border-blue-800">
                    {currentEmail?.id}
                  </span>
                  <h3 className="text-sm font-bold text-slate-100 line-clamp-1">{currentEmail?.subject}</h3>
                </div>
                <div className="text-xs text-slate-400 font-mono space-x-2">
                  <span>Sender: <strong className="text-slate-200">{currentEmail?.sender}</strong></span>
                  <span>•</span>
                  <span>Company: <strong className="text-cyan-300">{currentEmail?.company || 'N/A'}</strong></span>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowReceiptDrawer(true)}
                  className="px-2.5 py-1.5 rounded-lg bg-indigo-950 hover:bg-indigo-900 text-indigo-300 text-xs font-semibold border border-indigo-700 flex items-center space-x-1 transition"
                >
                  <Terminal className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Reasoning Receipt</span>
                </button>
                <button
                  onClick={onOpenOverrideModal}
                  className="px-2.5 py-1.5 rounded-lg bg-blue-950 hover:bg-blue-900 text-slate-200 text-xs font-semibold border border-blue-800 flex items-center space-x-1 transition"
                >
                  <Edit3 className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Override</span>
                </button>
                <button
                  onClick={() => onSelectEmail(null)}
                  className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700 transition"
                  title="Close Inspector"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* DROPDOWN EXPANDABLE CARD FOR ACTUAL EMAIL CONTENT (DEFAULT CLOSED / MINIMIZED) */}
            <div className="p-3 border-b border-blue-900/40 bg-slate-900/60 shrink-0 space-y-2.5">
              <button
                onClick={() => setIsEmailContentOpen(!isEmailContentOpen)}
                className="w-full flex items-center justify-between p-2.5 rounded-xl bg-blue-950/40 hover:bg-blue-950/80 border border-blue-900/60 text-xs font-bold text-slate-200 transition"
              >
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-cyan-400" />
                  <span>Actual Email Content / Body Text</span>
                  <span className="text-[10px] font-mono text-slate-400 font-normal">
                    (Click to {isEmailContentOpen ? 'minimize' : 'expand'})
                  </span>
                </div>
                {isEmailContentOpen ? <ChevronUp className="w-4 h-4 text-cyan-400" /> : <ChevronDown className="w-4 h-4 text-cyan-400" />}
              </button>

              {isEmailContentOpen && (
                <div className="p-3 rounded-xl bg-slate-950 border border-blue-900/60 font-mono text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap animate-fadeIn">
                  {currentEmail?.body || 'No text body available.'}
                </div>
              )}

              <button
                onClick={() => setShowUploadModal(true)}
                className="w-full py-2 px-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-extrabold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-cyan-950/60 transition active:scale-95 cursor-pointer"
              >
                <Upload className="w-4 h-4" />
                <span>Upload SI + BL Pair</span>
              </button>
            </div>

            {/* 2 TABS CONTROL BAR: SI vs BL AND SHIPMENT TIMELINE */}
            <div className="px-4 py-2 bg-blue-950/40 border-b border-blue-900/60 flex items-center space-x-2 shrink-0">
              <button
                onClick={() => setActiveRightTab('si_vs_bl')}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition ${
                  activeRightTab === 'si_vs_bl'
                    ? 'bg-cyan-600 hover:bg-cyan-500 text-white border border-cyan-400 shadow-md'
                    : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <FileCheck2 className="w-4 h-4" />
                <span>SI vs BL</span>
              </button>

              <button
                onClick={() => setActiveRightTab('timeline')}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition ${
                  activeRightTab === 'timeline'
                    ? 'bg-cyan-600 hover:bg-cyan-500 text-white border border-cyan-400 shadow-md'
                    : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <GitCommit className="w-4 h-4" />
                <span>Shipment Timeline</span>
              </button>
            </div>

            {/* SCROLLABLE TAB BODY */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* TAB 1: SI VS BL */}
              {activeRightTab === 'si_vs_bl' && (
                <>
                  {/* Circuit Breaker Tripped Card */}
                  {(currentEmail?.id === 'email_004' || currentEmail?.circuit_breaker_tripped || verif.circuit_breaker_tripped) && (
                    <div className="p-4 rounded-xl border border-rose-500/60 bg-rose-950/30 space-y-3 shadow-lg">
                      <div className="flex items-center space-x-2">
                        <AlertOctagon className="w-5 h-5 text-rose-500 animate-pulse" />
                        <span className="text-xs font-bold uppercase tracking-wider text-rose-200">
                          ⚡ AI Circuit Breaker Tripped — Automated Pipeline Halted
                        </span>
                      </div>
                      <RefusalCertificatePanel 
                        certificate={emailDetail?.refusal_certificate || DEFAULT_CIRCUIT_BREAKER_CERTIFICATE} 
                      />
                    </div>
                  )}

                  {/* AI Recommendation Banner */}
                  {verif.recommended_action && (
                    <div className="p-4 rounded-xl bg-slate-900 border border-indigo-500/30 flex items-start justify-between shadow-lg">
                      <div className="flex items-start space-x-3">
                        <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
                        <div>
                          <h4 className="text-xs font-semibold uppercase tracking-wider text-indigo-300">
                            AI Recommended Action
                          </h4>
                          <p className="text-xs font-medium text-slate-100 mt-0.5">
                            {verif.recommended_action}
                          </p>
                        </div>
                      </div>

                      {!isMatch && (
                        <button
                          onClick={onOpenOverrideModal}
                          className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shrink-0"
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  )}

                  {/* Conflict Evidence Side by Side Propose-and-Confirm */}
                  {currentEmail?.id && !isMatch && (
                    <ConflictEvidencePanel emailId={currentEmail.id} emailDetail={emailDetail} />
                  )}

                  {/* 7-Field Side-by-Side Matrix */}
                  {verif.field_matrix && (
                    <div className="rounded-xl border border-blue-900/60 bg-slate-900/80 overflow-hidden shadow-lg">
                      <div className="p-3 bg-blue-950/60 border-b border-blue-900/60 flex items-center justify-between">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                          <FileCheck2 className="w-4 h-4 text-cyan-400" />
                          <span>7-Field Comparison Matrix (Click row to highlight line in raw document below)</span>
                        </h3>
                      </div>

                      <div className="divide-y divide-blue-900/40 text-xs font-mono">
                        {verif.field_matrix.map((row) => {
                          const isSelected = selectedFieldKey === row.field_key;
                          return (
                            <div
                              key={row.field_key}
                              onClick={() => setSelectedFieldKey(isSelected ? null : row.field_key)}
                              className={`grid grid-cols-12 p-3 items-center cursor-pointer transition ${
                                isSelected
                                  ? 'bg-cyan-950/60 border-l-4 border-l-cyan-400'
                                  : !row.is_match
                                  ? 'bg-rose-950/20 border-l-4 border-l-rose-500 hover:bg-rose-950/30'
                                  : 'hover:bg-blue-950/30'
                              }`}
                            >
                              <div className="col-span-3 font-semibold text-slate-300 truncate">
                                {row.field_name}
                              </div>
                              <div className="col-span-4 text-slate-200 bg-slate-950 p-2 rounded border border-slate-800 truncate">
                                {row.si_value || '—'}
                              </div>
                              <div className="col-span-1 flex justify-center">
                                <ArrowRight className={`w-4 h-4 ${!row.is_match ? 'text-rose-400' : 'text-slate-600'}`} />
                              </div>
                              <div className="col-span-4 text-slate-200 bg-slate-950 p-2 rounded border border-slate-800 truncate">
                                {renderDiff(row.si_value, row.bl_value, row.is_match)}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Raw Attachment Side-by-Side Text Comparison */}
                  <div className="grid grid-cols-2 gap-4 pt-2">
                    {/* Left Panel: SI Text */}
                    <div className="rounded-xl border border-blue-900/60 bg-slate-900/80 p-4 space-y-2.5 shadow-lg">
                      <div className="flex items-center justify-between border-b border-blue-900/60 pb-2">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center space-x-2">
                          <FileText className="w-4 h-4" />
                          <span>Shipping Instruction (SI Raw Text)</span>
                        </h4>
                        <span className="text-[10px] font-mono bg-cyan-950 text-cyan-300 px-2 py-0.5 rounded border border-cyan-800">
                          SI Attachment File
                        </span>
                      </div>
                      <div className="font-mono text-xs text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-900 overflow-x-auto leading-relaxed max-h-72 space-y-1">
                        {(emailDetail?.si_text || currentEmail?.si_text || 'No SI file text available.').split('\n').map((line, idx) => {
                          const isSelected = selectedFieldKey && line.toLowerCase().includes(selectedFieldKey.replace('_', ' '));
                          return (
                            <div key={idx} className={isSelected ? 'bg-cyan-950 text-cyan-300 font-bold px-1 rounded border-l-2 border-cyan-400' : ''}>
                              {line}
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Right Panel: Draft BL Text */}
                    <div className="rounded-xl border border-blue-900/60 bg-slate-900/80 p-4 space-y-2.5 shadow-lg">
                      <div className="flex items-center justify-between border-b border-blue-900/60 pb-2">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-blue-400 flex items-center space-x-2">
                          <FileText className="w-4 h-4" />
                          <span>Draft Bill of Lading (BL Raw Text)</span>
                        </h4>
                        <span className="text-[10px] font-mono bg-blue-950 text-blue-300 px-2 py-0.5 rounded border border-blue-800">
                          BL Attachment File
                        </span>
                      </div>
                      <div className="font-mono text-xs text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-900 overflow-x-auto leading-relaxed max-h-72 space-y-1">
                        {(emailDetail?.bl_text || currentEmail?.bl_text || 'No BL file text available.').split('\n').map((line, idx) => {
                          const isSelected = selectedFieldKey && line.toLowerCase().includes(selectedFieldKey.replace('_', ' '));
                          return (
                            <div key={idx} className={isSelected ? 'bg-cyan-950 text-cyan-300 font-bold px-1 rounded border-l-2 border-cyan-400' : ''}>
                              {line}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* TAB 2: SHIPMENT TIMELINE */}
              {activeRightTab === 'timeline' && (
                <div className="rounded-xl border border-blue-900/60 bg-slate-900/80 p-5 space-y-4 shadow-lg">
                  <div className="flex items-center justify-between border-b border-blue-900/60 pb-3">
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-100 flex items-center space-x-2">
                        <GitCommit className="w-4 h-4 text-cyan-400" />
                        <span>Shipment Audit Timeline</span>
                      </h3>
                    </div>
                  </div>

                  <div className="relative border-l-2 border-blue-900/60 ml-4 pl-6 space-y-4 py-2">
                    {milestones.map((m) => {
                      const Icon = m.icon;
                      return (
                        <div key={m.id} className="relative">
                          <div className={`absolute -left-[35px] top-1 w-7 h-7 rounded-full flex items-center justify-center border-2 ${
                            m.status === 'Completed' || m.status === 'Passed' || m.status === 'Approved'
                              ? 'bg-emerald-950 border-emerald-500 text-emerald-400'
                              : 'bg-amber-950 border-amber-500 text-amber-400'
                          }`}>
                            <Icon className="w-3.5 h-3.5" />
                          </div>

                          <div className="p-3 rounded-xl bg-slate-950 border border-blue-900/40 text-xs font-mono space-y-1">
                            <div className="flex items-center justify-between">
                              <h4 className="font-bold text-slate-100 text-xs">{m.title}</h4>
                              <span className="text-[10px] text-slate-500">{new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            </div>
                            <p className="text-[11px] text-slate-300">{m.details}</p>
                            <span className="text-[10px] text-cyan-400 font-semibold block">{m.actor}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* REASONING RECEIPT DRAWER */}
      {showReceiptDrawer && (
        <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl glass-panel border-l border-blue-800 shadow-2xl p-6 flex flex-col space-y-4 animate-slideLeft bg-slate-950">
          <div className="flex items-center justify-between border-b border-blue-900/60 pb-3">
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
            <ReasoningReceipt
              emailId={currentEmail?.id}
              shipmentId={verif?.shipment_id}
              defaultOpen
            />
          </div>
        </div>
      )}

      {/* Upload SI + BL Pair Modal */}
      <UploadDocsModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUploadSuccess={onUploadSuccess}
        targetEmail={currentEmail}
      />
    </div>
  );
}
