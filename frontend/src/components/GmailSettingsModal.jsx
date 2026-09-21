import React, { useState } from 'react';
import { X, Check, CheckSquare, Square } from 'lucide-react';

export default function GmailSettingsModal({
  isOpen,
  onClose,
  previewPaneMode,
  setPreviewPaneMode,
  theme,
  setTheme,
  pageSize,
  setPageSize
}) {
  const [activeSettingsTab, setActiveSettingsTab] = useState('Advanced');
  const [autoAdvance, setAutoAdvance] = useState(true);
  const [customShortcuts, setCustomShortcuts] = useState(false);
  const [multipleInboxes, setMultipleInboxes] = useState(false);
  const [hoverActions, setHoverActions] = useState(true);

  if (!isOpen) return null;

  const tabs = [
    'General',
    'Labels',
    'Inbox',
    'Accounts and Import',
    'Filters and Blocked Addresses',
    'Forwarding and POP/IMAP',
    'Add-ons',
    'Chat and Meet',
    'Advanced',
    'Offline',
    'Themes'
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 select-none animate-in fade-in duration-150">
      <div 
        className="w-full max-w-5xl h-[85vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden border transition-colors"
        style={{
          backgroundColor: 'var(--gmail-surface)',
          borderColor: 'var(--gmail-border)',
          color: 'var(--gmail-text)'
        }}
      >
        {/* Header matching Gmail Settings */}
        <div className="px-6 py-4 border-b flex items-center justify-between" style={{ borderColor: 'var(--gmail-border)' }}>
          <h2 className="text-xl font-normal text-slate-800 dark:text-slate-100" style={{ fontFamily: 'Google Sans, Roboto, sans-serif' }}>
            Settings
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-black/10 dark:hover:bg-white/10 text-slate-500 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Horizontal Navigation Tabs matching Screenshot */}
        <div className="px-6 pt-3 border-b flex items-center space-x-6 overflow-x-auto text-xs font-medium no-scrollbar" style={{ borderColor: 'var(--gmail-border)' }}>
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveSettingsTab(tab)}
              className={`pb-2.5 whitespace-nowrap transition-colors relative cursor-pointer ${
                activeSettingsTab === tab
                  ? 'text-blue-600 dark:text-blue-400 font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              {tab}
              {activeSettingsTab === tab && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-400 rounded-full" />
              )}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-8 text-sm">
          
          {/* ADVANCED TAB (Directly matching user's screenshot) */}
          {activeSettingsTab === 'Advanced' && (
            <div className="max-w-3xl space-y-8">
              
              {/* Auto-advance */}
              <div className="flex items-start space-x-4">
                <button
                  onClick={() => setAutoAdvance(!autoAdvance)}
                  className="mt-0.5 text-blue-600 dark:text-blue-400 cursor-pointer"
                >
                  {autoAdvance ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5 text-slate-400" />}
                </button>
                <div className="space-y-1">
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                    Auto-advance
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400 text-xs leading-relaxed">
                    Show the next conversation instead of your inbox after you delete, archive, snooze, or mute a conversation.
                  </p>
                  <p className="text-slate-500 dark:text-slate-500 text-xs">
                    You can select whether to advance to the next or previous conversation in the 'General' settings page.
                  </p>
                </div>
              </div>

              {/* Custom keyboard shortcuts */}
              <div className="flex items-start space-x-4">
                <button
                  onClick={() => setCustomShortcuts(!customShortcuts)}
                  className="mt-0.5 text-blue-600 dark:text-blue-400 cursor-pointer"
                >
                  {customShortcuts ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5 text-slate-400" />}
                </button>
                <div className="space-y-1">
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                    Custom keyboard shortcuts
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400 text-xs leading-relaxed">
                    Enable the ability to customize your keyboard shortcuts via a new settings tab from which you can remap keys to various actions.
                  </p>
                </div>
              </div>

              {/* Multiple Inboxes */}
              <div className="flex items-start space-x-4">
                <button
                  onClick={() => setMultipleInboxes(!multipleInboxes)}
                  className="mt-0.5 text-blue-600 dark:text-blue-400 cursor-pointer"
                >
                  {multipleInboxes ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5 text-slate-400" />}
                </button>
                <div className="space-y-1">
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                    Multiple Inboxes
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400 text-xs leading-relaxed">
                    Add extra lists of emails in your inbox to see even more important mails at once.
                  </p>
                  <p className="text-slate-500 dark:text-slate-500 text-xs">
                    The new lists of threads can be labels, your starred messages, drafts or any search you want, configure under settings.
                  </p>
                </div>
              </div>

              {/* Preview Pane (The core feature in user screenshot!) */}
              <div className="flex items-start space-x-4 pt-2 border-t" style={{ borderColor: 'var(--gmail-border)' }}>
                <div className="mt-0.5 text-blue-600 dark:text-blue-400">
                  <CheckSquare className="w-5 h-5" />
                </div>
                <div className="space-y-3 flex-1">
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                      Preview Pane (Split Screen)
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400 text-xs leading-relaxed">
                      Enable the ability to toggle on/off the ability to view your messages side by side with the message list.
                    </p>
                  </div>

                  {/* Split mode radio options */}
                  <div className="flex items-center space-x-4 pt-1">
                    {[
                      { id: 'vertical', label: 'Vertical Split (Side-by-side)' },
                      { id: 'none', label: 'No Split (Full Inbox)' },
                      { id: 'horizontal', label: 'Horizontal Split (Bottom)' },
                    ].map((mode) => (
                      <label 
                        key={mode.id}
                        className={`flex items-center space-x-2 px-3 py-2 rounded-lg border text-xs cursor-pointer transition ${
                          previewPaneMode === mode.id
                            ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 font-semibold'
                            : 'border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-black/5 dark:hover:bg-white/5'
                        }`}
                      >
                        <input
                          type="radio"
                          name="previewMode"
                          checked={previewPaneMode === mode.id}
                          onChange={() => setPreviewPaneMode(mode.id)}
                          className="accent-blue-600"
                        />
                        <span>{mode.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* THEMES TAB */}
          {activeSettingsTab === 'Themes' && (
            <div className="max-w-2xl space-y-6">
              <div>
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-base mb-1">
                  Pick your theme
                </h3>
                <p className="text-xs text-slate-500">
                  Choose between the authentic Google Workspace Light Theme or Modern Gmail Dark Mode.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-6 pt-2">
                {/* Light Beige Theme */}
                <div 
                  onClick={() => setTheme('light')}
                  className={`p-4 rounded-xl border-2 cursor-pointer transition ${
                    theme === 'light' 
                      ? 'border-amber-700 shadow-md ring-2 ring-amber-700/20' 
                      : 'border-slate-200 dark:border-slate-700 hover:border-slate-400'
                  }`}
                >
                  <div className="h-28 rounded-lg bg-[#f7f3eb] border border-[#e2dbcf] p-2 flex flex-col justify-between mb-3 shadow-inner">
                    <div className="h-3 w-16 bg-[#b45309] rounded" />
                    <div className="space-y-1.5">
                      <div className="h-2 w-full bg-[#fffdfa] rounded border border-[#e2dbcf]" />
                      <div className="h-2 w-3/4 bg-[#ebe4d8] rounded" />
                    </div>
                    <div className="h-4 w-20 bg-[#e8ded0] rounded-full border border-[#d8cdba]" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm">Light Beige (Warm Canvas)</span>
                    {theme === 'light' && <Check className="w-4 h-4 text-amber-700" />}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Calm warm parchment & linen aesthetic</p>
                </div>

                {/* Dark Theme */}
                <div 
                  onClick={() => setTheme('dark')}
                  className={`p-4 rounded-xl border-2 cursor-pointer transition ${
                    theme === 'dark' 
                      ? 'border-blue-500 shadow-md ring-2 ring-blue-500/20' 
                      : 'border-slate-200 dark:border-slate-700 hover:border-slate-400'
                  }`}
                >
                  <div className="h-28 rounded-lg bg-[#1e1f22] border border-slate-700 p-2 flex flex-col justify-between mb-3 shadow-inner">
                    <div className="h-3 w-16 bg-[#a8c7fa] rounded" />
                    <div className="space-y-1.5">
                      <div className="h-2 w-full bg-slate-700 rounded" />
                      <div className="h-2 w-3/4 bg-slate-700 rounded" />
                    </div>
                    <div className="h-4 w-20 bg-[#28364d] rounded-full" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm">Gmail Dark</span>
                    {theme === 'dark' && <Check className="w-4 h-4 text-blue-400" />}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Low-strain dark slate Material Design</p>
                </div>
              </div>
            </div>
          )}

          {/* GENERAL TAB */}
          {activeSettingsTab === 'General' && (
            <div className="max-w-3xl space-y-6 text-xs">
              <div className="grid grid-cols-4 gap-4 py-3 border-b" style={{ borderColor: 'var(--gmail-border)' }}>
                <span className="font-semibold text-slate-700 dark:text-slate-300">Language</span>
                <span className="col-span-3 text-slate-600 dark:text-slate-400">English (United States) — DocuMatch AI</span>
              </div>
              
              <div className="grid grid-cols-4 gap-4 py-3 border-b" style={{ borderColor: 'var(--gmail-border)' }}>
                <span className="font-semibold text-slate-700 dark:text-slate-300">Maximum page size</span>
                <div className="col-span-3 flex items-center space-x-2">
                  <span>Show</span>
                  <select 
                    value={pageSize} 
                    onChange={(e) => setPageSize(Number(e.target.value))}
                    className="p-1 rounded border bg-transparent"
                  >
                    <option value={15}>15</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                  <span>conversations per page</span>
                </div>
              </div>

              <div className="grid grid-cols-4 gap-4 py-3 border-b" style={{ borderColor: 'var(--gmail-border)' }}>
                <span className="font-semibold text-slate-700 dark:text-slate-300">Hover actions</span>
                <label className="col-span-3 flex items-center space-x-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={hoverActions} 
                    onChange={() => setHoverActions(!hoverActions)} 
                    className="accent-blue-600" 
                  />
                  <span>Enable hover actions (Quick archive, delete, mark as read, snooze)</span>
                </label>
              </div>

              <div className="grid grid-cols-4 gap-4 py-3" style={{ borderColor: 'var(--gmail-border)' }}>
                <span className="font-semibold text-slate-700 dark:text-slate-300">Smart Features & AI</span>
                <span className="col-span-3 text-emerald-600 dark:text-emerald-400 font-semibold">
                  ✓ Autonomous Shipping Extraction, SI/BL Discrepancy Gate, and LLM Assistant active
                </span>
              </div>
            </div>
          )}

          {/* OTHER TABS PLACEHOLDER */}
          {!['Advanced', 'Themes', 'General'].includes(activeSettingsTab) && (
            <div className="py-12 text-center text-slate-400">
              <p className="text-sm">Configured for Google Workspace & DocuMatch Operations</p>
              <p className="text-xs text-slate-500 mt-1">Check 'Advanced' tab to customize Preview Pane and Auto-advance.</p>
            </div>
          )}

        </div>

        {/* Footer Actions matching Gmail */}
        <div className="px-6 py-4 border-t flex items-center justify-end space-x-3 bg-black/5 dark:bg-white/5" style={{ borderColor: 'var(--gmail-border)' }}>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-full border border-slate-300 dark:border-slate-700 text-xs font-semibold hover:bg-black/5 dark:hover:bg-white/5 transition"
          >
            Cancel
          </button>
          <button
            onClick={onClose}
            className="px-6 py-2 rounded-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
