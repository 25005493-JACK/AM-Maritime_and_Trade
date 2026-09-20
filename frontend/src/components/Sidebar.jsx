import React from 'react';
import { 
  Inbox, 
  BriefcaseBusiness,
  FileCheck2, 
  AlertTriangle, 
  BarChart3, 
  Award, 
  Ship, 
  RefreshCw,
  Calendar as CalendarIcon,
  GitGraph,
  ScanText,
  Sun,
  Moon
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, stats, isRefreshing, onRefresh, theme, onToggleTheme }) {
  const navItems = [
    { id: 'inbox', label: 'Inbox & Triage', icon: Inbox, count: stats?.total_emails },
    { id: 'workspace', label: 'Shipment Workspace', icon: BriefcaseBusiness, badgeColor: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
    { id: 'inspector', label: 'SI vs BL Inspector', icon: FileCheck2, count: stats?.comparison_requests },
    { id: 'timeline', label: 'Shipment Timeline', icon: GitGraph, badgeColor: 'bg-violet-500/20 text-violet-300 border-violet-500/30' },
    { id: 'calendar', label: 'Vessel Schedule Calendar', icon: CalendarIcon, badgeColor: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
    { id: 'human_review', label: 'Human Review Queue', icon: AlertTriangle, count: stats?.human_review_count, badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
    { id: 'analytics', label: 'Vessel & Order Analytics', icon: BarChart3 },
    { id: 'ocr_dashboard', label: 'PDF OCR Dashboard', icon: ScanText },
    { id: 'benchmark', label: 'Self-Evaluation Scoreboard', icon: Award }
  ];

  return (
    <aside className="w-56 min-w-[14rem] glass-panel border-r border-slate-800 flex flex-col justify-between h-dvh select-none">
      <div>
        {/* Brand Header */}
        <div className="p-3.5 border-b border-slate-800/80 flex items-center space-x-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-900/30 shrink-0">
            <Ship className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-100 tracking-tight leading-none">Averish AI</h1>
            <span className="text-[11px] text-cyan-400 font-medium tracking-wide">Maritime & Trade Platform</span>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="p-2.5 space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                title={item.label}
                className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-600/20 to-blue-600/20 text-cyan-300 border border-cyan-500/30 shadow-md shadow-cyan-950/40'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                <div className="flex items-center space-x-2.5 min-w-0">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span className="truncate">{item.label}</span>
                </div>
                {item.count !== undefined && (
                  <span className={`text-xs px-2 py-0.5 rounded-full font-mono font-semibold border ${
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

      {/* System Status Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/40">
        <button
          type="button"
          onClick={onToggleTheme}
          aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
          aria-pressed={theme === 'light'}
          className="mb-4 flex w-full items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:bg-slate-700/70"
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          {theme === 'dark' ? 'Light theme' : 'Dark theme'}
        </button>
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="font-mono text-slate-300">FastAPI & React Server</span>
          </div>
          <button 
            onClick={onRefresh}
            title={isRefreshing ? 'Refreshing dataset' : 'Refresh dataset'}
            aria-label={isRefreshing ? 'Refreshing dataset' : 'Refresh dataset'}
            disabled={isRefreshing}
            className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-cyan-400 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
        <div className="text-[11px] text-slate-500 font-mono">
          Services: SI/BL, LC Checking, Calendar
        </div>
      </div>
    </aside>
  );
}
