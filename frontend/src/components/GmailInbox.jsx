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
  Star, 
  Clock, 
  Archive, 
  Trash2, 
  Mail, 
  MailOpen, 
  RotateCw, 
  MoreVertical, 
  Square, 
  CheckSquare, 
  MinusSquare,
  ChevronDown,
  Columns,
  Rows,
  Maximize2,
  Minimize2,
  ArrowLeft,
  Printer,
  ExternalLink,
  Reply,
  Forward,
  Bookmark,
  AlertTriangle,
  FileCheck2,
  Ship,
  Sparkles,
  SlidersHorizontal,
  Check
} from 'lucide-react';

export default function GmailInbox({
  emails,
  selectedEmailId,
  onSelectEmail,
  emailDetail,
  onOpenInspector,
  onOpenOverrideModal,
  onRefresh,
  previewPaneMode = 'vertical',
  setPreviewPaneMode,
  showToast
}) {
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedEmailIds, setSelectedEmailIds] = useState(new Set());
  const [starredEmailIds, setStarredEmailIds] = useState(new Set(['email_001', 'email_004', 'email_012']));
  const [importantEmailIds, setImportantEmailIds] = useState(new Set(['email_001', 'email_002']));
  const [readEmailIds, setReadEmailIds] = useState(new Set(['email_001', 'email_003']));
  const [activeTab, setActiveTab] = useState('primary'); // 'primary', 'bl', 'si', 'review'
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showSelectMenu, setShowSelectMenu] = useState(false);
  const [showSplitMenu, setShowSplitMenu] = useState(false);
  const [activeMobileView, setActiveMobileView] = useState('list'); // 'list' or 'detail'

  const pageSize = 25;

  // Filter emails based on category tab, status, and search
  const filteredEmails = useMemo(() => {
    return emails.filter((email) => {
      // Category tab filtering
      if (activeTab === 'bl' && email.classification?.category !== 'BL_COMPARISON') return false;
      if (activeTab === 'si' && email.classification?.category !== 'SI_REQUEST') return false;
      if (activeTab === 'review') {
        const isReview = email.verification?.status === 'NEEDS_REVIEW' || email.verification?.status === 'HUMAN_REVIEW_REQUIRED' || email.verification?.status === 'MISMATCH';
        if (!isReview) return false;
      }

      // Status filter
      if (selectedStatus === 'MISMATCH') {
        if (email.verification?.status !== 'MISMATCH' && email.verification?.status !== 'MISMATCH_DETECTED') return false;
      } else if (selectedStatus === 'OK') {
        if (email.verification?.status !== 'OK' && email.verification?.status !== 'NO_MISMATCH_DETECTED') return false;
      } else if (selectedStatus === 'NEEDS_REVIEW') {
        if (email.verification?.status !== 'NEEDS_REVIEW' && email.verification?.status !== 'HUMAN_REVIEW_REQUIRED') return false;
      }

      return true;
    });
  }, [emails, activeTab, selectedStatus]);

  // Pagination calculation
  const totalPages = Math.ceil(filteredEmails.length / pageSize) || 1;
  const paginatedEmails = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredEmails.slice(start, start + pageSize);
  }, [filteredEmails, currentPage, pageSize]);

  // Star toggle
  const toggleStar = (e, id) => {
    e.stopPropagation();
    const newStarred = new Set(starredEmailIds);
    if (newStarred.has(id)) {
      newStarred.delete(id);
    } else {
      newStarred.add(id);
    }
    setStarredEmailIds(newStarred);
  };

  // Important toggle
  const toggleImportant = (e, id) => {
    e.stopPropagation();
    const newImp = new Set(importantEmailIds);
    if (newImp.has(id)) {
      newImp.delete(id);
    } else {
      newImp.add(id);
    }
    setImportantEmailIds(newImp);
  };

  // Checkbox select
  const toggleSelect = (e, id) => {
    e.stopPropagation();
    const newSel = new Set(selectedEmailIds);
    if (newSel.has(id)) {
      newSel.delete(id);
    } else {
      newSel.add(id);
    }
    setSelectedEmailIds(newSel);
  };

  // Bulk select
  const handleSelectAll = () => {
    if (selectedEmailIds.size === paginatedEmails.length) {
      setSelectedEmailIds(new Set());
    } else {
      setSelectedEmailIds(new Set(paginatedEmails.map((e) => e.id)));
    }
    setShowSelectMenu(false);
  };

  const handleSelectNone = () => {
    setSelectedEmailIds(new Set());
    setShowSelectMenu(false);
  };

  const handleSelectRead = () => {
    setSelectedEmailIds(new Set(paginatedEmails.filter((e) => readEmailIds.has(e.id)).map((e) => e.id)));
    setShowSelectMenu(false);
  };

  const handleSelectUnread = () => {
    setSelectedEmailIds(new Set(paginatedEmails.filter((e) => !readEmailIds.has(e.id)).map((e) => e.id)));
    setShowSelectMenu(false);
  };

  const handleSelectStarred = () => {
    setSelectedEmailIds(new Set(paginatedEmails.filter((e) => starredEmailIds.has(e.id)).map((e) => e.id)));
    setShowSelectMenu(false);
  };

  const handleRefreshClick = () => {
    setIsRefreshing(true);
    if (onRefresh) onRefresh();
    if (showToast) showToast('Refreshed inbox messages', 'info');
    setTimeout(() => setIsRefreshing(false), 800);
  };

  const handleEmailClick = (id) => {
    onSelectEmail(id);
    setActiveMobileView('detail');
    setReadEmailIds(new Set([...readEmailIds, id]));
  };

  const handleBatchArchive = () => {
    if (showToast) showToast(`Archived ${selectedEmailIds.size} conversations`, 'info');
    setSelectedEmailIds(new Set());
  };

  const handleBatchDelete = () => {
    if (showToast) showToast(`Moved ${selectedEmailIds.size} conversations to Trash`, 'warning');
    setSelectedEmailIds(new Set());
  };

  const handleBatchMarkRead = () => {
    const nextRead = new Set(readEmailIds);
    selectedEmailIds.forEach((id) => nextRead.add(id));
    setReadEmailIds(nextRead);
    setSelectedEmailIds(new Set());
    if (showToast) showToast(`Marked as read`, 'info');
  };

  const selectedEmail = emails.find((e) => e.id === selectedEmailId) || emails[0];
  const isSelectedAll = selectedEmailIds.size > 0 && selectedEmailIds.size === paginatedEmails.length;
  const isPartiallySelected = selectedEmailIds.size > 0 && selectedEmailIds.size < paginatedEmails.length;

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden select-none" style={{ backgroundColor: 'var(--gmail-bg)' }}>
      
      {/* Gmail Action Toolbar */}
      <div 
        className="h-12 px-4 flex items-center justify-between border-b text-xs text-slate-600 dark:text-slate-300"
        style={{
          backgroundColor: 'var(--gmail-surface)',
          borderColor: 'var(--gmail-border)'
        }}
      >
        {/* Left Action Buttons */}
        <div className="flex items-center space-x-1">
          
          {/* Select Checkbox with Dropdown */}
          <div className="relative flex items-center">
            <button
              onClick={handleSelectAll}
              className="p-1.5 rounded-l hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300 transition"
              title="Select all"
            >
              {isSelectedAll ? (
                <CheckSquare className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              ) : isPartiallySelected ? (
                <MinusSquare className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              ) : (
                <Square className="w-4 h-4 text-slate-400" />
              )}
            </button>
            <button
              onClick={() => setShowSelectMenu(!showSelectMenu)}
              className="p-1.5 rounded-r hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300 transition"
            >
              <ChevronDown className="w-3 h-3" />
            </button>

            {/* Select Dropdown Menu */}
            {showSelectMenu && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setShowSelectMenu(false)} />
                <div 
                  className="absolute top-8 left-0 z-40 w-36 py-1.5 rounded-lg shadow-xl border text-xs"
                  style={{
                    backgroundColor: 'var(--gmail-surface)',
                    borderColor: 'var(--gmail-border)',
                    color: 'var(--gmail-text)'
                  }}
                >
                  <button onClick={handleSelectAll} className="w-full text-left px-3 py-1.5 hover:bg-black/5 dark:hover:bg-white/10">All</button>
                  <button onClick={handleSelectNone} className="w-full text-left px-3 py-1.5 hover:bg-black/5 dark:hover:bg-white/10">None</button>
                  <button onClick={handleSelectRead} className="w-full text-left px-3 py-1.5 hover:bg-black/5 dark:hover:bg-white/10">Read</button>
                  <button onClick={handleSelectUnread} className="w-full text-left px-3 py-1.5 hover:bg-black/5 dark:hover:bg-white/10">Unread</button>
                  <button onClick={handleSelectStarred} className="w-full text-left px-3 py-1.5 hover:bg-black/5 dark:hover:bg-white/10">Starred</button>
                </div>
              </>
            )}
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleRefreshClick}
            className={`p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition ${isRefreshing ? 'animate-spin' : ''}`}
            title="Refresh"
          >
            <RotateCw className="w-4 h-4 text-slate-600 dark:text-slate-300" />
          </button>

          {/* Contextual Actions when items selected */}
          {selectedEmailIds.size > 0 ? (
            <div className="flex items-center space-x-1 pl-2 border-l" style={{ borderColor: 'var(--gmail-border)' }}>
              <button onClick={handleBatchArchive} className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="Archive">
                <Archive className="w-4 h-4" />
              </button>
              <button onClick={handleBatchDelete} className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="Delete">
                <Trash2 className="w-4 h-4 text-red-500" />
              </button>
              <button onClick={handleBatchMarkRead} className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="Mark as read">
                <MailOpen className="w-4 h-4" />
              </button>
              <button className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="Snooze">
                <Clock className="w-4 h-4" />
              </button>
              <span className="text-xs text-blue-600 dark:text-blue-400 font-semibold pl-2">
                {selectedEmailIds.size} selected
              </span>
            </div>
          ) : (
            <button className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="More">
              <MoreVertical className="w-4 h-4 text-slate-500" />
            </button>
          )}
        </div>

        {/* Right Pagination & Split Controls */}
        <div className="flex items-center space-x-3">
          
          {/* Pagination status */}
          <span className="text-xs font-mono text-slate-500">
            {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, filteredEmails.length)} of {filteredEmails.length}
          </span>

          {/* Prev / Next Arrows */}
          <div className="flex items-center space-x-0.5">
            <button
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
              className="p-1.5 rounded hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-30 disabled:pointer-events-none transition"
              title="Newer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
              className="p-1.5 rounded hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-30 disabled:pointer-events-none transition"
              title="Older"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Toggle Split Pane Mode (From user screenshot!) */}
          <div className="relative">
            <button
              onClick={() => setShowSplitMenu(!showSplitMenu)}
              className={`p-1.5 rounded flex items-center space-x-1 hover:bg-black/5 dark:hover:bg-white/10 border transition ${
                previewPaneMode !== 'none' ? 'border-blue-500/40 text-blue-600 dark:text-blue-400 bg-blue-500/10' : 'border-transparent text-slate-500'
              }`}
              title="Toggle split pane mode (Vertical / Horizontal / No Split)"
            >
              <Columns className="w-4 h-4" />
              <ChevronDown className="w-3 h-3" />
            </button>

            {showSplitMenu && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setShowSplitMenu(false)} />
                <div 
                  className="absolute top-8 right-0 z-40 w-44 py-1.5 rounded-xl shadow-xl border text-xs"
                  style={{
                    backgroundColor: 'var(--gmail-surface)',
                    borderColor: 'var(--gmail-border)',
                    color: 'var(--gmail-text)'
                  }}
                >
                  <div className="px-3 py-1 font-semibold text-[11px] text-slate-400 border-b" style={{ borderColor: 'var(--gmail-border)' }}>
                    Preview Pane Mode
                  </div>
                  <button 
                    onClick={() => { setPreviewPaneMode('none'); setShowSplitMenu(false); }}
                    className="w-full text-left px-3 py-2 flex items-center justify-between hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer"
                  >
                    <span>No split</span>
                    {previewPaneMode === 'none' && <Check className="w-3.5 h-3.5 text-blue-600" />}
                  </button>
                  <button 
                    onClick={() => { setPreviewPaneMode('vertical'); setShowSplitMenu(false); }}
                    className="w-full text-left px-3 py-2 flex items-center justify-between hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer"
                  >
                    <span>Vertical split</span>
                    {previewPaneMode === 'vertical' && <Check className="w-3.5 h-3.5 text-blue-600" />}
                  </button>
                  <button 
                    onClick={() => { setPreviewPaneMode('horizontal'); setShowSplitMenu(false); }}
                    className="w-full text-left px-3 py-2 flex items-center justify-between hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer"
                  >
                    <span>Horizontal split</span>
                    {previewPaneMode === 'horizontal' && <Check className="w-3.5 h-3.5 text-blue-600" />}
                  </button>
                </div>
              </>
            )}
          </div>

        </div>
      </div>

      {/* Gmail Category Tabs (Primary, BL Checks, SI Requests, Needs Review) */}
      <div 
        className="flex items-center px-4 border-b text-xs font-semibold select-none"
        style={{
          backgroundColor: 'var(--gmail-surface)',
          borderColor: 'var(--gmail-border)'
        }}
      >
        {[
          { id: 'primary', label: 'Primary', icon: Mail, count: emails.length },
          { id: 'bl', label: 'BL Checks', icon: FileCheck2, color: 'text-blue-600 dark:text-blue-400', count: 129 },
          { id: 'si', label: 'SI Requests', icon: FileText, color: 'text-green-600 dark:text-green-400', count: 141 },
          { id: 'review', label: 'Action Required', icon: AlertTriangle, color: 'text-amber-600 dark:text-amber-400', count: 34 }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setCurrentPage(1);
              }}
              className={`flex items-center space-x-2.5 px-6 py-3.5 border-b-2 transition-all cursor-pointer ${
                isActive
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400 font-bold'
                  : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-black/5 dark:hover:bg-white/5'
              }`}
            >
              <Icon className={`w-4 h-4 ${tab.color || ''}`} />
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-semibold ${
                  isActive ? 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Main Inbox Body: Split Pane or Single List */}
      <div className={`flex-1 flex ${previewPaneMode === 'horizontal' ? 'flex-col' : 'flex-row'} overflow-hidden`}>
        
        {/* Email List Column */}
        <div 
          className={`overflow-y-auto ${
            previewPaneMode === 'vertical' 
              ? 'w-1/2 min-w-[360px] max-w-[50%] border-r' 
              : previewPaneMode === 'horizontal' 
              ? 'h-1/2 border-b' 
              : 'w-full'
          }`}
          style={{
            borderColor: 'var(--gmail-border)'
          }}
        >
          {paginatedEmails.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-slate-400">
              <Mail className="w-12 h-12 stroke-[1] mb-2 text-slate-300 dark:text-slate-600" />
              <p className="text-sm font-medium">No conversations in this view</p>
            </div>
          ) : (
            paginatedEmails.map((email) => {
              const isSelected = selectedEmailId === email.id;
              const isChecked = selectedEmailIds.has(email.id);
              const isStarred = starredEmailIds.has(email.id);
              const isImportant = importantEmailIds.has(email.id);
              const isRead = readEmailIds.has(email.id);
              const category = email.classification?.category || 'GENERAL';
              const verif = email.verification;

              return (
                <div
                  key={email.id}
                  onClick={() => handleEmailClick(email.id)}
                  className={`group relative flex items-center px-4 py-2.5 border-b cursor-pointer transition-colors text-xs ${
                    isSelected 
                      ? 'font-medium' 
                      : !isRead 
                      ? 'font-semibold text-slate-900 dark:text-slate-100' 
                      : 'text-slate-600 dark:text-slate-400'
                  } hover:brightness-95`}
                  style={{
                    backgroundColor: isSelected 
                      ? 'var(--gmail-active-pill)' 
                      : !isRead 
                      ? 'var(--gmail-surface)' 
                      : 'var(--gmail-card-beige)',
                    borderColor: 'var(--gmail-border)'
                  }}
                >
                  {/* Left icons: Checkbox, Star, Important */}
                  <div className="flex items-center space-x-1.5 shrink-0 mr-3">
                    <button
                      onClick={(e) => toggleSelect(e, email.id)}
                      className="p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 text-slate-400"
                    >
                      {isChecked ? (
                        <CheckSquare className="w-4 h-4 text-blue-600" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-300 dark:text-slate-600" />
                      )}
                    </button>

                    <button
                      onClick={(e) => toggleStar(e, email.id)}
                      className="p-1 rounded hover:bg-black/10 dark:hover:bg-white/10"
                    >
                      <Star className={`w-4 h-4 ${isStarred ? 'fill-amber-400 text-amber-400' : 'text-slate-300 dark:text-slate-600'}`} />
                    </button>

                    <button
                      onClick={(e) => toggleImportant(e, email.id)}
                      className="p-1 rounded hover:bg-black/10 dark:hover:bg-white/10"
                    >
                      <Bookmark className={`w-3.5 h-3.5 ${isImportant ? 'fill-amber-500 text-amber-500' : 'text-slate-300 dark:text-slate-600'}`} />
                    </button>
                  </div>

                  {/* Sender Name */}
                  <div className={`w-36 shrink-0 truncate ${!isRead ? 'font-bold text-slate-900 dark:text-slate-100' : 'text-slate-700 dark:text-slate-300'}`}>
                    {email.company || email.sender.split('@')[0]}
                  </div>

                  {/* Badges, Subject & Snippet */}
                  <div className="flex-1 flex items-center min-w-0 pr-4 space-x-2">
                    
                    {/* Category Label Chip */}
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold shrink-0 ${
                      category === 'BL_COMPARISON' ? 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300' :
                      category === 'SI_REQUEST' ? 'bg-green-100 dark:bg-green-950/60 text-green-700 dark:text-green-300' :
                      category === 'INVOICE_QUERY' ? 'bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300' :
                      category === 'SPAM' ? 'bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300' :
                      'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                    }`}>
                      {category.replace('_', ' ')}
                    </span>

                    {/* Verification Status Pill */}
                    {verif?.status === 'OK' && (
                      <span className="px-2 py-0.2 rounded-full text-[10px] font-mono font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 shrink-0">
                        MATCHED
                      </span>
                    )}
                    {verif?.status === 'MISMATCH' && (
                      <span className="px-2 py-0.2 rounded-full text-[10px] font-mono font-bold bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 shrink-0">
                        MISMATCH ({verif.defect_fields?.length || 0})
                      </span>
                    )}
                    {verif?.status === 'NEEDS_REVIEW' && (
                      <span className="px-2 py-0.2 rounded-full text-[10px] font-mono font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 shrink-0">
                        REVIEW
                      </span>
                    )}

                    {/* Subject Line & Snippet */}
                    <span className={`truncate ${!isRead ? 'font-semibold text-slate-900 dark:text-slate-100' : 'text-slate-700 dark:text-slate-300'}`}>
                      {email.subject}
                    </span>
                    <span className="text-slate-400 dark:text-slate-500 truncate shrink-0">
                      — {email.id} {email.vessel ? `· Vessel: ${email.vessel}` : ''}
                    </span>

                    {/* Attachments */}
                    {email.attachments && email.attachments.length > 0 && (
                      <span className="flex items-center space-x-1 shrink-0 px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 text-[11px]" title={`${email.attachments.length} attachments`}>
                        <Paperclip className="w-3 h-3" />
                        <span className="font-mono">{email.attachments.length}</span>
                      </span>
                    )}
                  </div>

                  {/* Right: Timestamp or Hover Actions (Standard Gmail behavior) */}
                  <div className="shrink-0 flex items-center justify-end pl-2">
                    
                    {/* Timestamp (Hidden on hover) */}
                    <span className="font-mono text-slate-500 text-[11px] group-hover:hidden">
                      {new Date(email.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>

                    {/* Quick Actions (Shown on hover) */}
                    <div className="hidden group-hover:flex items-center space-x-1" onClick={(e) => e.stopPropagation()}>
                      <button 
                        onClick={() => {
                          if (showToast) showToast(`Archived ${email.id}`, 'info');
                        }}
                        className="p-1 rounded-full hover:bg-black/10 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300" 
                        title="Archive"
                      >
                        <Archive className="w-3.5 h-3.5" />
                      </button>
                      <button 
                        onClick={() => {
                          if (showToast) showToast(`Moved ${email.id} to Trash`, 'warning');
                        }}
                        className="p-1 rounded-full hover:bg-black/10 dark:hover:bg-white/10 text-red-500" 
                        title="Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                      <button 
                        onClick={() => {
                          const next = new Set(readEmailIds);
                          if (next.has(email.id)) next.delete(email.id); else next.add(email.id);
                          setReadEmailIds(next);
                        }}
                        className="p-1 rounded-full hover:bg-black/10 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300" 
                        title={isRead ? "Mark as unread" : "Mark as read"}
                      >
                        {isRead ? <Mail className="w-3.5 h-3.5" /> : <MailOpen className="w-3.5 h-3.5" />}
                      </button>
                      <button className="p-1 rounded-full hover:bg-black/10 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300" title="Snooze">
                        <Clock className="w-3.5 h-3.5" />
                      </button>
                    </div>

                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Reading / Preview Pane (Active when split mode enabled) */}
        {previewPaneMode !== 'none' && (
          <div 
            className={`flex-1 flex flex-col overflow-hidden ${
              previewPaneMode === 'vertical' ? 'w-1/2' : 'h-1/2'
            }`}
            style={{
              backgroundColor: 'var(--gmail-surface)'
            }}
          >
            {selectedEmail ? (
              <div className="flex-1 flex flex-col h-full overflow-hidden">
                
                {/* Reading Pane Header Bar */}
                <div className="px-6 py-3 border-b flex items-center justify-between select-none" style={{ borderColor: 'var(--gmail-border)' }}>
                  <div className="flex items-center space-x-2">
                    <button className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300" title="Archive">
                      <Archive className="w-4 h-4" />
                    </button>
                    <button className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-red-500" title="Delete">
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <button className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300" title="Mark as unread">
                      <Mail className="w-4 h-4" />
                    </button>
                    <button className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300" title="Snooze">
                      <Clock className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="flex items-center space-x-1 text-slate-500">
                    <button className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="Print">
                      <Printer className="w-4 h-4" />
                    </button>
                    <button 
                      onClick={onOpenInspector}
                      className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-blue-600 dark:text-blue-400" 
                      title="Open full SI/BL inspector"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Email Content Body */}
                <div className="flex-1 overflow-y-auto p-6 space-y-5">
                  
                  {/* Subject Line & Classification Badges */}
                  <div>
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <h2 className="text-xl font-normal text-slate-900 dark:text-slate-100 tracking-tight" style={{ fontFamily: 'Google Sans, Roboto, sans-serif' }}>
                        {selectedEmail.subject}
                      </h2>
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 font-bold border border-blue-500/20 shrink-0">
                        {selectedEmail.id}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded text-xs font-mono font-semibold bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300">
                        {selectedEmail.classification?.category || 'GENERAL'}
                      </span>
                      {selectedEmail.company && (
                        <span className="px-2.5 py-0.5 rounded text-xs bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 font-medium">
                          {selectedEmail.company}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Sender Details Header */}
                  <div className="flex items-center justify-between pb-4 border-b" style={{ borderColor: 'var(--gmail-border)' }}>
                    <div className="flex items-center space-x-3">
                      {/* Avatar */}
                      <div className="w-10 h-10 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-sm shadow-xs">
                        {selectedEmail.sender[0].toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                            {selectedEmail.company || selectedEmail.sender.split('@')[0]}
                          </span>
                          <span className="text-xs text-slate-500">
                            &lt;{selectedEmail.sender}&gt;
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 flex items-center space-x-1">
                          <span>to me</span>
                          <ChevronDown className="w-3 h-3" />
                        </div>
                      </div>
                    </div>

                    <div className="text-xs text-slate-500 font-mono flex items-center space-x-2">
                      <span>{new Date(selectedEmail.timestamp).toLocaleString()}</span>
                      <Star className="w-4 h-4 text-slate-300 hover:text-amber-400 cursor-pointer" />
                      <Reply className="w-4 h-4 text-slate-400 hover:text-blue-600 cursor-pointer" />
                    </div>
                  </div>

                  {/* AI Maritime Triage & Discrepancy Gate Banner */}
                  <div className={`p-4 rounded-2xl border transition-all ${
                    selectedEmail.verification?.status === 'MISMATCH'
                      ? 'bg-rose-50/60 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/60'
                      : selectedEmail.verification?.status === 'OK'
                      ? 'bg-emerald-50/60 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/60'
                      : 'bg-amber-50/60 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900/60'
                  }`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Sparkles className={`w-4 h-4 ${
                          selectedEmail.verification?.status === 'MISMATCH' ? 'text-rose-600' :
                          selectedEmail.verification?.status === 'OK' ? 'text-emerald-600' : 'text-amber-600'
                        }`} />
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                          Averish AI Maritime Verification Gate
                        </span>
                      </div>
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded-full font-bold bg-white dark:bg-black/40 shadow-2xs">
                        98.8% Model Confidence
                      </span>
                    </div>

                    <p className="text-xs text-slate-700 dark:text-slate-300 mb-3">
                      {selectedEmail.verification?.status === 'MISMATCH' && (
                        <span>⚠️ Discrepancy detected between Shipping Instruction (SI) and Draft Bill of Lading (BL) across {selectedEmail.verification?.defect_fields?.length || 0} fields.</span>
                      )}
                      {selectedEmail.verification?.status === 'OK' && (
                        <span>✓ Verified: All 7 critical maritime trade fields match exactly between SI and BL documents.</span>
                      )}
                      {selectedEmail.verification?.status === 'NEEDS_REVIEW' && (
                        <span>⚠️ Automated review needed: {selectedEmail.verification?.review_reason || 'Gate condition triggered'}.</span>
                      )}
                    </p>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={onOpenInspector}
                        className="px-4 py-1.5 rounded-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
                      >
                        Inspect SI vs BL Diff
                      </button>
                      <button
                        onClick={onOpenOverrideModal}
                        className="px-4 py-1.5 rounded-full border border-slate-300 dark:border-slate-700 text-xs font-semibold hover:bg-black/5 dark:hover:bg-white/5 transition cursor-pointer"
                      >
                        Human Override
                      </button>
                    </div>
                  </div>

                  {/* Extracted Shipping Summary */}
                  {selectedEmail.vessel && (
                    <div 
                      className="grid grid-cols-3 gap-3 p-3.5 rounded-xl border text-xs" 
                      style={{ 
                        backgroundColor: 'var(--gmail-card-beige)',
                        borderColor: 'var(--gmail-border)' 
                      }}
                    >
                      <div>
                        <span className="text-slate-400 block text-[10px] font-semibold uppercase">Vessel Name</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedEmail.vessel}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] font-semibold uppercase">Booking Ref</span>
                        <span className="font-mono text-slate-800 dark:text-slate-200 font-semibold">{selectedEmail.id}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] font-semibold uppercase">Client / Shipper</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedEmail.company || 'Standard Carrier'}</span>
                      </div>
                    </div>
                  )}

                  {/* Main Email Body Text */}
                  <div className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-sans whitespace-pre-wrap py-2">
                    {emailDetail?.body || `Dear Shipping Operations Team,\n\nPlease find attached the Shipping Instruction (SI) and draft Bill of Lading (BL) for booking reference ${selectedEmail.id}.\n\nKindly review and confirm the cargo description, container tare weights, and ports before vessel departure.\n\nBest regards,\n${selectedEmail.company || selectedEmail.sender}\nLogistics & Documentation Desk`}
                  </div>

                  {/* Gmail Attachment Cards */}
                  {selectedEmail.attachments && selectedEmail.attachments.length > 0 && (
                    <div className="pt-4 border-t" style={{ borderColor: 'var(--gmail-border)' }}>
                      <div className="text-xs font-semibold text-slate-500 mb-3 flex items-center space-x-1.5">
                        <Paperclip className="w-3.5 h-3.5" />
                        <span>{selectedEmail.attachments.length} Attachments</span>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        {selectedEmail.attachments.map((file, idx) => (
                          <div 
                            key={idx}
                            className="p-3 rounded-xl border flex items-center space-x-3 hover:shadow-sm transition cursor-pointer group"
                            style={{ 
                              backgroundColor: 'var(--gmail-card-beige)',
                              borderColor: 'var(--gmail-border)' 
                            }}
                            onClick={onOpenInspector}
                          >
                            <div className="w-9 h-9 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                              <FileText className="w-5 h-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate group-hover:text-blue-600 transition">
                                {file}
                              </p>
                              <span className="text-[10px] text-slate-400 font-mono">
                                42 KB · Verified Attachment
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Reply / Forward Pill Buttons */}
                  <div className="flex items-center space-x-3 pt-6">
                    <button className="flex items-center space-x-2 px-6 py-2.5 rounded-full border border-slate-300 dark:border-slate-700 text-xs font-semibold hover:bg-black/5 dark:hover:bg-white/5 transition">
                      <Reply className="w-4 h-4 text-slate-500" />
                      <span>Reply</span>
                    </button>
                    <button className="flex items-center space-x-2 px-6 py-2.5 rounded-full border border-slate-300 dark:border-slate-700 text-xs font-semibold hover:bg-black/5 dark:hover:bg-white/5 transition">
                      <Forward className="w-4 h-4 text-slate-500" />
                      <span>Forward</span>
                    </button>
                  </div>

                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-400">
                <Mail className="w-12 h-12 stroke-[1] mb-2 text-slate-300 dark:text-slate-600" />
                <p className="text-sm font-medium">No conversation selected</p>
                <p className="text-xs text-slate-500">Pick an email from the list to view</p>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
