import React, { useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  ShieldCheck, 
  Award, 
  Sliders,
  Terminal,
  Brain
} from 'lucide-react';

import AnalyticsDashboard from './AnalyticsDashboard.jsx';
import AgentLearningDashboard from './AgentLearningDashboard.jsx';
import SelfEvaluationView from './SelfEvaluationView.jsx';
import AutomationSlider from './AutomationSlider.jsx';
import RedTeamPanel from './RedTeamPanel.jsx';
import ReasoningReceipt from './ReasoningReceipt.jsx';

export default function AdminDashboard({
  analytics,
  selectedEmailId,
  emailDetail,
  automationLevel,
  onAutomationLevelChange,
  onRunSelfEvaluate,
  evaluationData,
  loadingEval,
  showToast,
  fetchEmails,
  fetchEmailDetail
}) {
  const [adminTab, setAdminTab] = useState('analytics'); // 'analytics', 'learning', 'trust', 'benchmark'

  const adminTabs = [
    { id: 'analytics', label: 'Vessel & Order Analytics', icon: BarChart3, badge: 'Overview' },
    { id: 'learning', label: 'Agent Self Learning', icon: TrendingUp, badge: 'Reflexion & Bayes' },
    { id: 'trust', label: 'Trust & AI Controls', icon: ShieldCheck, badge: 'L0-L3 Controls' },
    { id: 'benchmark', label: 'Self Evaluation Board', icon: Award, badge: 'Scoreboard' }
  ];

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* ADMIN TOP CONTROL BAR WITH TABS */}
      <div className="px-6 py-4 border-b border-blue-900/60 bg-slate-950 shrink-0 space-y-3 shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-extrabold text-slate-100 flex items-center space-x-2">
              <ShieldCheck className="w-5 h-5 text-indigo-400" />
              <span>Admin & System Governance Control Center</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Consolidated governance covering Vessel Analytics, Self-Learning Memory, Trust Controls, and Benchmark Evaluation.
            </p>
          </div>
        </div>

        {/* TOP BAR TABS */}
        <div className="flex items-center space-x-2 pt-1 border-t border-blue-900/40 overflow-x-auto no-scrollbar">
          {adminTabs.map((t) => {
            const Icon = t.icon;
            const isActive = adminTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setAdminTab(t.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-600 via-cyan-600 to-indigo-600 text-white border border-cyan-400 shadow-lg shadow-cyan-950/60 ring-1 ring-cyan-500/40'
                    : 'bg-slate-900/80 text-slate-400 hover:text-slate-100 hover:bg-slate-800 border border-blue-900/40'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-300' : 'text-slate-400'}`} />
                <span>{t.label}</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                  isActive ? 'bg-cyan-950 text-cyan-300 border-cyan-500/40' : 'bg-slate-950 text-slate-500 border-slate-800'
                }`}>
                  {t.badge}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ADMIN SUB-VIEW CONTENT AREA */}
      <div className="flex-1 overflow-y-auto">
        {adminTab === 'analytics' && (
          <AnalyticsDashboard analytics={analytics} />
        )}

        {adminTab === 'learning' && (
          <AgentLearningDashboard />
        )}

        {adminTab === 'trust' && (
          <div className="p-6 space-y-6 bg-slate-950">
            <div>
              <h2 className="text-sm font-bold text-slate-100">Trust &amp; AI Controls</h2>
              <p className="text-xs text-slate-400 mt-1">
                Auditable reasoning, adversarial rehearsal, and the automation license. All metrics derived directly from validator outcomes and loaded inbox data.
              </p>
            </div>

            <AutomationSlider
              level={automationLevel}
              onLevelChange={async (level) => {
                onAutomationLevelChange(level);
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

        {adminTab === 'benchmark' && (
          <SelfEvaluationView
            onRunSelfEvaluate={onRunSelfEvaluate}
            evaluationData={evaluationData}
            loading={loadingEval}
          />
        )}
      </div>
    </div>
  );
}
