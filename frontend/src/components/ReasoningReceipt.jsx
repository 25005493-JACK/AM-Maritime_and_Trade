import React, { useEffect, useState } from 'react';
import {
  AlertOctagon,
  ChevronDown,
  ChevronRight,
  Cpu,
  Download,
  FileJson,
  Quote,
  ShieldCheck,
  UserCheck,
} from 'lucide-react';
import { apiFetch } from '../api.js';

const PATH_STYLES = {
  rule: { label: 'RULE', cls: 'bg-slate-800/80 text-slate-300 border-slate-600/60' },
  ai: { label: 'AI', cls: 'bg-purple-950/70 text-purple-300 border-purple-600/60' },
  human: { label: 'HUMAN', cls: 'bg-blue-950/70 text-blue-300 border-blue-600/60' },
};

const PATH_ICONS = { rule: ShieldCheck, ai: Cpu, human: UserCheck };

export function DecisionPathTag({ path }) {
  const style = PATH_STYLES[path] || PATH_STYLES.rule;
  const Icon = PATH_ICONS[path] || ShieldCheck;
  return (
    <span className={`inline-flex items-center gap-1 font-mono text-[10px] px-1.5 py-0.5 rounded border ${style.cls}`}>
      <Icon className="w-3 h-3" />
      {style.label}
    </span>
  );
}

export function ValidatorRow({ validators }) {
  return (
    <span className="inline-flex items-center gap-2">
      {(validators || []).map((validator) => (
        <span
          key={validator.name}
          title={validator.detail || ''}
          className={`font-mono text-[10px] px-1.5 py-0.5 rounded border ${
            validator.status === 'pass'
              ? 'border-emerald-700/60 bg-emerald-950/40 text-emerald-300'
              : 'border-rose-700/60 bg-rose-950/40 text-rose-300'
          }`}
        >
          {validator.name} {validator.status === 'pass' ? '✓' : '✗'}
        </span>
      ))}
    </span>
  );
}

