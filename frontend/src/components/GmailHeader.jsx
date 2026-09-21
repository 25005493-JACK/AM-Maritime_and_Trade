import React, { useState } from 'react';
import { 
  Menu, 
  Search, 
  SlidersHorizontal, 
  HelpCircle, 
  Settings, 
  Grid3X3, 
  Sun, 
  Moon, 
  X,
  Check,
  Ship,
  Sparkles
} from 'lucide-react';

export default function GmailHeader({
  sidebarCollapsed,
  setSidebarCollapsed,
  searchTerm,
  setSearchTerm,
  onOpenSettings,
  onOpenApps,
  theme,
  setTheme,
  stats
}) {
  const [searchFocused, setSearchFocused] = useState(false);

  return (
    <header className="h-16 px-4 flex items-center justify-between select-none border-b transition-colors duration-200"
      style={{
        backgroundColor: 'var(--gmail-bg)',
        borderColor: 'var(--gmail-border)'
      }}>
      
      {/* Left: Hamburger & Gmail Logo */}
      <div className="flex items-center space-x-3 w-64 min-w-[240px]">
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="p-2.5 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300 transition-colors"
          title="Main menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Authentic Gmail Logo & Title */}
        <div className="flex items-center space-x-2.5 cursor-pointer">
          <div className="relative flex items-center justify-center">
            {/* SVG of Gmail envelope with Google colors */}
            <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none">
              <path d="M20 4H4C2.9 4 2.01 4.9 2.01 6L2 18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6C22 4.9 21.1 4 20 4ZM20 8L12 13L4 8V6L12 11L20 6V8Z" fill="#EA4335" />
              <path d="M4 6L12 11L20 6V8L12 13L4 8V6Z" fill="#4285F4" opacity="0.9" />
              <path d="M2 18V6C2 4.9 2.9 4 4 4H5V18C5 18.55 4.55 19 4 19C3.45 19 3 18.55 3 18H2Z" fill="#34A853" opacity="0.4" />
              <path d="M22 6V18C22 19.1 21.1 20 20 20H19V6H20C21.1 6 22 6 22 6Z" fill="#FBBC05" opacity="0.4" />
            </svg>
          </div>
          <div className="flex items-baseline space-x-1.5">
            <span className="text-[22px] font-normal tracking-tight text-slate-700 dark:text-slate-200" style={{ fontFamily: 'Google Sans, Roboto, sans-serif' }}>
              Gmail
            </span>
            <span className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
              Freight Ops
            </span>
          </div>
        </div>
      </div>

      {/* Center: Authentic Gmail Pill Search Bar */}
      <div className="flex-1 max-w-2xl px-4">
        <div 
          className={`relative flex items-center w-full h-12 rounded-full transition-all duration-200 border ${
            searchFocused 
              ? 'shadow-md ring-2 ring-amber-700/20' 
              : 'hover:brightness-95'
          }`}
          style={{
            backgroundColor: searchFocused ? 'var(--gmail-surface)' : 'var(--gmail-surface-variant)',
            borderColor: searchFocused ? 'var(--gmail-border)' : 'transparent'
          }}
        >
          <div className="pl-4 pr-3 text-slate-500 dark:text-slate-400">
            <Search className="w-5 h-5" />
          </div>

          <input
            type="text"
            placeholder="Search mail (ID, vessel, shipper, booking ref, port)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            className="w-full bg-transparent text-sm text-slate-800 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none"
          />

          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="p-1.5 mr-1 rounded-full hover:bg-black/10 dark:hover:bg-white/10 text-slate-500 transition"
              title="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <button
            className="p-2 mr-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-slate-500 dark:text-slate-400 transition"
            title="Show search options"
          >
            <SlidersHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Right: Quick Tools, Settings, Google Apps & User Profile */}
      <div className="flex items-center space-x-1.5 select-none">
        {/* Theme Toggle (Light / Dark) */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="p-2.5 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300 transition-colors"
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
        >
          {theme === 'dark' ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-slate-600" />}
        </button>

        {/* Help */}
        <button
          className="p-2.5 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300 transition-colors"
          title="Support & Guides"
        >
          <HelpCircle className="w-5 h-5" />
        </button>

        {/* Settings Button */}
        <button
          onClick={onOpenSettings}
          className="p-2.5 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300 transition-colors"
          title="Settings (Auto-advance, Preview Pane, Themes)"
        >
          <Settings className="w-5 h-5" />
        </button>

        {/* Google Apps 9-dots Waffle Button */}
        <button
          onClick={onOpenApps}
          className="p-2.5 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300 transition-colors"
          title="Google Workspace & DocuMatch Apps"
        >
          <Grid3X3 className="w-5 h-5" />
        </button>

        {/* User Profile Avatar */}
        <div className="pl-1">
          <button 
            className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-medium text-sm flex items-center justify-center shadow-inner hover:ring-4 hover:ring-blue-500/20 transition"
            title="Google Account: DocuMatch Ops (ops@documatch.ai)"
          >
            A
          </button>
        </div>
      </div>
    </header>
  );
}
