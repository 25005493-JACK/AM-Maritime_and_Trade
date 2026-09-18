import React, { useState } from 'react';
import { 
  Award, 
  Play, 
  CheckCircle2, 
  XCircle, 
  Sparkles, 
  Terminal, 
  RefreshCw 
} from 'lucide-react';

export default function SelfEvaluationView({ onRunSelfEvaluate, evaluationData, loading }) {
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
            Automated POST <code className="text-cyan-400 font-mono">/submit</code> evaluation pipeline as specified in the hackathon guide.
          </p>
        </div>

        <button
          onClick={onRunSelfEvaluate}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-600 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 text-slate-950 font-bold text-xs flex items-center space-x-2 shadow-lg shadow-amber-950/40 transition disabled:opacity-50"
        >
          {loading ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4 fill-current" />
          )}
          <span>{loading ? 'Evaluating...' : 'Run Benchmark Evaluation'}</span>
        </button>
      </div>

      {/* Main Scoreboard Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {evaluationData ? (
          <>
            {/* Top Score Banner */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-amber-950/20 to-slate-900 border border-amber-500/40 shadow-xl flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 rounded-2xl bg-amber-500/20 border border-amber-500/40 text-amber-400 flex items-center justify-center font-mono font-extrabold text-2xl shadow-inner">
                  {evaluationData.score_report?.overall_score}%
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
                    <span>Overall Benchmark Score</span>
                    <Sparkles className="w-4 h-4 text-amber-400" />
                  </h3>
                  <p className="text-xs text-slate-300 mt-1">
                    {evaluationData.score_report?.message}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-6 font-mono text-center">
                <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">Classification Acc</span>
                  <strong className="text-cyan-400 text-lg">{evaluationData.score_report?.classification_accuracy_pct}%</strong>
                </div>
                <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">Mismatch Recall</span>
                  <strong className="text-emerald-400 text-lg">{evaluationData.score_report?.mismatch_recall_pct}%</strong>
                </div>
                <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">Human Review Acc</span>
                  <strong className="text-amber-400 text-lg">{evaluationData.score_report?.human_review_accuracy_pct}%</strong>
                </div>
              </div>
            </div>

            {/* Email Test Breakdown Table */}
            <div className="glass-card rounded-xl border border-slate-800 p-5 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <span>Submitted Payload Score Breakdown (POST /submit)</span>
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono">
                      <th className="py-2.5 px-3">Email ID</th>
                      <th className="py-2.5 px-3">Ground Truth Category</th>
                      <th className="py-2.5 px-3">Expected Verification Status</th>
                      <th className="py-2.5 px-3">Classification Test</th>
                      <th className="py-2.5 px-3 text-right">Verification Test</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    {(evaluationData.score_report?.details || []).map((det, i) => (
                      <tr key={i} className="hover:bg-slate-900/50">
                        <td className="py-2.5 px-3 font-semibold text-cyan-400">{det.email_id}</td>
                        <td className="py-2.5 px-3">{det.truth_category}</td>
                        <td className="py-2.5 px-3">{det.truth_status}</td>
                        <td className="py-2.5 px-3">
                          {det.passed_classification ? (
                            <span className="text-emerald-400 flex items-center space-x-1">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>PASS</span>
                            </span>
                          ) : (
                            <span className="text-rose-400 flex items-center space-x-1">
                              <XCircle className="w-3.5 h-3.5" />
                              <span>FAIL</span>
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          {det.passed_verification ? (
                            <span className="text-emerald-400 inline-flex items-center space-x-1">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>PASS</span>
                            </span>
                          ) : (
                            <span className="text-rose-400 inline-flex items-center space-x-1">
                              <XCircle className="w-3.5 h-3.5" />
                              <span>FAIL</span>
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-24 text-slate-500">
            <Award className="w-16 h-16 stroke-[1.2] mb-3 text-slate-600" />
            <h3 className="text-base font-semibold text-slate-300">Ready to Evaluate Submission</h3>
            <p className="text-xs text-slate-500 max-w-md text-center mt-1">
              Click "Run Benchmark Evaluation" above to generate the submission payload and evaluate accuracy against ground truth.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