export function RefusalCertificatePanel({ certificate }) {
  if (!certificate) return null;
  const recipientTone = {
    carrier: 'text-cyan-300 border-cyan-700/60 bg-cyan-950/40',
    shipper: 'text-indigo-300 border-indigo-700/60 bg-indigo-950/40',
    internal_ops: 'text-slate-300 border-slate-600/60 bg-slate-900/60',
  }[certificate.suggested_recipient] || 'text-slate-300 border-slate-600/60 bg-slate-900/60';

  return (
    <div className="rounded-xl border border-rose-600/50 bg-rose-950/20 p-3 space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <AlertOctagon className="w-4 h-4 text-rose-400" />
        <span className="text-xs font-bold uppercase tracking-wider text-rose-200">AI refusal certificate</span>
        <span className={`font-mono text-[10px] px-2 py-0.5 rounded border ${recipientTone}`}>
          suggested recipient: {certificate.suggested_recipient}
        </span>
        <span className="font-mono text-[10px] text-slate-400">
          {certificate.consecutive_ai_failures}/{certificate.threshold} consecutive validator failures
        </span>
      </div>

      <p className="text-[11px] text-rose-100">{certificate.reason}</p>
      <p className="text-[11px] text-slate-400">{certificate.recipient_rationale}</p>

      {certificate.failed_fields?.length > 0 && (
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2 overflow-auto">
          <table className="w-full text-[11px] font-mono">
            <thead>
              <tr className="text-slate-500">
                <th className="text-left font-medium pb-1">field</th>
                <th className="text-left font-medium pb-1">attempted</th>
                <th className="text-left font-medium pb-1">why it failed</th>
              </tr>
            </thead>
            <tbody>
              {certificate.failed_fields.map((failure, idx) => (
                <tr key={`${failure.field_name}-${idx}`} className="border-t border-slate-800/60">
                  <td className="py-1 pr-2 text-slate-200">{failure.field_name}</td>
                  <td className="py-1 pr-2 text-slate-400">{failure.attempted_value ?? '(none)'}</td>
                  <td className="py-1 text-rose-300">{failure.why_failed}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-400 font-mono">
        <span>estimated delay: {certificate.estimated_delay_hours}h</span>
        <span className="text-slate-600">·</span>
        <span>{certificate.estimated_delay_basis}</span>
      </div>

      {certificate.missing_or_unclear?.length > 0 && (
        <p className="text-[11px] text-slate-300">
          missing / unclear: <span className="font-mono">{certificate.missing_or_unclear.join(', ')}</span>
        </p>
      )}

      <ul className="text-[11px] text-slate-400 list-disc list-inside">
        {(certificate.what_would_unblock || []).map((item) => <li key={item}>{item}</li>)}
      </ul>
      <p className="text-[10px] text-slate-500 italic">{certificate.notice}</p>
    </div>
  );
}

export function ReceiptRows({ fields }) {
  const [openField, setOpenField] = useState(null);
  return (
    <div className="divide-y divide-slate-800/70">
      {(fields || []).map((row) => {
        const isOpen = openField === row.field_name;
        const evidence = row.source_evidence;
        return (
          <div key={`${row.email_id}-${row.field_name}`} className="py-2">
            <button
              type="button"
              onClick={() => setOpenField(isOpen ? null : row.field_name)}
              className="w-full text-left flex flex-wrap items-center gap-2"
            >
              {isOpen ? <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                      : <ChevronRight className="w-3.5 h-3.5 text-slate-500" />}
              <span className="text-xs font-semibold text-slate-100 w-36">{row.field_name}</span>
              <DecisionPathTag path={row.decision_path} />
              {row.rule_matched && (
                <span className="font-mono text-[10px] text-slate-500">{row.rule_matched}</span>
              )}
              <ValidatorRow validators={row.validators} />
              {row.dcsa_field && (
                <span className="font-mono text-[10px] text-cyan-300/80">DCSA: {row.dcsa_field}</span>
              )}
              {row.policy_tag && (
                <span className="font-mono text-[10px] px-1.5 py-0.5 rounded border border-indigo-700/60 bg-indigo-950/40 text-indigo-300">
                  {row.policy_tag}
                </span>
              )}
              {row.learned_note && (
                <span className="font-mono text-[10px] px-1.5 py-0.5 rounded border border-purple-700/60 bg-purple-950/40 text-purple-300 flex items-center gap-1">
                  <span>🧠 Memory Applied</span>
                </span>
              )}
              {row.token_cost !== null && row.token_cost !== undefined && (
                <span className="font-mono text-[10px] text-purple-300">
                  {row.token_cost} tokens · {row.latency_ms}ms
                </span>
              )}
            </button>

            {isOpen && (
              <div className="mt-2 ml-5 space-y-1.5 text-[11px]">
                <div className="font-mono text-slate-300">
                  value: <span className="text-slate-100">{row.value ?? '(none)'}</span>
                </div>
                {evidence ? (
                  <div className="flex items-start gap-1.5 text-slate-400">
                    <Quote className="w-3 h-3 mt-0.5 text-cyan-400 shrink-0" />
                    <span>
                      {evidence.document} · offset {evidence.char_offset} · line {evidence.line_number}
                      <span className="block italic text-slate-300">&ldquo;{evidence.exact_text}&rdquo;</span>
                    </span>
                  </div>
                ) : (
                  <div className="text-amber-300">No source span located for this value.</div>
                )}
                {row.learned_note && (
                  <div className="p-2 rounded-lg bg-purple-950/50 border border-purple-800/60 text-purple-200">
                    <div className="font-semibold text-purple-300 flex items-center gap-1 mb-0.5">
                      <span>🧠 Learned from a prior correction:</span>
                    </div>
                    <div className="italic text-[11px] text-purple-100/90 pl-3 border-l-2 border-purple-500">
                      &ldquo;{row.retrieved_reflections?.[0]?.reflection_text || row.learned_note}&rdquo;
                    </div>
                    {row.retrieved_reflections?.[0]?.times_retrieved !== undefined && (
                      <span className="block mt-1 font-mono text-[10px] text-purple-400">
                        Memory reuse count: {row.retrieved_reflections[0].times_retrieved} retrievals
                      </span>
                    )}
                  </div>
                )}
                {row.policy_routing && (
                  <div className="p-2 rounded-lg bg-indigo-950/40 border border-indigo-800/50 text-[10px] font-mono text-indigo-200 space-y-0.5">
                    <div className="font-bold text-indigo-300">
                      Bayesian Routing Policy: {row.policy_tag}
                    </div>
                    <div className="text-slate-400">
                      Beta posterior: &alpha;={row.policy_routing.alpha}, &beta;={row.policy_routing.beta} · 
                      Mean trust: {Math.round((row.policy_routing.mean_trust || 0.5) * 100)}%
                      {row.policy_routing.sampled_trust !== undefined && (
                        <span> · Thompson sample: {Math.round(row.policy_routing.sampled_trust * 100)}%</span>
                      )}
                    </div>
                    {row.policy_routing.reason && (
                      <div className="text-amber-300/90 mt-0.5">{row.policy_routing.reason}</div>
                    )}
                  </div>
                )}
                {row.decision_path === 'ai' && (
                  <div className="font-mono text-[10px] text-purple-300/90">
                    ai read: {(row.ai_fields_read || []).join(', ') || '—'} · rules handled:{' '}
                    {(row.ai_fields_skipped || []).join(', ') || '—'} · provider: {row.ai_provider}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function ReasoningReceipt({ shipmentId, emailId, receipt: providedReceipt = null, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const [receipt, setReceipt] = useState(providedReceipt);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (providedReceipt) {
      setReceipt(providedReceipt);
      return undefined;
    }
    if (!open || (!shipmentId && !emailId) || receipt) return undefined;
    let cancelled = false;
    setLoading(true);
    const url = shipmentId
      ? `/api/shipments/${shipmentId}/receipt`
      : `/api/verify/${emailId}/receipt`;
    apiFetch(url)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error('failed'))))
      .then((data) => { if (!cancelled) setReceipt(data); })
      .catch(() => { if (!cancelled) setReceipt(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [open, shipmentId, emailId, receipt, providedReceipt]);

  const summary = receipt?.summary;
  const download = () => {
    if (!receipt) return;
    const blob = new Blob([JSON.stringify(receipt, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${shipmentId || emailId || 'shipment'}.reasoning-receipt.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="glass-card rounded-xl border border-slate-800 overflow-hidden">
      <div className="p-3 flex flex-wrap items-center justify-between gap-2 border-b border-slate-800">
        <button
          type="button"
          onClick={() => setOpen((prev) => !prev)}
          className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-200"
        >
          {open ? <ChevronDown className="w-4 h-4 text-cyan-400" /> : <ChevronRight className="w-4 h-4 text-cyan-400" />}
          <FileJson className="w-4 h-4 text-cyan-400" />
          <span>Reasoning Receipt</span>
          {summary && (
            <span className="font-mono text-[10px] text-slate-400 normal-case">
              {summary.resolved_by_rules} rule / {summary.resolved_by_ai} AI / {summary.resolved_by_human} human
            </span>
          )}
        </button>
        <button
          type="button"
          onClick={download}
          disabled={!receipt}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold transition ${
            receipt ? 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                    : 'bg-slate-900 text-slate-600 cursor-not-allowed'
          }`}
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export receipt</span>
        </button>
      </div>

      {open && (
        <div className="p-3 space-y-3">
          {loading && <p className="text-xs text-slate-400">Building receipt…</p>}
          {!loading && !receipt && <p className="text-xs text-amber-300">No receipt available for this shipment.</p>}
          {receipt && (
            <>
              <ReceiptRows fields={receipt.fields} />
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2 text-[11px] text-slate-300 font-mono">
                {summary?.summary_line}
                <span className="block text-slate-500">{summary?.tokens_note}</span>
              </div>
              <RefusalCertificatePanel certificate={receipt.refusal_certificate} />
            </>
          )}
        </div>
      )}
    </div>
  );
}
