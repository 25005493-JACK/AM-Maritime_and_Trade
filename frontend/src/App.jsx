import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar.jsx';
import InboxFeed from './components/InboxFeed.jsx';
import SplitScreenInspector from './components/SplitScreenInspector.jsx';
import HumanReviewModal from './components/HumanReviewModal.jsx';
import AnalyticsDashboard from './components/AnalyticsDashboard.jsx';
import SelfEvaluationView from './components/SelfEvaluationView.jsx';
import VesselCalendar from './components/VesselCalendar.jsx';
import TimelineWheel from './components/TimelineWheel.jsx';
import OcrDashboard from './components/OcrDashboard.jsx';
import { Download } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState(
    () => window.location.pathname === '/dashboard' ? 'ocr_dashboard' : 'inbox'
  );
  const [theme, setTheme] = useState(() => {
    const initial = window.localStorage.getItem('averish-theme') === 'light' ? 'light' : 'dark';
    document.documentElement.dataset.theme = initial;
    return initial;
  });
  const [emails, setEmails] = useState([]);
  const [selectedEmailId, setSelectedEmailId] = useState(null);
  const [emailDetail, setEmailDetail] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [evaluationData, setEvaluationData] = useState(null);
  const [loadingEval, setLoadingEval] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);

  // Toast Notification State
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Calendar State
  const [calendarData, setCalendarData] = useState(null);
  const [selectedPort, setSelectedPort] = useState('ALL');
  const isOcrDashboard = activeTab === 'ocr_dashboard';

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem('averish-theme', theme);
  }, [theme]);

  const navigateTo = (tab) => {
    setActiveTab(tab);
    const nextPath = tab === 'ocr_dashboard' ? '/dashboard' : '/';
    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, '', nextPath);
    }
  };

  useEffect(() => {
    const handlePopState = () => {
      setActiveTab(window.location.pathname === '/dashboard' ? 'ocr_dashboard' : 'inbox');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

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

  // Fetch Calendar Data (supports port filter)
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
      }
    } catch (err) {
      console.error('Failed to run self evaluate:', err);
    } finally {
      setLoadingEval(false);
    }
  };

  // Save Human-in-the-Loop Override
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
      }
    } catch (err) {
      console.error('Failed to save override:', err);
    }
  };

  useEffect(() => {
    if (isOcrDashboard) return;
    fetchEmails();
    fetchAnalytics();
    fetchCalendar('ALL');
  }, [isOcrDashboard]);

  useEffect(() => {
    if (selectedEmailId) {
      fetchEmailDetail(selectedEmailId);
    }
  }, [selectedEmailId]);

  return (
    <div className="flex h-screen w-full bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Navigation Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={navigateTo}
        stats={analytics?.summary_stats}
        theme={theme}
        onToggleTheme={() => setTheme((current) => current === 'dark' ? 'light' : 'dark')}
        onRefresh={() => {
          fetchEmails();
          fetchAnalytics();
          fetchCalendar(selectedPort);
        }}
      />

      {/* Main Active Tab Container */}
      <main className="flex-1 flex min-w-0 overflow-hidden">
        {activeTab === 'inbox' && (
          <div className="flex-1 flex min-w-0">
            <InboxFeed
              emails={emails}
              selectedEmailId={selectedEmailId}
              onSelectEmail={(id) => setSelectedEmailId(id)}
              onOpenInspector={() => navigateTo('inspector')}
            />
            {/* Embedded Inspector Panel on Wide Screens */}
            <div className="hidden xl:flex w-[42rem] min-w-[420px] border-l border-slate-800">
              <SplitScreenInspector
                emailDetail={emailDetail}
                onOpenOverrideModal={() => setShowOverrideModal(true)}
                onShowToast={showToast}
              />
            </div>
          </div>
        )}

        {activeTab === 'inspector' && (
          <SplitScreenInspector
            emailDetail={emailDetail}
            onOpenOverrideModal={() => setShowOverrideModal(true)}
            onShowToast={showToast}
          />
        )}

        {activeTab === 'timeline' && (
          <TimelineWheel theme={theme} />
        )}

        {activeTab === 'calendar' && (
          <VesselCalendar
            calendarData={calendarData}
            selectedPort={selectedPort}
            onPortChange={handlePortChange}
            onAssignContainer={handleAssignContainer}
            onAutoConfirmBooking={handleAutoConfirmBooking}
          />
        )}

        {activeTab === 'human_review' && (
          <div className="flex-1 p-6 overflow-y-auto bg-slate-950">
            <div className="flex items-start justify-between gap-4 mb-6">
              <div>
                <h2 className="text-lg font-bold text-slate-100 mb-2">Human-in-the-Loop Review Queue</h2>
                <p className="text-xs text-slate-400">
                  Messages escalated due to damaged OCR text, missing required fields, or low confidence extraction.
                </p>
              </div>
              <a
                href="/api/review-decisions/export"
                download="reviewer-decisions.csv"
                className="shrink-0 inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition"
                title="Download reviewer decision log"
              >
                <Download className="w-4 h-4" />
                <span>Export Decision Log</span>
              </a>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {emails
                .filter((e) => e.verification?.status === 'NEEDS_REVIEW' || e.verification?.status === 'HUMAN_REVIEW_REQUIRED')
                .map((email) => (
                  <div key={email.id} className="glass-card p-4 rounded-xl border border-amber-500/40">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-xs text-amber-400 font-bold">{email.id}</span>
                      <span className="text-xs text-slate-400">{email.sender}</span>
                    </div>
                    <h3 className="text-sm font-semibold text-slate-100 mb-2">{email.subject}</h3>
                    <p className="text-xs text-amber-300 font-mono bg-amber-950/40 p-2 rounded mb-3">
                      Reason: {email.verification?.human_review_reasons?.join(' | ')}
                    </p>
                    <button
                      onClick={() => {
                        setSelectedEmailId(email.id);
                        setShowOverrideModal(true);
                      }}
                      className="w-full py-2 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs rounded-lg transition"
                    >
                      Review & Override Fields
                    </button>
                  </div>
                ))}
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <AnalyticsDashboard analytics={analytics} />
        )}

        {activeTab === 'ocr_dashboard' && (
          <OcrDashboard />
        )}

        {activeTab === 'benchmark' && (
          <SelfEvaluationView
            onRunSelfEvaluate={handleRunSelfEvaluate}
            evaluationData={evaluationData}
            loading={loadingEval}
          />
        )}
      </main>

      {/* Human Review Override Modal */}
      {showOverrideModal && (
        <HumanReviewModal
          emailDetail={emailDetail}
          onClose={() => setShowOverrideModal(false)}
          onSaveOverride={handleSaveOverride}
        />
      )}

      {/* Interactive Toast Notification Banner */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 animate-bounce duration-300">
          <div className={`px-4 py-3 rounded-xl shadow-2xl font-medium text-xs border flex items-center space-x-2 backdrop-blur-md ${
            toast.type === 'success' 
              ? 'bg-emerald-950/90 text-emerald-300 border-emerald-500/50 shadow-emerald-950/60'
              : toast.type === 'warning'
              ? 'bg-amber-950/90 text-amber-300 border-amber-500/50 shadow-amber-950/60'
              : 'bg-cyan-950/90 text-cyan-300 border-cyan-500/50 shadow-cyan-950/60'
          }`}>
            <span>{toast.message}</span>
          </div>
        </div>
      )}
    </div>
  );
}
