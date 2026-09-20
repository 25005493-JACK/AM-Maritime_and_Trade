import React from 'react';
import { 
  Inbox, 
  FileCheck2, 
  AlertTriangle, 
  BarChart3, 
  Award, 
  Ship, 
  RefreshCw,
  Calendar as CalendarIcon,
  FileSpreadsheet,
  GitGraph,
  ScanText
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, stats, onRefresh }) {
  const navItems = [
    { id: 'inbox', label: 'Inbox & Triage', icon: Inbox, count: stats?.total_emails },
    { id: 'inspector', label: 'SI vs BL Inspector', icon: FileCheck2, count: stats?.comparison_requests },
    { id: 'timeline', label: 'Shipment Timeline', icon: GitGraph, badgeColor: 'bg-violet-500/20 text-violet-300 border-violet-500/30' },
    { id: 'calendar', label: 'Vessel Schedule Calendar', icon: CalendarIcon, badgeColor: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' },
    { id: 'human_review', label: 'Human Review Queue', icon: AlertTriangle, count: stats?.human_review_count, badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
    { id: 'analytics', label: 'Vessel & Order Analytics', icon: BarChart3 },
    { id: 'ocr_dashboard', label: 'PDF OCR Dashboard', icon: ScanText },
    { id: 'benchmark', label: 'Self-Evaluation Scoreboard', icon: Award }
  ];

  return (
    <aside className="w-64 min-w-[16rem] glass-panel border-r border-slate-800 flex flex-col justify-between h-screen select-none">
      <div>
        {/* Brand Header */}
        <div className="p-4 border-b border-slate-800/80 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-900/30">
            <Ship className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-100 tracking-tight leading-none">Averish AI</h1>
            <span className="text-xs text-cyan-400 font-medium tracking-wide">Maritime & Trade Platform</span>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-600/20 to-blue-600/20 text-cyan-300 border border-cyan-500/30 shadow-md shadow-cyan-950/40'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
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
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="font-mono text-slate-300">FastAPI & React Server</span>
          </div>
          <button 
            onClick={onRefresh}
            title="Refresh dataset"
            className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-cyan-400 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="text-[11px] text-slate-500 font-mono">
          Services: SI/BL, LC Checking, Calendar
        </div>
      </div>
    </aside>
  );
}
