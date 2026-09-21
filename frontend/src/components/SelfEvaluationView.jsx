import React from 'react';
import { 
  Award, 
  Play, 
  CheckCircle2, 
  XCircle, 
  Sparkles, 
  Terminal, 
  RefreshCw,
  Download,
  ShieldCheck,
  AlertTriangle,
  FileCheck,
  Layers
} from 'lucide-react';

export default function SelfEvaluationView({ onRunSelfEvaluate, evaluationData, loading }) {
  const report = evaluationData?.score_report;

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950">
      {/* Header Bar */}
      <div className="p-4 border-b border-slate-800 glass-panel flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <Award className="w-5 h-5 text-amber-400" />
            <span>Self-Evaluation Benchmark Scoreboard</span>
          </h2>
          <p className="text-xs text-slate-400">
            Autonomous scoring engine verifying all 520 inbox emails & 250 attachments against official Averis x Monash Hackathon 2026 standards.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <a
            href="/api/submission.json"
            download="submission.json"
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs flex items-center space-x-2 border border-slate-700 shadow-sm transition"
          >
            <Download className="w-4 h-4 text-cyan-400" />
            <span>Download submission.json</span>
          </a>

          <button
            onClick={onRunSelfEvaluate}
            disabled={loading}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-600 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 text-slate-950 font-bold text-xs flex items-center space-x-2 shadow-lg shadow-amber-950/40 transition disabled:opacity-50 active:scale-95"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4 fill-current" />
            )}
            <span>{loading ? 'Evaluating 520 Emails...' : 'Run Benchmark Evaluation'}</span>
          </button>
        </div>
      </div>

      {/* Main Scoreboard Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {report ? (
          <>
            {/* Top Score Banner */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-amber-950/20 to-slate-900 border border-amber-500/40 shadow-xl flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-20 h-20 rounded-2xl bg-amber-500/20 border border-amber-500/40 text-amber-400 flex flex-col items-center justify-center font-mono font-extrabold text-3xl shadow-inner">
                  <span>{report.overall_score}%</span>
                  <span className="text-[10px] font-sans text-amber-300 font-normal">FINAL SCORE</span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
                    <span>Benchmark Verification Complete</span>
                    <Sparkles className="w-4 h-4 text-amber-400" />
                  </h3>
                  <p className="text-xs text-slate-300 mt-1 max-w-lg">
                    {report.message} Scored 50% end-to-end defect catching + 30% Stage-1 macro-F1 + 20% Stage-3 defect-F1.
                  </p>
                  <div className="flex items-center space-x-4 mt-2 text-xs font-mono text-slate-400">
                    <span>Total Emails: <strong className="text-cyan-400">{report.total_emails_processed}</strong></span>
                    <span>•</span>
                    <span>BL Checks: <strong className="text-indigo-400">{report.bl_comparison_total}</strong></span>
                    <span>•</span>
                    <span>Format: <strong className="text-emerald-400">sample_submission.json compliant</strong></span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 font-mono text-center">
                <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-400 block uppercase font-sans font-bold">Stage 1 (Macro-F1)</span>
                  <strong className="text-cyan-400 text-xl">{report.stage1_classification_f1}%</strong>
                </div>
                <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-400 block uppercase font-sans font-bold">Stage 3 (Defect-F1)</span>
                  <strong className="text-emerald-400 text-xl">{report.stage3_defect_f1}%</strong>
                </div>
                <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-400 block uppercase font-sans font-bold">Reliability Axis</span>
                  <strong className="text-amber-400 text-xl">{report.reliability_pct}%</strong>
                </div>
              </div>
            </div>

            {/* Verification Breakdown Grid */}
            <div className="grid grid-cols-3 gap-5">
              {/* Scoreboard Outcome Breakdown */}
              <div className="glass-card rounded-xl border border-slate-800 p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-cyan-400" />
                    <span>BL Comparison Outcomes</span>
                  </h4>
                  <span className="text-xs font-mono text-slate-500">{report.bl_comparison_total} items</span>
                </div>
                <div className="space-y-2 font-mono text-xs">
                  <div className="flex items-center justify-between p-2 rounded bg-emerald-950/30 border border-emerald-500/30 text-emerald-300">
                    <span>OK (No Mismatch)</span>
                    <strong className="text-sm">{report.scoreboard?.OK || 0}</strong>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-rose-950/30 border border-rose-500/30 text-rose-300">
                    <span>MISMATCH (Defects Flagged)</span>
                    <strong className="text-sm">{report.scoreboard?.MISMATCH || 0}</strong>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-amber-950/30 border border-amber-500/30 text-amber-300">
                    <span>NEEDS REVIEW (Escalated)</span>
                    <strong className="text-sm">{report.scoreboard?.NEEDS_REVIEW || 0}</strong>
                  </div>
                </div>
              </div>

              {/* Needs Review Reasons Breakdown */}
              <div className="glass-card rounded-xl border border-slate-800 p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <span>Reliability Escalations</span>
                  </h4>
                  <span className="text-xs font-mono text-slate-500">4 Core Reasons</span>
                </div>
                <div className="space-y-2 font-mono text-xs">
                  {Object.entries(report.review_reasons_breakdown || {}).map(([reason, count]) => (
                    <div key={reason} className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                      <span className="text-amber-400 font-semibold">{reason}</span>
                      <strong className="text-slate-100">{count}</strong>
                    </div>
                  ))}
                </div>
              </div>

              {/* Defect Fields Caught Breakdown */}
              <div className="glass-card rounded-xl border border-slate-800 p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                    <FileCheck className="w-4 h-4 text-indigo-400" />
                    <span>Discrepancy Fields Caught</span>
                  </h4>
                  <span className="text-xs font-mono text-slate-500">7 Fields</span>
                </div>
                <div className="space-y-1.5 font-mono text-xs max-h-48 overflow-y-auto">
                  {Object.entries(report.defect_field_counts || {}).map(([f, count]) => (
                    <div key={f} className="flex items-center justify-between p-1.5 rounded bg-slate-900/60 border border-slate-800/80 text-slate-300">
                      <span className="text-slate-300">{f}</span>
                      <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 font-bold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Category Distribution Bar */}
            <div className="glass-card rounded-xl border border-slate-800 p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  <span>5-Category Inbox Ingestion & Classification Distribution</span>
                </h4>
                <span className="text-xs font-mono text-slate-400">Total: 520 Emails</span>
              </div>
              <div className="grid grid-cols-5 gap-3 font-mono text-center text-xs">
                {Object.entries(report.category_distribution || {}).map(([cat, count]) => (
                  <div key={cat} className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[11px] text-slate-400 block font-semibold truncate">{cat}</span>
                    <strong className="text-cyan-400 text-lg">{count}</strong>
                    <span className="text-[10px] text-slate-500 block">({((count / 520) * 100).toFixed(1)}%)</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-24 text-slate-500">
            <Award className="w-16 h-16 stroke-[1.2] mb-3 text-slate-600" />
            <h3 className="text-base font-semibold text-slate-300">Ready to Evaluate Test Data Workflow</h3>
            <p className="text-xs text-slate-500 max-w-md text-center mt-1">
              Click "Run Benchmark Evaluation" above to process all 520 emails and multi-format attachments, score the verification results, and inspect the scoreboard.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
