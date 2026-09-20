import React, { useState, useMemo } from 'react';
import { 
  Search, 
  Tag, 
  FileText, 
  AlertCircle, 
  CheckCircle2, 
  HelpCircle, 
  ChevronRight, 
  ChevronLeft,
  Paperclip,
  Filter,
  Layers,
  AlertTriangle
} from 'lucide-react';

export default function InboxFeed({ emails, selectedEmailId, onSelectEmail, onOpenInspector }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  const categories = [
    { id: 'ALL', label: 'All Categories' },
    { id: 'BL_COMPARISON', label: 'BL Checks (Comparison)', countId: 'BL_COMPARISON' },
    { id: 'SI_REQUEST', label: 'SI Requests', countId: 'SI_REQUEST' },
    { id: 'INVOICE_QUERY', label: 'Invoices & Billing', countId: 'INVOICE_QUERY' },
    { id: 'GENERAL', label: 'General Operations', countId: 'GENERAL' },
    { id: 'SPAM', label: 'Spam', countId: 'SPAM' }
  ];

  const filteredEmails = useMemo(() => {
    return emails.filter((email) => {
      const textStr = `${email.id} ${email.subject} ${email.sender} ${email.company || ''} ${email.vessel || ''} ${email.classification?.ui_tag || ''} ${email.classification?.category || ''}`.toLowerCase();
      const matchesSearch = textStr.includes(searchTerm.toLowerCase().trim());

      const emailCat = email.classification?.category || '';
      const matchesCategory = 
        selectedCategory === 'ALL' || emailCat === selectedCategory;

      let matchesStatus = true;
      const stat = email.verification?.status || '';
      if (selectedStatus === 'MISMATCH') {
        matchesStatus = stat === 'MISMATCH' || stat === 'MISMATCH_DETECTED';
      } else if (selectedStatus === 'OK') {
        matchesStatus = stat === 'OK' || stat === 'NO_MISMATCH_DETECTED';
      } else if (selectedStatus === 'NEEDS_REVIEW') {
        matchesStatus = stat === 'NEEDS_REVIEW' || stat === 'HUMAN_REVIEW_REQUIRED';
      }

      return matchesSearch && matchesCategory && matchesStatus;
    });
  }, [emails, searchTerm, selectedCategory, selectedStatus]);

  // Pagination calculation
  const totalPages = Math.ceil(filteredEmails.length / pageSize) || 1;
  const paginatedEmails = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredEmails.slice(start, start + pageSize);
  }, [filteredEmails, currentPage, pageSize]);

  const handleCategorySelect = (catId) => {
    setSelectedCategory(catId);
    setCurrentPage(1);
  };

  const handleStatusSelect = (statId) => {
    setSelectedStatus(statId);
    setCurrentPage(1);
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950">
      {/* Search & Filter Header */}
      <div className="p-4 border-b border-slate-800 glass-panel space-y-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
              <Layers className="w-5 h-5 text-cyan-400" />
              <span>Shipping Operations Inbox</span>
            </h2>
            <span className="text-xs bg-slate-800 text-cyan-400 font-mono px-2 py-0.5 rounded border border-slate-700">
              {filteredEmails.length} of {emails.length} emails
            </span>
          </div>

          {/* Quick Search */}
          <div className="relative w-72">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search ID, subject, shipper, vessel..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-lg pl-9 pr-3 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
            />
          </div>
        </div>

        {/* Category Filters */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs no-scrollbar">
          <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0 mr-1" />
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => handleCategorySelect(cat.id)}
              className={`px-3 py-1.5 rounded-lg whitespace-nowrap font-medium transition ${
                selectedCategory === cat.id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-sm'
                  : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Status Quick Filter Bar & Pagination Status */}
        <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/60">
          <div className="flex items-center space-x-2">
            <span className="text-slate-500 font-medium">Verification Status:</span>
            {[
              { id: 'ALL', label: 'All Statuses' },
              { id: 'MISMATCH', label: 'Mismatch Detected', cls: 'badge-mismatch' },
              { id: 'OK', label: 'OK (Matched)', cls: 'badge-match' },
              { id: 'NEEDS_REVIEW', label: 'Needs Review', cls: 'badge-warning' }
            ].map((st) => (
              <button
                key={st.id}
                onClick={() => handleStatusSelect(st.id)}
                className={`px-2.5 py-1 rounded font-mono transition ${
                  selectedStatus === st.id
                    ? 'bg-slate-700 text-slate-100 border border-slate-500 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 border border-transparent'
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center space-x-2 font-mono text-slate-400">
              <span>Page {currentPage} of {totalPages}</span>
              <button
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                className="p-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <button
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                className="p-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Inbox List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
        {paginatedEmails.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <FileText className="w-12 h-12 stroke-[1.5] mb-3 text-slate-600" />
            <p className="text-sm font-medium">No matching emails found</p>
            <p className="text-xs text-slate-600">Try adjusting your filters or search keywords</p>
          </div>
        ) : (
          paginatedEmails.map((email) => {
            const isSelected = selectedEmailId === email.id;
            const classInfo = email.classification || {};
            const verif = email.verification;
            const category = classInfo.category || 'GENERAL';

            return (
              <div
                key={email.id}
                onClick={() => onSelectEmail(email.id)}
                className={`p-3.5 rounded-xl border transition-all duration-150 cursor-pointer ${
                  isSelected
                    ? 'bg-slate-900/90 border-cyan-500/60 shadow-lg shadow-cyan-950/30 ring-1 ring-cyan-500/30'
                    : 'glass-card hover:bg-slate-900/50 hover:border-slate-700 border-slate-800/80'
                }`}
              >
                <div className="flex items-start justify-between gap-3 mb-1.5">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs text-cyan-400 font-bold bg-cyan-950/40 px-1.5 py-0.5 rounded border border-cyan-800/40">
                      {email.id}
                    </span>
                    <span className="text-sm font-semibold text-slate-200">{email.sender}</span>
                    {email.company && (
                      <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700 truncate max-w-[180px]">
                        {email.company}
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-mono text-slate-500 shrink-0">
                    {new Date(email.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                {/* Email Subject */}
                <h3 className="text-sm font-medium text-slate-100 mb-2.5 line-clamp-1">
                  {email.subject}
                </h3>

                {/* Tag Bar & Operational Indicators */}
                <div className="flex flex-wrap items-center justify-between gap-2 pt-1.5 border-t border-slate-800/60 text-xs">
                  <div className="flex flex-wrap items-center gap-1.5">
                    {/* Official Category Pill */}
                    <span className={`px-2 py-0.5 rounded font-mono text-[11px] font-semibold border ${
                      category === 'BL_COMPARISON' ? 'bg-indigo-950 text-indigo-300 border-indigo-700' :
                      category === 'SI_REQUEST' ? 'bg-sky-950 text-sky-300 border-sky-700' :
                      category === 'INVOICE_QUERY' ? 'bg-purple-950 text-purple-300 border-purple-700' :
                      category === 'SPAM' ? 'bg-rose-950 text-rose-300 border-rose-700' :
                      'bg-slate-800 text-slate-300 border-slate-700'
                    }`}>
                      {category}
                    </span>

                    {/* UI Tag */}
                    <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-300 text-[11px] border border-slate-800 flex items-center space-x-1">
                      <Tag className="w-3 h-3 text-cyan-400" />
                      <span>{classInfo.ui_tag || classInfo.super_category}</span>
                    </span>

                    {/* Attachments indicator */}
                    {email.attachments && email.attachments.length > 0 && (
                      <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-400 text-[11px] flex items-center space-x-1 border border-slate-800">
                        <Paperclip className="w-3 h-3 text-slate-500" />
                        <span>{email.attachments.length} doc{email.attachments.length > 1 ? 's' : ''}</span>
                      </span>
                    )}
                  </div>

                  {/* Verification Status Pill */}
                  <div className="flex items-center space-x-2">
                    {verif?.status === 'OK' && (
                      <span className="badge-match px-2.5 py-0.5 rounded-full flex items-center space-x-1 font-mono text-[11px] font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>OK (All 7 Matched)</span>
                      </span>
                    )}
                    {verif?.status === 'MISMATCH' && (
                      <span className="badge-mismatch px-2.5 py-0.5 rounded-full flex items-center space-x-1 font-mono text-[11px] font-semibold mismatch-glow">
                        <AlertCircle className="w-3.5 h-3.5" />
                        <span>MISMATCH ({verif.defect_fields?.length || 0} defects)</span>
                      </span>
                    )}
                    {verif?.status === 'NEEDS_REVIEW' && (
                      verif?.review_reason === 'missing_attachment' ? (
                        <span className="bg-amber-950/80 border border-amber-500/70 text-amber-300 px-2.5 py-0.5 rounded-full flex items-center space-x-1 font-mono text-[11px] font-bold shadow-sm shadow-amber-950/50">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                          <span>GATE: MISSING ATTACHMENT</span>
                        </span>
                      ) : (
                        <span className="badge-warning px-2.5 py-0.5 rounded-full flex items-center space-x-1 font-mono text-[11px] font-semibold">
                          <HelpCircle className="w-3.5 h-3.5" />
                          <span>NEEDS REVIEW: {verif.review_reason}</span>
                        </span>
                      )
                    )}

                    {category === 'BL_COMPARISON' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectEmail(email.id);
                          onOpenInspector();
                        }}
                        className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs flex items-center space-x-1 shadow transition active:scale-95 ml-1"
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

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="p-3 border-t border-slate-800 glass-panel flex items-center justify-between text-xs text-slate-400">
          <div className="font-mono">
            Showing {(currentPage - 1) * pageSize + 1} - {Math.min(currentPage * pageSize, filteredEmails.length)} of {filteredEmails.length}
          </div>
          <div className="flex items-center space-x-1 font-mono">
            <button
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage(1)}
              className="px-2 py-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none"
            >
              First
            </button>
            <button
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
              className="px-2 py-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none"
            >
              Prev
            </button>
            <span className="px-3 py-1 font-bold text-cyan-400 bg-slate-900/60 rounded border border-slate-800">
              {currentPage} / {totalPages}
            </span>
            <button
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
              className="px-2 py-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none"
            >
              Next
            </button>
            <button
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage(totalPages)}
              className="px-2 py-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none"
            >
              Last
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
