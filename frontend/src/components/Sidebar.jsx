import React, { useState } from 'react';
import { 
  Inbox, 
  AlertTriangle, 
  Calendar as CalendarIcon, 
  ShieldCheck, 
  Ship, 
  ChevronLeft, 
  ChevronRight,
  Sun,
  Moon,
  RefreshCw
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, stats, healthInfo, onRefresh, theme, onToggleTheme, onOpenUpload, emails = [] }) {
  const [collapsed, setCollapsed] = useState(false);

  // Dynamic live email count & human review count matching top workspace headers
  const liveTotalCount = emails.length > 0 ? emails.length : (stats?.total_emails || 0);

  const liveHumanReviewCount = emails.length > 0
    ? emails.filter((e) => {
        const status = e.verification?.status;
        if (status === 'OK' || status === 'Approved' || status === 'Passed' || status === 'Completed') {
          return false;
        }
        const hasReason = e.verification?.review_reason || (e.verification?.human_review_reasons && e.verification.human_review_reasons.length > 0);
        return status === 'HUMAN_REVIEW_REQUIRED' || status === 'NEEDS_REVIEW' || hasReason;
      }).length
    : (stats?.human_review_count || 0);

  const navItems = [
    { 
      id: 'inbox', 
      label: 'Inbox', 
      icon: Inbox, 
      count: liveTotalCount,
      badgeColor: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
    },
    { 
      id: 'human_review', 
      label: 'Human Review Queue', 
      icon: AlertTriangle, 
      count: liveHumanReviewCount, 
      badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30' 
    },
    { 
      id: 'calendar', 
      label: 'Vessel Schedule Calendar', 
      icon: CalendarIcon, 
      badgeColor: 'bg-blue-500/20 text-blue-300 border-blue-500/30' 
    },
    { 
      id: 'admin', 
      label: 'Admin', 
      icon: ShieldCheck, 
      badgeColor: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30' 
    }
  ];

  return (
    <aside 
      className={`glass-panel border-r border-blue-900/60 bg-slate-950 flex flex-col justify-between h-screen select-none transition-all duration-300 relative z-20 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      <div>
        {/* Brand Header */}
        <div className={`p-4 border-b border-blue-900/60 flex items-center ${collapsed ? 'justify-center' : 'justify-between'}`}>
          {!collapsed ? (
            <>
              <div className="flex items-center space-x-3 overflow-hidden min-w-0">
                <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shrink-0 shadow-md">
                  <Ship className="w-6 h-6 text-white" />
                </div>
                <div className="min-w-0">
                  <h1 className="text-base font-extrabold text-slate-100 tracking-tight leading-none truncate">
                    DocuMatch
                  </h1>
                  <span className="text-[11px] text-cyan-400 font-medium tracking-wide">
                    Maritime & Trade
                  </span>
                </div>
              </div>
              <button
                onClick={() => setCollapsed(true)}
                title="Collapse Sidebar"
                className="p-1.5 rounded-lg bg-blue-950/80 hover:bg-blue-900 text-slate-300 hover:text-cyan-400 border border-blue-800/60 transition shrink-0 ml-2 cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </>
          ) : (
            <button
              onClick={() => setCollapsed(false)}
              title="Expand Sidebar"
              className="w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-500 flex items-center justify-center shadow-lg shadow-cyan-950/50 transition relative group cursor-pointer"
            >
              <Ship className="w-5 h-5 text-white group-hover:hidden" />
              <ChevronRight className="w-5 h-5 text-white hidden group-hover:block" />
            </button>
          )}
        </div>

        {/* Centralized Workspace Section Header */}
        <div className="py-2.5 px-3 border-b border-blue-900/40 bg-blue-950/30 text-center">
          {collapsed ? (
            <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-mono block text-center">
              WS
            </span>
          ) : (
            <span className="text-xs font-bold uppercase tracking-widest text-cyan-400 font-mono block text-center">
              Workspace
            </span>
          )}
        </div>


        {/* Navigation Options */}
        <nav className="p-3 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                title={collapsed ? item.label : undefined}
                className={`w-full flex items-center ${
                  collapsed ? 'justify-center py-3' : 'justify-between px-3 py-3'
                } rounded-xl text-xs font-bold transition-all duration-200 cursor-pointer ${
                  isActive
                    ? 'bg-blue-900/80 text-cyan-300 border border-cyan-500/50 shadow-lg shadow-cyan-950/60'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-blue-950/50 border border-transparent'
                }`}
              >
                <div className={`flex items-center ${!collapsed ? 'space-x-3' : 'justify-center'}`}>
                  <Icon className={`${collapsed ? 'w-5 h-5' : 'w-4 h-4'} ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  {!collapsed && <span>{item.label}</span>}
                </div>
                {!collapsed && item.count !== undefined && item.count > 0 && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-extrabold border ${
                    item.badgeColor || (isActive ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' : 'bg-slate-800 text-slate-400 border-slate-700')
                  }`}>
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Footer Controls & LLM Mode Status */}
      <div className="p-3 border-t border-blue-900/60 bg-blue-950/20 space-y-2.5">


        <div className={`flex items-center ${collapsed ? 'justify-center flex-col space-y-2' : 'justify-between'} text-xs text-slate-400`}>
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              <span className="font-mono text-[11px] text-slate-300 font-semibold">Online</span>
            </div>
          )}
          <div className="flex items-center space-x-1">
            <button
              onClick={onToggleTheme}
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Theme`}
              className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-cyan-400 border border-slate-800 transition cursor-pointer"
            >
              {theme === 'dark' ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-indigo-400" />}
            </button>
            <button 
              onClick={onRefresh}
              title="Refresh Data"
              className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-cyan-400 border border-slate-800 transition cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
