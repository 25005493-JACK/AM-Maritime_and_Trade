import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar.jsx';
import InboxWorkspace from './components/InboxWorkspace.jsx';
import HumanReviewQueue from './components/HumanReviewQueue.jsx';
import VesselCalendar from './components/VesselCalendar.jsx';
import AdminDashboard from './components/AdminDashboard.jsx';
import HumanReviewModal from './components/HumanReviewModal.jsx';
import UploadDocsModal from './components/UploadDocsModal.jsx';
import { apiFetch } from './api.js';

export default function App() {
  const [theme, setTheme] = useState('dark');
  const [activeTab, setActiveTab] = useState('inbox'); // 'inbox', 'human_review', 'calendar', 'admin'
  const [emails, setEmails] = useState([]);
  const [selectedEmailId, setSelectedEmailId] = useState(null);
  const [emailDetail, setEmailDetail] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [evaluationData, setEvaluationData] = useState(null);
  const [loadingEval, setLoadingEval] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
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

  // Toggle Dark/Light Theme
  const handleToggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  // Fetch emails list
  const fetchEmails = async () => {
    try {
      const res = await apiFetch('/api/emails');
      if (res.ok) {
        const data = await res.json();
        setEmails(data);
      }
    } catch (err) {
      console.error('Failed to fetch emails:', err);
    }
  };

  // Fetch email detail
  const fetchEmailDetail = async (id) => {
    if (!id) {
      setEmailDetail(null);
      return;
    }
    try {
      // Check client-side uploaded emails store first (for static Vercel host retention)
      try {
        const customUploads = JSON.parse(localStorage.getItem('documatch_uploaded_emails') || '{}');
        if (customUploads[id]) {
          setEmailDetail(customUploads[id]);
          return;
        }
      } catch (e) {}

      const res = await apiFetch(`/api/emails/${id}`);
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
      const res = await apiFetch('/api/analytics');
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
      const res = await apiFetch('/api/reflections');
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
      const res = await apiFetch(url);
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
      const res = await apiFetch('/api/calendar/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        await fetchCalendar(selectedPort);
        showToast(`Assigned ${payload.booking_no} to vessel schedule!`, 'success');
      }
    } catch (err) {
      console.error('Failed to assign container:', err);
    }
  };

  const handleAutoConfirmBooking = async (emailId) => {
    try {
      const res = await apiFetch('/api/calendar/auto-book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email_id: emailId })
      });
      if (res.ok) {
        await fetchCalendar(selectedPort);
        showToast(`Booking for ${emailId} confirmed to calendar!`, 'success');
      }
    } catch (err) {
      console.error('Failed to auto confirm booking:', err);
    }
  };

  // Run self evaluation
  const handleRunSelfEvaluate = async () => {
    setLoadingEval(true);
    try {
      const res = await apiFetch('/api/self-evaluate');
      if (res.ok) {
        const data = await res.json();
        setEvaluationData(data);
        showToast('Self-Evaluation Benchmark Scoreboard updated!', 'success');
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
      const res = await apiFetch('/api/override', {
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
        showToast(`Saved reviewer override for ${emailId}!`, 'success');
      }
    } catch (err) {
      console.error('Failed to save override:', err);
    }
  };

  const [healthInfo, setHealthInfo] = useState({ llm_mode: 'off', llm_available: false });

  // Fetch System Health & LLM Mode
  const fetchHealth = async () => {
    try {
      const res = await apiFetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setHealthInfo(data);
      }
    } catch (err) {
      console.error('Failed to fetch health info:', err);
    }
  };

  // Handle Live Upload Success
  const handleUploadSuccess = async (uploadData) => {
    await fetchEmails();
    if (uploadData?.email_id) {
      setSelectedEmailId(uploadData.email_id);
      await fetchEmailDetail(uploadData.email_id);
    }
    await fetchAnalytics();
    await fetchHealth();

    const verif = uploadData?.verification || {};
    const status = verif.status || uploadData?.verification_status;
    const defects = verif.defect_fields || uploadData?.defect_fields || [];

    if (status === 'MISMATCH') {
      const fieldList = defects.length > 0 ? defects.join(', ') : 'fields';
      showToast(`Uploaded & compared live: MISMATCH detected in ${fieldList}`, 'warning');
    } else if (status === 'OK') {
      showToast(`Uploaded & compared live: OK (All 7 required fields match!)`, 'success');
    } else if (status === 'NEEDS_REVIEW') {
      showToast(`Uploaded & compared live: NEEDS REVIEW (${verif.review_reason || 'Human review required'})`, 'info');
    } else {
      showToast(`Processed ${uploadData?.email_id || 'document pair'} live through real pipeline!`, 'success');
    }
  };

  useEffect(() => {
    fetchEmails();
    fetchAnalytics();
    fetchCalendar('ALL');
    fetchReflections();
    fetchHealth();
  }, []);

  useEffect(() => {
    if (selectedEmailId) {
      fetchEmailDetail(selectedEmailId);
    } else {
      setEmailDetail(null);
    }
  }, [selectedEmailId]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Toast Notification Popup */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 px-4 py-3 rounded-xl bg-blue-950 border border-cyan-400 text-cyan-300 text-xs font-mono font-bold shadow-2xl animate-fadeIn">
          {toast.message}
        </div>
      )}

      {/* Navigation Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={analytics?.summary_stats}
        healthInfo={healthInfo}
        onRefresh={() => {
          fetchEmails();
          fetchAnalytics();
          fetchCalendar(selectedPort);
          fetchHealth();
        }}
        theme={theme}
        onToggleTheme={handleToggleTheme}
        onOpenUpload={() => setShowUploadModal(true)}
      />

      {/* Main Active Workspace View */}
      <main className="flex-1 flex overflow-hidden bg-slate-950">
        {activeTab === 'inbox' && (
          <InboxWorkspace
            emails={emails}
            selectedEmailId={selectedEmailId}
            onSelectEmail={(id) => setSelectedEmailId(id)}
            emailDetail={emailDetail}
            onOpenOverrideModal={() => setShowOverrideModal(true)}
            onUploadSuccess={handleUploadSuccess}
            healthInfo={healthInfo}
          />
        )}

        {activeTab === 'human_review' && (
          <HumanReviewQueue
            emails={emails}
            onReviewEmail={(id) => {
              setSelectedEmailId(id);
              setShowOverrideModal(true);
            }}
            reflectionsData={reflectionsData}
            onRefreshReflections={fetchReflections}
          />
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

        {activeTab === 'admin' && (
          <AdminDashboard
            analytics={analytics}
            emails={emails}
            selectedEmailId={selectedEmailId}
            onSelectEmail={(id) => {
              setSelectedEmailId(id);
              fetchEmailDetail(id);
            }}
            emailDetail={emailDetail}
            automationLevel={automationLevel}
            onAutomationLevelChange={(level) => setAutomationLevel(level)}
            onRunSelfEvaluate={handleRunSelfEvaluate}
            evaluationData={evaluationData}
            loadingEval={loadingEval}
            showToast={showToast}
            fetchEmails={fetchEmails}
            fetchEmailDetail={fetchEmailDetail}
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

      {/* Dynamic Document Upload Modal */}
      <UploadDocsModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  );
}
