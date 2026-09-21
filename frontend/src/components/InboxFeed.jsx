import React, { useState } from 'react';
import { 
  Search, 
  Tag, 
  FileText, 
  AlertCircle, 
  CheckCircle2, 
  HelpCircle, 
  ChevronRight, 
  Paperclip,
  Filter,
  CheckSquare,
  Square,
  ShieldCheck,
  Send
} from 'lucide-react';

export default function InboxFeed({ emails, selectedEmailId, onSelectEmail, onOpenInspector }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [selectedEmailIds, setSelectedEmailIds] = useState([]);

  const superCategories = [
    'ALL',
    'Documentation (SI & BL)',
    'Booking & Scheduling',
    'Container & Yard Ops',
    'Port & Vessel Ops',
    'Finance & Billing',
    'Spam / General'
  ];

  const filteredEmails = emails.filter((email) => {
    const textStr = `${email.subject} ${email.sender} ${email.company} ${email.vessel} ${email.classification?.ui_tag}`.toLowerCase();
    const matchesSearch = textStr.includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'ALL' || email.classification?.super_category === selectedCategory;

    let matchesStatus = true;
    if (selectedStatus === 'MISMATCH') {
      matchesStatus = email.verification?.status === 'MISMATCH_DETECTED';
    } else if (selectedStatus === 'MATCHED') {
      matchesStatus = email.verification?.status === 'NO_MISMATCH_DETECTED';
    } else if (selectedStatus === 'HUMAN_REVIEW') {
      matchesStatus = email.verification?.status === 'HUMAN_REVIEW_REQUIRED';
    } else if (selectedStatus === 'SPAM') {
      matchesStatus = email.classification?.super_category === 'Spam / General';
    }

    return matchesSearch && matchesCategory && matchesStatus;
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

  const handleBatchApprove = () => {
    alert(`Batch Approved ${selectedEmailIds.length} clean match shipment(s)! Draft Bills of Lading released.`);
    setSelectedEmailIds([]);
  };

  const handleBatchEscalate = () => {
    alert(`Batch Escalated ${selectedEmailIds.length} shipment(s) to Human Review Queue.`);
    setSelectedEmailIds([]);
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950">
      {/* Search & Filter Header */}
      <div className="p-4 border-b border-slate-800 glass-panel space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <span>Shipping Operations Inbox</span>
            <span className="text-xs bg-slate-800 text-cyan-400 font-mono px-2 py-0.5 rounded border border-slate-700">
              {filteredEmails.length} messages
            </span>
          </h2>

          {/* Quick Search */}
          <div className="relative w-72">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search sender, vessel, SI/BL..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-lg pl-9 pr-3 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
            />
          </div>
        </div>

        {/* Super Category Filters */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs no-scrollbar">
          <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0 mr-1" />
          {superCategories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-md whitespace-nowrap font-medium transition ${
                selectedCategory === cat
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Batch Operations & Status Quick Filter Bar */}
        <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/60">
          <div className="flex items-center space-x-2">
            <button
              onClick={toggleSelectAll}
              className="flex items-center space-x-1.5 text-slate-400 hover:text-slate-200 font-medium"
            >
              {selectedEmailIds.length === filteredEmails.length && filteredEmails.length > 0 ? (
                <CheckSquare className="w-4 h-4 text-cyan-400" />
              ) : (
                <Square className="w-4 h-4" />
              )}
              <span>Select All ({selectedEmailIds.length})</span>
            </button>

            {selectedEmailIds.length > 0 && (
              <div className="flex items-center space-x-2 ml-4 animate-fadeIn">
                <button
                  onClick={handleBatchApprove}
                  className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center space-x-1 shadow"
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Batch Approve</span>
                </button>
                <button
                  onClick={handleBatchEscalate}
                  className="px-2.5 py-1 rounded bg-amber-600 hover:bg-amber-500 text-slate-950 font-semibold text-xs flex items-center space-x-1 shadow"
                >
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>Batch Escalate</span>
                </button>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-slate-500 font-medium">Status:</span>
            {[
              { id: 'ALL', label: 'All Status' },
              { id: 'MISMATCH', label: 'Mismatch Found', color: 'badge-mismatch' },
              { id: 'MATCHED', label: 'No Mismatch', color: 'badge-match' },
              { id: 'HUMAN_REVIEW', label: 'Human Review', color: 'badge-warning' },
              { id: 'SPAM', label: 'Spam', color: 'bg-slate-800 text-slate-400 border border-slate-700' }
            ].map((st) => (
              <button
                key={st.id}
                onClick={() => setSelectedStatus(st.id)}
                className={`px-2.5 py-0.5 rounded font-mono transition ${
                  selectedStatus === st.id
                    ? 'bg-slate-700 text-slate-100 border border-slate-500'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 border border-transparent'
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Inbox List */}
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
            const verif = email.verification;

            return (
              <div
                key={email.id}
                onClick={() => onSelectEmail(email.id)}
                className={`p-3.5 rounded-xl border transition-all duration-150 cursor-pointer ${
                  isSelected
                    ? 'bg-slate-900/90 border-cyan-500/60 shadow-lg shadow-cyan-950/30'
                    : 'glass-card hover:bg-slate-900/50 hover:border-slate-700 border-slate-800/80'
                }`}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center space-x-2">
                    <button onClick={(e) => toggleSelectEmail(email.id, e)}>
                      {isChecked ? (
                        <CheckSquare className="w-4 h-4 text-cyan-400" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-600 hover:text-slate-400" />
                      )}
                    </button>
                    <span className="font-mono text-xs text-slate-400 font-semibold">{email.id}</span>
                    <span className="text-sm font-semibold text-slate-200">{email.sender}</span>
                    {email.company && (
                      <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
                        {email.company}
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-mono text-slate-500 shrink-0">
                    {new Date(email.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                <h3 className="text-sm font-medium text-slate-100 mb-2.5 line-clamp-1">
                  {email.subject}
                </h3>

                <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/60 text-xs">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded bg-slate-800/90 text-slate-300 font-medium text-[11px] border border-slate-700">
                      {classInfo.super_category}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-300 text-[11px] border border-cyan-800/50 flex items-center space-x-1">
                      <Tag className="w-3 h-3 text-cyan-400" />
                      <span>{classInfo.ui_tag}</span>
                    </span>
                    {email.has_attachments && (
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 text-[11px] flex items-center space-x-1 border border-slate-700">
                        <Paperclip className="w-3 h-3" />
                        <span>SI/BL Docs</span>
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    {verif?.status === 'NO_MISMATCH_DETECTED' && (
                      <span className="badge-match px-2 py-0.5 rounded flex items-center space-x-1 font-mono text-[11px]">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>No Mismatch</span>
                      </span>
                    )}
                    {verif?.status === 'MISMATCH_DETECTED' && (
                      <span className="badge-mismatch px-2 py-0.5 rounded flex items-center space-x-1 font-mono text-[11px] mismatch-glow">
                        <AlertCircle className="w-3 h-3" />
                        <span>Mismatch ({verif.mismatched_fields.length})</span>
                      </span>
                    )}
                    {verif?.status === 'HUMAN_REVIEW_REQUIRED' && (
                      <span className="badge-warning px-2 py-0.5 rounded flex items-center space-x-1 font-mono text-[11px]">
                        <HelpCircle className="w-3 h-3" />
                        <span>Human Review</span>
                      </span>
                    )}

                    {classInfo.is_comparison_request && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectEmail(email.id);
                          onOpenInspector();
                        }}
                        className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs flex items-center space-x-1 shadow transition"
                      >
                        <span>Inspect</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
