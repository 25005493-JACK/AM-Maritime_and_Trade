import React, { useState } from 'react';
import { 
  GitCommit, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  UserCheck, 
  FileText, 
  Ship, 
  ShieldCheck, 
  ChevronRight,
  Filter
} from 'lucide-react';

export default function ShipmentTimeline({ emails }) {
  const compEmails = (emails || []).filter(e => e.has_attachments || e.verification);
  const [selectedEmailId, setSelectedEmailId] = useState(compEmails[0]?.id || '');

  const activeEmail = compEmails.find(e => e.id === selectedEmailId) || compEmails[0];

  if (!activeEmail) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-slate-500 bg-slate-950">
        <GitCommit className="w-16 h-16 stroke-[1.2] mb-3 text-slate-600" />
        <h3 className="text-base font-semibold text-slate-300">No Shipment Selected</h3>
      </div>
    );
  }

  const verif = activeEmail.verification || {};
  const isMatch = verif.status === 'NO_MISMATCH_DETECTED';
  const isHuman = verif.status === 'HUMAN_REVIEW_REQUIRED';

  const milestones = [
    {
      id: 1,
      title: 'Booking Confirmed & Allocation Scheduled',
      timestamp: new Date(new Date(activeEmail.timestamp).getTime() - 86400000).toISOString(),
      actor: 'Carrier Booking System',
      status: 'Completed',
      icon: Ship,
      details: `Vessel: ${activeEmail.vessel || 'MSC ISABELLA'} ${activeEmail.voyage || 'v.240E'} | Company: ${activeEmail.company || 'Global Traders Inc'}`
    },
    {
      id: 2,
      title: 'Shipping Instruction (SI) Received & Ingested',
      timestamp: activeEmail.timestamp,
      actor: activeEmail.sender,
      status: 'Completed',
      icon: FileText,
      details: `Subject: "${activeEmail.subject}" | 7 Reference fields extracted`
    },
    {
      id: 3,
      title: 'Draft Bill of Lading (BL) AI Verification Checked',
      timestamp: new Date(new Date(activeEmail.timestamp).getTime() + 1800000).toISOString(),
      actor: 'Antigravity Verification Pipeline',
      status: isMatch ? 'Passed' : isHuman ? 'Escalated' : 'Discrepancy Flagged',
      icon: isMatch ? CheckCircle2 : AlertTriangle,
      details: isMatch 
        ? 'All 7 standard fields agree perfectly (Shipper, Consignee, Notify, POL, POD, Containers, Weight)'
        : `Verification result: ${verif.summary_message || 'Field differences detected'}`
    },
    {
      id: 4,
      title: 'Human-in-the-Loop Audit & Override Gate',
      timestamp: new Date(new Date(activeEmail.timestamp).getTime() + 3600000).toISOString(),
      actor: isHuman ? 'Pending Operational Review' : 'Automated Policy Check',
      status: isHuman ? 'Action Required' : 'Approved',
      icon: UserCheck,
      details: isHuman 
        ? `Escalated reason: ${verif.human_review_reasons?.join(' | ') || 'Corrupted stream or blank value'}`
        : 'Rule-based audit trail validated against DCSA standards'
    },
    {
      id: 5,
      title: 'Final Bill of Lading Printing & Container Release',
      timestamp: new Date(new Date(activeEmail.timestamp).getTime() + 7200000).toISOString(),
      actor: 'Documentation Desk',
      status: isMatch ? 'Ready for Release' : 'Pending Revision',
      icon: ShieldCheck,
      details: isMatch 
        ? 'Released to Shipper. Certificate of Origin & Shipment Advice finalized.'
        : 'Waiting for revised draft BL from carrier.'
    }
  ];

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950">
      {/* Header Bar */}
      <div className="p-4 border-b border-slate-800 glass-panel flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <GitCommit className="w-5 h-5 text-cyan-400" />
            <span>End-to-End Shipment Audit & Lifecycle Timeline</span>
          </h2>
          <p className="text-xs text-slate-400">
            Node tree tracking booking, SI submission, BL verification, human review, and document release.
          </p>
        </div>

        {/* Shipment Selector */}
        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-700 px-3 py-1.5 rounded-xl">
          <Filter className="w-4 h-4 text-cyan-400" />
          <span className="text-xs text-slate-400 font-medium">Select Shipment:</span>
          <select
            value={selectedEmailId}
            onChange={(e) => setSelectedEmailId(e.target.value)}
            className="bg-transparent text-xs font-bold text-cyan-300 focus:outline-none cursor-pointer"
          >
            {compEmails.map((e) => (
              <option key={e.id} value={e.id} className="bg-slate-900 text-slate-200">
                {e.id} - {e.company} ({e.vessel})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Timeline Content Body */}
      <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full space-y-6">
        {/* Active Shipment Banner */}
        <div className="p-4 rounded-xl glass-card border border-slate-800 flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-mono text-xs text-cyan-400 font-bold">{activeEmail.id}</span>
              <h3 className="text-sm font-bold text-slate-100">{activeEmail.subject}</h3>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Shipper: <strong className="text-slate-200">{activeEmail.company}</strong> | Vessel: <strong className="text-cyan-400">{activeEmail.vessel} {activeEmail.voyage}</strong>
            </p>
          </div>

          <div className="shrink-0">
            {isMatch ? (
              <span className="badge-match px-3 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Verified Match</span>
              </span>
            ) : isHuman ? (
              <span className="badge-warning px-3 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1 font-mono">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Human Review</span>
              </span>
            ) : (
              <span className="badge-mismatch px-3 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1 font-mono mismatch-glow">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Discrepancy Flagged</span>
              </span>
            )}
          </div>
        </div>

        {/* Milestone Node Tree */}
        <div className="relative border-l-2 border-slate-800 ml-4 pl-6 space-y-6">
          {milestones.map((m) => {
            const Icon = m.icon;
            return (
              <div key={m.id} className="relative group">
                {/* Node Bullet */}
                <div className={`absolute -left-[35px] top-1 w-8 h-8 rounded-full flex items-center justify-center border-2 transition ${
                  m.status === 'Completed' || m.status === 'Passed' || m.status === 'Approved' || m.status === 'Ready for Release'
                    ? 'bg-emerald-950 border-emerald-500 text-emerald-400'
                    : m.status === 'Action Required' || m.status === 'Escalated'
                    ? 'bg-amber-950 border-amber-500 text-amber-400'
                    : 'bg-rose-950 border-rose-500 text-rose-400'
                }`}>
                  <Icon className="w-4 h-4" />
                </div>

                {/* Card Container */}
                <div className="glass-card p-4 rounded-xl border border-slate-800/80 space-y-2 hover:border-slate-700 transition">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-slate-200">{m.title}</h4>
                    <span className="text-[11px] font-mono text-slate-500 flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(m.timestamp).toLocaleString()}</span>
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 font-mono bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
                    {m.details}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <span>Actor / System: <strong className="text-slate-400">{m.actor}</strong></span>
                    <span className={`px-2 py-0.5 rounded font-mono font-semibold ${
                      m.status === 'Completed' || m.status === 'Passed' || m.status === 'Approved'
                        ? 'text-emerald-400 bg-emerald-950/40'
                        : 'text-amber-400 bg-amber-950/40'
                    }`}>
                      {m.status}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
