import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar.jsx';
import InboxFeed from './components/InboxFeed.jsx';
import SplitScreenInspector from './components/SplitScreenInspector.jsx';
import HumanReviewModal from './components/HumanReviewModal.jsx';
import AnalyticsDashboard from './components/AnalyticsDashboard.jsx';
import SelfEvaluationView from './components/SelfEvaluationView.jsx';
import VesselCalendar from './components/VesselCalendar.jsx';
import TimelineWheel from './components/TimelineWheel.jsx';
import OcrDashboard from './components/OcrDashboard.jsx';
import AgentLearningDashboard, { ReflectionsPanel } from './components/AgentLearningDashboard.jsx';
import ReasoningReceipt from './components/ReasoningReceipt.jsx';
import RedTeamPanel from './components/RedTeamPanel.jsx';
import AutomationSlider from './components/AutomationSlider.jsx';
import { Download } from 'lucide-react';

export default function App() {
  const [theme, setTheme] = useState('dark');
  const [activeTab, setActiveTab] = useState('inbox');
  const [emails, setEmails] = useState([]);
  const [selectedEmailId, setSelectedEmailId] = useState(null);
  const [emailDetail, setEmailDetail] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [evaluationData, setEvaluationData] = useState(null);
  const [loadingEval, setLoadingEval] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [automationLevel, setAutomationLevel] = useState(1);
  const [reflectionsData, setReflectionsData] = useState({ total: 0, by_sender: {} });

  // Toast Notification State
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Calendar State
  const [calendarData, setCalendarData] = useState(null);
  const [selectedPort, setSelectedPort] = useState('ALL');

  // Resizable Right Panel Width State for Inbox & Triage Tab
  const [inspectorWidth, setInspectorWidth] = useState(580);
  const isDraggingRef = useRef(false);

  // Toggle Dark/Light Theme
  const handleToggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  // Flexible Mouse Drag Handler for Resizing Right Bar (Prevents crushing left panel)
  const handleMouseDownResize = (e) => {
    e.preventDefault();
    isDraggingRef.current = true;

    const handleMouseMove = (moveEvent) => {
      if (!isDraggingRef.current) return;
      const windowWidth = window.innerWidth;
      const sidebarWidth = 256; // 64 * 4 = 256px
      const availableWidth = windowWidth - sidebarWidth;
      
      // Right width calculated from mouse position
      const targetRightWidth = windowWidth - moveEvent.clientX;
      
      // Clamp right width between 350px and (availableWidth - 380px) to prevent crushing inbox feed
      const maxAllowedRight = Math.max(350, availableWidth - 380);
      const clampedWidth = Math.min(Math.max(targetRightWidth, 350), maxAllowedRight);

      setInspectorWidth(clampedWidth);
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

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

  // Fetch Agent Reflexion Memories
  const fetchReflections = async () => {
    try {
      const res = await fetch('/api/reflections');
      if (res.ok) {
        const data = await res.json();
        setReflectionsData(data);
      }
    } catch (err) {
      console.error('Failed to fetch reflections:', err);
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
        await fetchReflections();
        setShowOverrideModal(false);
      }
    } catch (err) {
      console.error('Failed to save override:', err);
    }
  };

  useEffect(() => {
    fetchEmails();
    fetchAnalytics();
    fetchCalendar('ALL');
    fetchReflections();
  }, []);

  useEffect(() => {
    if (emails.length > 0 && !selectedEmailId) {
      const firstMismatch = emails.find((e) => e.verification?.status === 'MISMATCH');
      setSelectedEmailId(firstMismatch ? firstMismatch.id : emails[0].id);
    }
  }, [emails, selectedEmailId]);

  useEffect(() => {
    if (selectedEmailId) {
      fetchEmailDetail(selectedEmailId);
    }
  }, [selectedEmailId]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Navigation Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={analytics?.summary_stats}
        onRefresh={() => {
          fetchEmails();
          fetchAnalytics();
          fetchCalendar(selectedPort);
        }}
        theme={theme}
        onToggleTheme={handleToggleTheme}
      />

      {/* Main Active Tab Container */}
      <main className="flex-1 flex overflow-hidden">
        {activeTab === 'inbox' && (
          <div className="flex-1 flex relative overflow-x-auto">
            {/* Left Inbox Feed (Flexible min-width, never squeezed out) */}
            <div className="flex-1 flex flex-col min-w-[380px] overflow-hidden">
              <InboxFeed
                emails={emails}
                selectedEmailId={selectedEmailId}
                onSelectEmail={(id) => setSelectedEmailId(id)}
                onOpenInspector={() => setActiveTab('inspector')}
              />
            </div>

            {/* Draggable Resizable Divider Handle */}
            <div
              onMouseDown={handleMouseDownResize}
              className="resize-handle hover:bg-cyan-500 active:bg-cyan-400 shrink-0"
              title="Drag to resize Inspector panel width"
            />

            {/* Right Resizable Inspector Panel */}
            <div
              style={{ width: `${inspectorWidth}px` }}
              className="hidden lg:flex flex-col border-l border-slate-800 shrink-0 min-w-[350px] overflow-hidden"
            >
              <SplitScreenInspector
                emailDetail={emailDetail}
                onOpenOverrideModal={() => setShowOverrideModal(true)}
              />
            </div>
          </div>
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
            <h2 className="text-lg font-bold text-slate-100 mb-2">Human-in-the-Loop Review Queue</h2>
            <p className="text-xs text-slate-400 mb-6">
              Messages escalated due to damaged OCR text, missing required fields, or low confidence extraction.
            </p>
            <div className="grid grid-cols-2 gap-4">
              {emails
                .filter((e) => e.verification?.status === 'HUMAN_REVIEW_REQUIRED')
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

            {/* Embedded Reflexion Episodic Memory Panel for Reviewers */}
            <div className="mt-8">
              <ReflectionsPanel
                reflectionsBySender={reflectionsData.by_sender}
                onRefresh={fetchReflections}
              />
            </div>
          </div>
        )}

        {activeTab === 'learning' && (
          <AgentLearningDashboard />
        )}

        {activeTab === 'trust' && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-950">
            <div>
              <h2 className="text-sm font-bold text-slate-100">Trust &amp; AI Controls</h2>
              <p className="text-xs text-slate-400 mt-1">
                Auditable reasoning, adversarial rehearsal and the automation licence. Every number here is
                computed from the pipeline's own validator outcomes and the currently loaded inbox.
              </p>
            </div>

            <AutomationSlider
              level={automationLevel}
              onLevelChange={async (level) => {
                setAutomationLevel(level);
                await fetchEmails();
                if (selectedEmailId) fetchEmailDetail(selectedEmailId);
                showToast(`Automation level set to L${level} - inbox states recalculated`, 'info');
              }}
            />

            <RedTeamPanel emailId={selectedEmailId} />

            <ReasoningReceipt
              emailId={selectedEmailId}
              shipmentId={emailDetail?.verification?.shipment_id}
            />
          </div>
        )}
        {activeTab === 'analytics' && (
          <AnalyticsDashboard analytics={analytics} />
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
    </div>
  );
}
