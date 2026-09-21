import React, { useState } from 'react';
import { 
  Inbox, 
  Star, 
  Clock, 
  Send, 
  FileText, 
  ChevronDown, 
  ChevronUp, 
  Bookmark, 
  AlertOctagon, 
  Trash2, 
  Mail, 
  Plus, 
  Tag, 
  Ship, 
  Calendar as CalendarIcon, 
  FileCheck2, 
  AlertTriangle, 
  BarChart3, 
  Award, 
  GitGraph,
  Sparkles,
  Cloud
} from 'lucide-react';

export default function GmailSidebar({
  activeTab,
  setActiveTab,
  selectedCategory,
  setSelectedCategory,
  stats,
  collapsed,
  onOpenCompose,
  starredCount = 12,
  draftsCount = 4
}) {
  const [showMore, setShowMore] = useState(false);

  // Main Gmail standard folders
  const standardFolders = [
    { id: 'inbox', label: 'Inbox', icon: Inbox, count: stats?.total_emails || 410, isCategory: false },
    { id: 'starred', label: 'Starred', icon: Star, count: starredCount, isCategory: false },
    { id: 'snoozed', label: 'Snoozed', icon: Clock, isCategory: false },
    { id: 'sent', label: 'Sent', icon: Send, isCategory: false },
    { id: 'drafts', label: 'Drafts', icon: FileText, count: draftsCount, isCategory: false },
  ];

  const moreFolders = [
    { id: 'important', label: 'Important', icon: Bookmark },
    { id: 'all_mail', label: 'All Mail', icon: Mail, count: stats?.total_emails || 410 },
    { id: 'spam', label: 'Spam', icon: AlertOctagon, count: stats?.spam_count || 37 },
    { id: 'trash', label: 'Trash', icon: Trash2 },
  ];

  // Shipping labels with Gmail colored dots
  const shippingLabels = [
    { id: 'BL_COMPARISON', label: 'BL Checks', color: '#4285F4', count: stats?.comparison_requests || 129 },
    { id: 'SI_REQUEST', label: 'SI Requests', color: '#34A853', count: stats?.si_requests || 141 },
    { id: 'INVOICE_QUERY', label: 'Invoices & Queries', color: '#A142F4', count: stats?.invoice_queries || 83 },
    { id: 'GENERAL', label: 'General Operations', color: '#70757a', count: 130 },
  ];

  // Dedicated Freight Workspace Views
  const workspaceApps = [
    { id: 'timeline', label: 'Shipment Timeline', icon: GitGraph, badge: 'Matrix' },
    { id: 'inspector', label: 'SI vs BL Inspector', icon: FileCheck2 },
    { id: 'calendar', label: 'Vessel Calendar', icon: CalendarIcon },
    { id: 'human_review', label: 'Review Queue', icon: AlertTriangle, count: stats?.human_review_count || 34, isAlert: true },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'benchmark', label: 'Self-Evaluation', icon: Award },
  ];

  const isFolderActive = (id) => {
    if (activeTab === 'inbox') {
      if (id === 'inbox' && selectedCategory === 'ALL') return true;
      if (id === selectedCategory) return true;
    }
    return activeTab === id;
  };

  const handleFolderClick = (id, isCategory = false) => {
    if (isCategory) {
      setActiveTab('inbox');
      setSelectedCategory(id);
    } else if (id === 'inbox') {
      setActiveTab('inbox');
      setSelectedCategory('ALL');
    } else if (['timeline', 'inspector', 'calendar', 'human_review', 'analytics', 'benchmark'].includes(id)) {
      setActiveTab(id);
    } else {
      // Generic folder view
      setActiveTab('inbox');
      setSelectedCategory(id);
    }
  };

  return (
    <aside 
      className={`h-[calc(100vh-4rem)] flex flex-col justify-between select-none transition-all duration-200 border-r ${
        collapsed ? 'w-18' : 'w-64 min-w-[16rem]'
      }`}
      style={{
        backgroundColor: 'var(--gmail-bg)',
        borderColor: 'var(--gmail-border)'
      }}
    >
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-4 no-scrollbar">
        
        {/* Floating Google "+ Compose" Button */}
        <div className="pt-2 pb-2">
          <button
            onClick={onOpenCompose}
            className={`flex items-center space-x-3 rounded-2xl transition-all duration-200 shadow-sm hover:shadow-md cursor-pointer ${
              collapsed 
                ? 'w-12 h-12 justify-center p-0 mx-auto' 
                : 'px-6 py-4'
            }`}
            style={{
              backgroundColor: 'var(--gmail-compose-bg)',
              color: 'var(--gmail-compose-text)'
            }}
            title="Compose message"
          >
            {/* Colorful Google Plus Icon */}
            <div className="w-5 h-5 flex items-center justify-center shrink-0">
              <svg viewBox="0 0 36 36" className="w-5 h-5">
                <path fill="#4285F4" d="M16 16v14h4V16h14v-4H20V-2h-4v14H2v4h14z" />
                <path fill="#34A853" d="M30 16H20l-4-4h14v4z" />
                <path fill="#FBBC05" d="M6 16h10v4H6z" />
                <path fill="#EA4335" d="M20 16v10h-4V16h4z" />
              </svg>
            </div>
            {!collapsed && (
              <span className="text-sm font-semibold tracking-wide" style={{ fontFamily: 'Google Sans, Roboto, sans-serif' }}>
                Compose
              </span>
            )}
          </button>
        </div>

        {/* Standard Navigation Folders */}
        <div className="space-y-0.5">
          {standardFolders.map((folder) => {
            const Icon = folder.icon;
            const active = isFolderActive(folder.id);
            return (
              <button
                key={folder.id}
                onClick={() => handleFolderClick(folder.id, folder.isCategory)}
                className={`w-full flex items-center justify-between px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  active
                    ? 'font-bold'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-black/5 dark:hover:bg-white/5'
                }`}
                style={active ? {
                  backgroundColor: 'var(--gmail-active-pill)',
                  color: 'var(--gmail-active-pill-text)'
                } : {}}
                title={folder.label}
              >
                <div className="flex items-center space-x-4 min-w-0">
                  <Icon className={`w-4 h-4 shrink-0 ${active ? 'fill-current' : ''}`} />
                  {!collapsed && <span className="truncate">{folder.label}</span>}
                </div>
                {!collapsed && folder.count !== undefined && (
                  <span className={`text-xs font-mono font-semibold ${active ? 'text-blue-700 dark:text-blue-300' : 'text-slate-500'}`}>
                    {folder.count}
                  </span>
                )}
              </button>
            );
          })}

          {/* More / Less Folders Accordion */}
          {!collapsed && (
            <>
              {showMore && (
                <div className="space-y-0.5 pt-0.5">
                  {moreFolders.map((folder) => {
                    const Icon = folder.icon;
                    const active = isFolderActive(folder.id);
                    return (
                      <button
                        key={folder.id}
                        onClick={() => handleFolderClick(folder.id, true)}
                        className={`w-full flex items-center justify-between px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                          active
                            ? 'font-bold'
                            : 'text-slate-700 dark:text-slate-300 hover:bg-black/5 dark:hover:bg-white/5'
                        }`}
                        style={active ? {
                          backgroundColor: 'var(--gmail-active-pill)',
                          color: 'var(--gmail-active-pill-text)'
                        } : {}}
                      >
                        <div className="flex items-center space-x-4 min-w-0">
                          <Icon className="w-4 h-4 shrink-0" />
                          <span className="truncate">{folder.label}</span>
                        </div>
                        {folder.count !== undefined && (
                          <span className="text-xs font-mono text-slate-500">
                            {folder.count}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}

              <button
                onClick={() => setShowMore(!showMore)}
                className="w-full flex items-center space-x-4 px-4 py-2 rounded-full text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
              >
                {showMore ? <ChevronUp className="w-4 h-4 shrink-0" /> : <ChevronDown className="w-4 h-4 shrink-0" />}
                <span>{showMore ? 'Less' : 'More'}</span>
              </button>
            </>
          )}
        </div>

        {/* Labels Section (Gmail Category Labels) */}
        {!collapsed && (
          <div className="pt-2 border-t" style={{ borderColor: 'var(--gmail-border)' }}>
            <div className="px-4 py-1.5 flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              <span>Labels</span>
              <button className="p-1 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-slate-500" title="Create label">
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>
            
            <div className="space-y-0.5">
              {shippingLabels.map((lbl) => {
                const active = activeTab === 'inbox' && selectedCategory === lbl.id;
                return (
                  <button
                    key={lbl.id}
                    onClick={() => handleFolderClick(lbl.id, true)}
                    className={`w-full flex items-center justify-between px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                      active
                        ? 'font-bold'
                        : 'text-slate-700 dark:text-slate-300 hover:bg-black/5 dark:hover:bg-white/5'
                    }`}
                    style={active ? {
                      backgroundColor: 'var(--gmail-active-pill)',
                      color: 'var(--gmail-active-pill-text)'
                    } : {}}
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <span 
                        className="w-3 h-3 rounded-sm shrink-0 shadow-sm"
                        style={{ backgroundColor: lbl.color }}
                      />
                      <span className="truncate text-xs">{lbl.label}</span>
                    </div>
                    <span className="text-[11px] font-mono text-slate-500 font-semibold">
                      {lbl.count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Workspace Applications Section */}
        {!collapsed && (
          <div className="pt-2 border-t" style={{ borderColor: 'var(--gmail-border)' }}>
            <div className="px-4 py-1.5 flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              <span>Freight Workspace</span>
            </div>

            <div className="space-y-0.5">
              {workspaceApps.map((app) => {
                const Icon = app.icon;
                const active = activeTab === app.id;
                return (
                  <button
                    key={app.id}
                    onClick={() => setActiveTab(app.id)}
                    className={`w-full flex items-center justify-between px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                      active
                        ? 'font-bold'
                        : 'text-slate-700 dark:text-slate-300 hover:bg-black/5 dark:hover:bg-white/5'
                    }`}
                    style={active ? {
                      backgroundColor: 'var(--gmail-active-pill)',
                      color: 'var(--gmail-active-pill-text)'
                    } : {}}
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500'}`} />
                      <span className="truncate text-xs">{app.label}</span>
                    </div>

                    {app.badge && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded font-mono font-bold bg-violet-500/20 text-violet-600 dark:text-violet-400 border border-violet-500/30">
                        {app.badge}
                      </span>
                    )}

                    {app.count !== undefined && (
                      <span className={`text-[11px] px-1.5 py-0.2 rounded-full font-mono font-bold ${
                        app.isAlert 
                          ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30' 
                          : 'text-slate-500'
                      }`}>
                        {app.count}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

      </div>

      {/* Gmail Storage Footer */}
      {!collapsed && (
        <div className="p-4 border-t text-xs text-slate-500 dark:text-slate-400 space-y-2" style={{ borderColor: 'var(--gmail-border)' }}>
          <div className="flex items-center justify-between">
            <span className="flex items-center space-x-1.5 font-medium">
              <Cloud className="w-3.5 h-3.5 text-blue-500" />
              <span>1.42 GB of 15 GB used</span>
            </span>
            <span className="text-[10px] text-blue-600 dark:text-blue-400 font-semibold cursor-pointer hover:underline">Manage</span>
          </div>
          <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div className="h-full bg-blue-600 rounded-full w-[12%]" />
          </div>
          <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1">
            <span>DocuMatch AI</span>
            <span className="font-mono text-emerald-500 font-semibold">● Online</span>
          </div>
        </div>
      )}
    </aside>
  );
}
