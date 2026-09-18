import React from 'react';
import { 
  BarChart3, 
  Ship, 
  Building2, 
  CheckCircle2, 
  AlertCircle, 
  HelpCircle, 
  Layers,
  ArrowUpRight
} from 'lucide-react';

export default function AnalyticsDashboard({ analytics }) {
  if (!analytics) return null;

  const { summary_stats, vessel_manifests, company_orders } = analytics;
  const stats = summary_stats || {};

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950">
      {/* Header Bar */}
      <div className="p-4 border-b border-slate-800 glass-panel flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <span>Operational Analytics & Manifest Reporting</span>
          </h2>
          <p className="text-xs text-slate-400">
            Real-time discrepancy stats, vessel manifest compliance, and company order lifecycle tracking.
          </p>
        </div>
      </div>

      {/* Main Dashboard Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Metric Summary Cards */}
        <div className="grid grid-cols-5 gap-4">
          <div className="glass-card p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-medium text-slate-400">Total Inbox Emails</span>
            <div className="text-2xl font-extrabold text-slate-100 font-mono mt-1">{stats.total_emails || 0}</div>
            <span className="text-[11px] text-slate-500 block mt-1">Processed by AI Triage</span>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-medium text-slate-400">SI vs BL Verification Requests</span>
            <div className="text-2xl font-extrabold text-cyan-400 font-mono mt-1">{stats.comparison_requests || 0}</div>
            <span className="text-[11px] text-cyan-500/80 block mt-1">Doc comparison requests</span>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-medium text-slate-400">Clean Matches</span>
            <div className="text-2xl font-extrabold text-emerald-400 font-mono mt-1">{stats.matched_count || 0}</div>
            <span className="text-[11px] text-emerald-500/80 block mt-1">Ready for BL Release</span>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-medium text-slate-400 font-mono">Discrepancies Flagged</span>
            <div className="text-2xl font-extrabold text-rose-400 font-mono mt-1">{stats.mismatch_count || 0}</div>
            <span className="text-[11px] text-rose-500/80 block mt-1">Revision Requested</span>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-medium text-slate-400">Human Escalations</span>
            <div className="text-2xl font-extrabold text-amber-400 font-mono mt-1">{stats.human_review_count || 0}</div>
            <span className="text-[11px] text-amber-500/80 block mt-1">Human Review Queue</span>
          </div>
        </div>

        {/* Vessel Manifest Status Report */}
        <div className="glass-card rounded-xl border border-slate-800 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
              <Ship className="w-4 h-4 text-cyan-400" />
              <span>Vessel Manifest Compliance Report</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">Aggregated per Vessel Voyage</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono">
                  <th className="py-2.5 px-3">Vessel Name</th>
                  <th className="py-2.5 px-3">Total Shipments</th>
                  <th className="py-2.5 px-3">Matches</th>
                  <th className="py-2.5 px-3">Mismatches</th>
                  <th className="py-2.5 px-3">Human Escalations</th>
                  <th className="py-2.5 px-3 text-right">Compliance %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {(vessel_manifests || []).map((v, i) => {
                  const total = v.total_shipments || 1;
                  const compliance = Math.round((v.matched / total) * 100);
                  return (
                    <tr key={i} className="hover:bg-slate-900/50">
                      <td className="py-2.5 px-3 font-semibold text-slate-100">{v.vessel}</td>
                      <td className="py-2.5 px-3">{v.total_shipments}</td>
                      <td className="py-2.5 px-3 text-emerald-400">{v.matched}</td>
                      <td className="py-2.5 px-3 text-rose-400">{v.mismatched}</td>
                      <td className="py-2.5 px-3 text-amber-400">{v.human_review}</td>
                      <td className="py-2.5 px-3 text-right">
                        <span className={`px-2 py-0.5 rounded font-bold ${
                          compliance >= 80 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}>
                          {compliance}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Company Order Tracking */}
        <div className="glass-card rounded-xl border border-slate-800 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
              <Building2 className="w-4 h-4 text-indigo-400" />
              <span>Company Order End-to-End Tracking</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">Client Account Lifecycle</span>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {(company_orders || []).map((c, i) => (
              <div key={i} className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-200">{c.company}</h4>
                  <span className="text-[11px] text-slate-400 font-mono block mt-0.5">
                    Orders Tracked: {c.total_orders}
                  </span>
                </div>
                <span className="badge-match px-2 py-0.5 rounded text-[10px] font-mono">
                  {c.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
