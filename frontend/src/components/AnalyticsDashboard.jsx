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
      <div className="p-4 border-b border-slate-800 glass-panel flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2.5">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <span>Operational Analytics & Manifest Reporting</span>
          </h2>
          <p className="text-sm text-slate-300 mt-0.5">
            Real-time discrepancy stats, vessel manifest compliance, and company order lifecycle tracking.
          </p>
        </div>
      </div>

      {/* Main Dashboard Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Metric Summary Cards */}
        <div className="grid grid-cols-5 gap-4">
          <div className="glass-card p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Total Inbox Emails</span>
            <div className="text-3xl font-extrabold text-slate-100 font-mono mt-1.5">{stats.total_emails || 0}</div>
            <span className="text-xs text-slate-400 block mt-1">Processed by AI Triage</span>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">SI vs BL Verification Requests</span>
            <div className="text-3xl font-extrabold text-cyan-400 font-mono mt-1.5">{stats.comparison_requests || 0}</div>
            <span className="text-xs text-cyan-300/90 block mt-1">Doc comparison requests</span>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Clean Matches</span>
            <div className="text-3xl font-extrabold text-emerald-400 font-mono mt-1.5">{stats.matched_count || 0}</div>
            <span className="text-xs text-emerald-300/90 block mt-1">Ready for BL Release</span>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Discrepancies Flagged</span>
            <div className="text-3xl font-extrabold text-rose-400 font-mono mt-1.5">{stats.mismatch_count || 0}</div>
            <span className="text-xs text-rose-300/90 block mt-1">Revision Requested</span>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Human Escalations</span>
            <div className="text-3xl font-extrabold text-amber-400 font-mono mt-1.5">{stats.human_review_count || 0}</div>
            <span className="text-xs text-amber-300/90 block mt-1">Human Review Queue</span>
          </div>
        </div>

        {/* Vessel Manifest Status Report */}
        <div className="glass-card rounded-xl border border-slate-800 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <Ship className="w-4 h-4 text-cyan-400" />
              <span>Vessel Manifest Compliance Report</span>
            </h3>
            <span className="text-xs text-slate-300 font-mono font-medium">Aggregated per Vessel Voyage</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-slate-300 font-mono text-xs uppercase tracking-wider">
                  <th className="py-3 px-4">Vessel Name</th>
                  <th className="py-3 px-4">Total Shipments</th>
                  <th className="py-3 px-4">Matches</th>
                  <th className="py-3 px-4">Mismatches</th>
                  <th className="py-3 px-4">Human Escalations</th>
                  <th className="py-3 px-4 text-right">Compliance %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {(vessel_manifests || []).map((v, i) => {
                  const total = v.total_shipments || 1;
                  const compliance = Math.round((v.matched / total) * 100);
                  return (
                    <tr key={i} className="hover:bg-slate-900/60 transition">
                      <td className="py-3 px-4 font-bold text-slate-100 text-sm">{v.vessel}</td>
                      <td className="py-3 px-4 font-bold text-slate-200 text-sm">{v.total_shipments}</td>
                      <td className="py-3 px-4 font-extrabold text-emerald-400 text-sm">{v.matched}</td>
                      <td className="py-3 px-4 font-extrabold text-rose-400 text-sm">{v.mismatched}</td>
                      <td className="py-3 px-4 font-extrabold text-amber-400 text-sm">{v.human_review}</td>
                      <td className="py-3 px-4 text-right">
                        <span className={`px-2.5 py-1 rounded font-bold text-xs ${
                          compliance >= 80 ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-700' : 'bg-amber-950/80 text-amber-300 border border-amber-700'
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
            <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <Building2 className="w-4 h-4 text-indigo-400" />
              <span>Company Order End-to-End Tracking</span>
            </h3>
            <span className="text-xs text-slate-300 font-mono font-medium">Client Account Lifecycle</span>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {(company_orders || []).map((c, i) => (
              <div key={i} className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/90 flex items-center justify-between hover:border-slate-700 transition">
                <div>
                  <h4 className="text-sm font-bold text-white tracking-tight">{c.company}</h4>
                  <span className="text-xs text-slate-300 font-mono font-medium block mt-1">
                    Orders Tracked: <span className="font-bold text-cyan-300">{c.total_orders}</span>
                  </span>
                </div>
                <span className="badge-match px-2.5 py-1 rounded-md text-xs font-mono font-bold">
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
