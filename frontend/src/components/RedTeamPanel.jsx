import React, { useEffect, useState } from 'react';
import { AlertTriangle, Bug, Loader2, PlayCircle } from 'lucide-react';
import { ReceiptRows, RefusalCertificatePanel } from './ReasoningReceipt.jsx';

/**
 * Red Team rehearsal: mutate the documents, then let the SAME pipeline react.
 * Results reuse the shared receipt / certificate / comparison data, which is what
 * proves the pipeline handled the adversarial input itself.
 */
export default function RedTeamPanel({ emailId }) {
  const [transforms, setTransforms] = useState([]);
  const [running, setRunning] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/red-team/transforms')
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error('failed'))))
      .then((data) => setTransforms(data.transforms || []))
      .catch(() => setTransforms([]));
  }, []);

  const run = async (transform) => {
    if (!emailId) return;
    setRunning(transform);
    setError(null);
    try {
      const res = await fetch(`/api/shipments/${emailId}/red-team`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transform }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Red team run failed');
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err) {
      setError('Could not run the red team transform');
    } finally {
      setRunning(null);
    }
  };

  const statusChip = (status) => {
    const tone = status === 'OK' ? 'badge-match' : status === 'MISMATCH' ? 'badge-mismatch' : 'badge-warning';
    return <span className={`${tone} px-2 py-0.5 rounded text-[10px] font-mono`}>{status || '—'}</span>;
  };

  const mismatched = (result?.verification?.field_matrix || []).filter((row) => !row.is_match);

  return (
    <div className="glass-card rounded-xl border border-orange-500/40 overflow-hidden">
      <div className="p-3 bg-orange-950/20 border-b border-orange-500/30 flex items-center justify-between gap-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-orange-200 flex items-center space-x-2">
          <Bug className="w-4 h-4 text-orange-400" />
          <span>Red Team - adversarial rehearsal</span>
        </h3>
        <span className="font-mono text-[10px] text-slate-400">{emailId || 'no email selected'}</span>
      </div>

      <div className="p-3 space-y-3">
        <p className="text-[11px] text-slate-400">
          Each transform mutates the documents only, then re-runs the existing classifier, extractor,
          comparator and receipt/certificate paths. Nothing here is a separate demo pipeline.
        </p>

        <div className="flex flex-wrap gap-2">
          {transforms.map((transform) => (
            <button
              key={transform.id}
              type="button"
              disabled={!emailId || running === transform.id}
              onClick={() => run(transform.id)}
              title={transform.description}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-100 text-[11px] font-semibold transition"
            >
              {running === transform.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                         : <PlayCircle className="w-3.5 h-3.5 text-orange-400" />}
              {transform.label}
            </button>
          ))}
        </div>

        {error && <p className="text-[11px] text-rose-300">{error}</p>}

        {result && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
              <span className="font-mono">transform: {result.transform}</span>
              <span className="text-slate-600">·</span>
              <span>before</span> {statusChip(result.before.status)}
              <span>after</span> {statusChip(result.after.status)}
              {result.triggered.ai_invoked && (
                <span className="font-mono text-[10px] px-2 py-0.5 rounded border border-purple-600/60 bg-purple-950/40 text-purple-300">
                  AI fallback invoked: {(result.triggered.ai_fields_attempted || []).join(', ')}
                </span>
              )}
              {result.triggered.ai_accepted?.length > 0 && (
                <span className="font-mono text-[10px] px-2 py-0.5 rounded border border-emerald-600/60 bg-emerald-950/40 text-emerald-300">
                  evidence-validated: {result.triggered.ai_accepted.join(', ')}
                </span>
              )}
              {result.triggered.circuit_breaker_tripped && (
                <span className="font-mono text-[10px] px-2 py-0.5 rounded border border-rose-600/60 bg-rose-950/40 text-rose-300 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> circuit breaker tripped
                </span>
              )}
            </div>

            <p className="text-[11px] text-slate-500 font-mono">{(result.notes || []).join(' ')}</p>

            {mismatched.length > 0 && (
              <div className="rounded-lg border border-rose-800/50 bg-rose-950/20 p-2">
                <div className="text-[11px] font-semibold text-rose-200 mb-1">
                  Comparison result (unchanged comparison logic)
                </div>
                <table className="w-full text-[11px] font-mono">
                  <tbody>
                    {mismatched.map((row) => (
                      <tr key={row.field_key} className="border-t border-slate-800/60">
                        <td className="py-1 pr-2 text-slate-300">{row.field_name}</td>
                        <td className="py-1 pr-2 text-slate-400">{row.si_value}</td>
                        <td className="py-1 pr-2 text-slate-400">{row.bl_value}</td>
                        <td className="py-1 text-rose-300">{row.match_type}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {result.refusal_certificate && (
              <RefusalCertificatePanel certificate={result.refusal_certificate} />
            )}

            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3">
              <div className="text-[11px] font-semibold text-slate-200 mb-2">
                Reasoning receipt for the mutated document
              </div>
              <ReceiptRows fields={result.receipt?.fields} />
              <div className="mt-2 text-[11px] text-slate-400 font-mono">
                {result.receipt?.summary?.summary_line}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
