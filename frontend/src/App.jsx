import React, { useState, useEffect } from 'react';
import GmailHeader from './components/GmailHeader.jsx';
import GmailSidebar from './components/GmailSidebar.jsx';
import GmailInbox from './components/GmailInbox.jsx';
import GmailComposeModal from './components/GmailComposeModal.jsx';
import GmailSettingsModal from './components/GmailSettingsModal.jsx';
import GoogleAppsMenu from './components/GoogleAppsMenu.jsx';
import SplitScreenInspector from './components/SplitScreenInspector.jsx';
import HumanReviewModal from './components/HumanReviewModal.jsx';
import AnalyticsDashboard from './components/AnalyticsDashboard.jsx';
import SelfEvaluationView from './components/SelfEvaluationView.jsx';
import VesselCalendar from './components/VesselCalendar.jsx';
import TimelineWheel from './components/TimelineWheel.jsx';

export default function App() {
  // Navigation & View States
  const [activeTab, setActiveTab] = useState('inbox');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [previewPaneMode, setPreviewPaneMode] = useState('vertical'); // 'vertical', 'horizontal', 'none'
  const [theme, setTheme] = useState('light'); // Default to authentic Google Workspace Light
  const [pageSize, setPageSize] = useState(25);

  // Search & Modals
  const [searchTerm, setSearchTerm] = useState('');
  const [isComposeOpen, setIsComposeOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAppsMenuOpen, setIsAppsMenuOpen] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);

  // Data States
  const [emails, setEmails] = useState([]);
  const [selectedEmailId, setSelectedEmailId] = useState(null);
  const [emailDetail, setEmailDetail] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [evaluationData, setEvaluationData] = useState(null);
  const [loadingEval, setLoadingEval] = useState(false);

  // Toast Notification State
  const [toast, setToast] = useState(null);
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Calendar State
  const [calendarData, setCalendarData] = useState(null);
  const [selectedPort, setSelectedPort] = useState('ALL');

  // Set theme attribute on root
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Fetch emails list
  const fetchEmails = async () => {
    try {
      const res = await fetch('/api/emails');
      if (res.ok) {
        const data = await res.json();
        setEmails(data);
        if (data.length > 0 && !selectedEmailId) {
          setSelectedEmailId(data[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch emails:', err);
    }
  };

  // Fetch email detail
  const fetchEmailDetail = async (id) => {
    if (!id) return;
    try {
      const res = await fetch(`/api/emails/${id}`);
      if (res.ok) {
        const data = await res.json();
        setEmailDetail(data);
      }
    } catch (err) {
      console.error('Failed to fetch email detail:', err);
    }
  };

  // Fetch analytics
  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics');
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    }
  };

  // Fetch Calendar Data
  const fetchCalendar = async (port = selectedPort) => {
    try {
      const url = port && port !== 'ALL' ? `/api/calendar?port=${encodeURIComponent(port)}` : '/api/calendar';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setCalendarData(data);
      }
    } catch (err) {
      console.error('Failed to fetch calendar:', err);
    }
  };

  const handlePortChange = (port) => {
    setSelectedPort(port);
    fetchCalendar(port);
  };

  const handleAssignContainer = async (payload) => {
    try {
      const res = await fetch('/api/calendar/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        await fetchCalendar(selectedPort);
        showToast('Container assigned to vessel schedule', 'success');
      }
    } catch (err) {
      console.error('Failed to assign container:', err);
    }
  };

  const handleAutoConfirmBooking = async (emailId) => {
    try {
      const res = await fetch('/api/calendar/auto-book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_id: emailId })
      });
      if (res.ok) {
        await fetchCalendar(selectedPort);
        showToast(`Auto-confirmed booking for ${emailId}`, 'success');
      }
    } catch (err) {
      console.error('Failed to auto confirm booking:', err);
    }
  };

  // Run self evaluation
  const handleRunSelfEvaluate = async () => {
    setLoadingEval(true);
    try {
      const res = await fetch('/api/self-evaluate');
      if (res.ok) {
        const data = await res.json();
        setEvaluationData(data);
        showToast('Self-evaluation benchmark complete', 'success');
      }
    } catch (err) {
      console.error('Failed to run self evaluate:', err);
    } finally {
      setLoadingEval(false);
    }
  };

  // Save Human Override
  const handleSaveOverride = async (emailId, siOverrides, blOverrides) => {
    try {
      const res = await fetch('/api/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_id: emailId,
          si_overrides: siOverrides,
          bl_overrides: blOverrides
        })
      });

      if (res.ok) {
        await fetchEmails();
        await fetchEmailDetail(emailId);
        await fetchAnalytics();
        setShowOverrideModal(false);
        showToast(`Human correction saved for ${emailId}`, 'success');
      }
    } catch (err) {
      console.error('Failed to save override:', err);
    }
  };

  // Send Email simulation from Compose Modal
  const handleSendEmail = ({ to, subject, body, attachments }) => {
    showToast(`Message sent to ${to || 'Recipient'}`, 'info');
  };

  useEffect(() => {
    fetchEmails();
    fetchAnalytics();
    fetchCalendar('ALL');
  }, []);

  useEffect(() => {
    if (selectedEmailId) {
      fetchEmailDetail(selectedEmailId);
    }
  }, [selectedEmailId]);

  // Filter emails by global search term
  const searchedEmails = emails.filter((email) => {
    if (!searchTerm.trim()) return true;
    const q = searchTerm.toLowerCase();
    return (
      email.id.toLowerCase().includes(q) ||
      email.subject.toLowerCase().includes(q) ||
      email.sender.toLowerCase().includes(q) ||
      (email.company && email.company.toLowerCase().includes(q)) ||
      (email.vessel && email.vessel.toLowerCase().includes(q))
    );
  });

  return (
    <div 
      className="flex flex-col h-screen w-screen overflow-hidden font-sans transition-colors duration-200 select-none"
      style={{
        backgroundColor: 'var(--gmail-bg)',
        color: 'var(--gmail-text)'
      }}
    >
      {/* 1. Authentic Gmail Top Header */}
      <GmailHeader
        sidebarCollapsed={sidebarCollapsed}
        setSidebarCollapsed={setSidebarCollapsed}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenApps={() => setIsAppsMenuOpen(!isAppsMenuOpen)}
        theme={theme}
        setTheme={setTheme}
        stats={analytics?.summary_stats}
      />

      {/* 2. Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Authentic Gmail Left Sidebar */}
        <GmailSidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          selectedCategory={selectedCategory}
          setSelectedCategory={setSelectedCategory}
          stats={analytics?.summary_stats}
          collapsed={sidebarCollapsed}
          onOpenCompose={() => setIsComposeOpen(true)}
        />

        {/* Content View Routing */}
        <main className="flex-1 flex overflow-hidden">
          
          {/* A. GMAIL INBOX VIEW */}
          {activeTab === 'inbox' && (
            <GmailInbox
              emails={searchedEmails}
              selectedEmailId={selectedEmailId}
              onSelectEmail={(id) => setSelectedEmailId(id)}
              emailDetail={emailDetail}
              onOpenInspector={() => setActiveTab('inspector')}
              onOpenOverrideModal={() => setShowOverrideModal(true)}
              onRefresh={() => {
                fetchEmails();
                fetchAnalytics();
              }}
              previewPaneMode={previewPaneMode}
              setPreviewPaneMode={setPreviewPaneMode}
              showToast={showToast}
            />
          )}

          {/* B. SI VS BL INSPECTOR */}
          {activeTab === 'inspector' && (
            <div className="flex-1 flex overflow-hidden">
              <SplitScreenInspector
                emailDetail={emailDetail}
                onOpenOverrideModal={() => setShowOverrideModal(true)}
                onShowToast={showToast}
              />
            </div>
          )}

          {/* C. SHIPMENT TIMELINE VIEW */}
          {activeTab === 'timeline' && (
            <div className="flex-1 flex overflow-hidden">
              <TimelineWheel />
            </div>
          )}

          {/* D. VESSEL CALENDAR */}
          {activeTab === 'calendar' && (
            <div className="flex-1 flex overflow-hidden">
              <VesselCalendar
                calendarData={calendarData}
                selectedPort={selectedPort}
                onPortChange={handlePortChange}
                onAssignContainer={handleAssignContainer}
                onAutoConfirmBooking={handleAutoConfirmBooking}
              />
            </div>
          )}

          {/* E. HUMAN REVIEW QUEUE */}
          {activeTab === 'human_review' && (
            <div className="flex-1 p-6 overflow-y-auto" style={{ backgroundColor: 'var(--gmail-surface)' }}>
              <div className="max-w-5xl mx-auto">
                <div className="mb-6 pb-4 border-b" style={{ borderColor: 'var(--gmail-border)' }}>
                  <h2 className="text-xl font-normal text-slate-900 dark:text-slate-100 tracking-tight" style={{ fontFamily: 'Google Sans, Roboto, sans-serif' }}>
                    Human-in-the-Loop Review Queue
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Messages flagged by AI due to OCR legibility issues, missing mandatory trade fields, or cross-document discrepancies.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {emails
                    .filter((e) => e.verification?.status === 'NEEDS_REVIEW' || e.verification?.status === 'HUMAN_REVIEW_REQUIRED')
                    .map((email) => (
                      <div 
                        key={email.id} 
                        className="p-5 rounded-2xl border shadow-xs transition hover:shadow-md"
                        style={{
                          backgroundColor: 'var(--gmail-bg)',
                          borderColor: 'var(--gmail-border)'
                        }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30">
                            {email.id}
                          </span>
                          <span className="text-xs text-slate-500">{email.sender}</span>
                        </div>
                        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-2">
                          {email.subject}
                        </h3>
                        <p className="text-xs text-amber-700 dark:text-amber-300 font-mono bg-amber-50 dark:bg-amber-950/40 p-2.5 rounded-lg mb-4 border border-amber-200 dark:border-amber-900/40">
                          Flag: {email.verification?.human_review_reasons?.join(' | ') || email.verification?.review_reason || 'Gate condition triggered'}
                        </p>
                        <button
                          onClick={() => {
                            setSelectedEmailId(email.id);
                            setShowOverrideModal(true);
                          }}
                          className="w-full py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs rounded-xl shadow-xs transition cursor-pointer"
                        >
                          Review & Override Extracted Fields
                        </button>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}

          {/* F. ANALYTICS */}
          {activeTab === 'analytics' && (
            <div className="flex-1 overflow-y-auto">
              <AnalyticsDashboard analytics={analytics} />
            </div>
          )}

          {/* G. EVALUATION BENCHMARK */}
          {activeTab === 'benchmark' && (
            <div className="flex-1 overflow-y-auto">
              <SelfEvaluationView
                onRunSelfEvaluate={handleRunSelfEvaluate}
                evaluationData={evaluationData}
                loading={loadingEval}
              />
            </div>
          )}

        </main>
      </div>

      {/* 3. Floating Gmail Compose Modal (Bottom Right) */}
      <GmailComposeModal
        isOpen={isComposeOpen}
        onClose={() => setIsComposeOpen(false)}
        onSendEmail={handleSendEmail}
      />

      {/* 4. Google 9-dot Waffle Menu Dropdown */}
      <GoogleAppsMenu
        isOpen={isAppsMenuOpen}
        onClose={() => setIsAppsMenuOpen(false)}
        onSelectApp={(appId) => setActiveTab(appId)}
        onOpenSettings={() => {
          setIsSettingsOpen(true);
          setIsAppsMenuOpen(false);
        }}
      />

      {/* 5. Authentic Gmail Settings Modal (From Screenshot) */}
      <GmailSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        previewPaneMode={previewPaneMode}
        setPreviewPaneMode={setPreviewPaneMode}
        theme={theme}
        setTheme={setTheme}
        pageSize={pageSize}
        setPageSize={setPageSize}
      />

      {/* 6. Human Review Override Modal */}
      {showOverrideModal && (
        <HumanReviewModal
          emailDetail={emailDetail}
          onClose={() => setShowOverrideModal(false)}
          onSaveOverride={handleSaveOverride}
        />
      )}

      {/* 7. Authentic Gmail Toast Alert (Bottom Left / Right) */}
      {toast && (
        <div className="fixed bottom-6 left-6 z-50 animate-in slide-in-from-bottom-3 duration-200">
          <div className="px-5 py-3 rounded-lg shadow-xl font-medium text-xs flex items-center space-x-3 bg-[#1f1f1f] text-white border border-slate-700">
            <span>{toast.message}</span>
            <button 
              onClick={() => setToast(null)}
              className="text-blue-400 font-semibold hover:underline cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
