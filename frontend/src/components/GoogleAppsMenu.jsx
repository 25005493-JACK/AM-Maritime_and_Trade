import React from 'react';
import { 
  Mail, 
  FileCheck2, 
  GitGraph, 
  Calendar, 
  AlertTriangle, 
  BarChart3, 
  Award, 
  Settings, 
  FileText,
  Ship,
  Sparkles
} from 'lucide-react';

export default function GoogleAppsMenu({
  isOpen,
  onClose,
  onSelectApp,
  onOpenSettings
}) {
  if (!isOpen) return null;

  const apps = [
    { id: 'inbox', label: 'Gmail', icon: Mail, color: 'text-red-500', bg: 'bg-red-500/10' },
    { id: 'inspector', label: 'Inspector', icon: FileCheck2, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { id: 'timeline', label: 'Timeline', icon: GitGraph, color: 'text-violet-500', bg: 'bg-violet-500/10' },
    { id: 'calendar', label: 'Calendar', icon: Calendar, color: 'text-cyan-500', bg: 'bg-cyan-500/10' },
    { id: 'human_review', label: 'Review Queue', icon: AlertTriangle, color: 'text-amber-500', bg: 'bg-amber-500/10' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
    { id: 'benchmark', label: 'Evaluation', icon: Award, color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
    { id: 'settings', label: 'Settings', icon: Settings, color: 'text-slate-500', bg: 'bg-slate-500/10', isSettings: true },
    { id: 'docs', label: 'Trade Docs', icon: FileText, color: 'text-blue-600', bg: 'bg-blue-600/10' }
  ];

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40" onClick={onClose} />

      {/* Floating Apps Grid Box */}
      <div 
        className="absolute top-16 right-12 z-50 w-80 p-4 rounded-3xl shadow-2xl border transition-colors select-none animate-in fade-in zoom-in-95 duration-150"
        style={{
          backgroundColor: 'var(--gmail-surface)',
          borderColor: 'var(--gmail-border)',
          color: 'var(--gmail-text)'
        }}
      >
        <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 px-2 pb-2 mb-1 border-b" style={{ borderColor: 'var(--gmail-border)' }}>
          Google Workspace & Averish Apps
        </div>

        <div className="grid grid-cols-3 gap-3 pt-2">
          {apps.map((app) => {
            const Icon = app.icon;
            return (
              <button
                key={app.id}
                onClick={() => {
                  if (app.isSettings) {
                    onOpenSettings();
                  } else {
                    onSelectApp(app.id);
                  }
                  onClose();
                }}
                className="flex flex-col items-center justify-center p-3 rounded-2xl hover:bg-black/5 dark:hover:bg-white/10 transition group cursor-pointer"
              >
                <div className={`w-11 h-11 rounded-2xl ${app.bg} flex items-center justify-center mb-1.5 shadow-xs group-hover:scale-105 transition`}>
                  <Icon className={`w-6 h-6 ${app.color}`} />
                </div>
                <span className="text-xs font-medium text-slate-700 dark:text-slate-200 text-center leading-tight truncate w-full">
                  {app.label}
                </span>
              </button>
            );
          })}
        </div>

        <div className="mt-4 pt-3 border-t text-center" style={{ borderColor: 'var(--gmail-border)' }}>
          <span className="text-[11px] text-blue-600 dark:text-blue-400 font-medium hover:underline cursor-pointer">
            More from Averish Marketplace
          </span>
        </div>
      </div>
    </>
  );
}
