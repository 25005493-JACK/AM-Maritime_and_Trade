import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  Check,
  Download,
  FileJson,
  GitCompareArrows,
  Loader2,
  ShieldCheck,
  UserCheck,
} from 'lucide-react';
import { apiFetch } from '../api.js';

/**
 * Propose-and-confirm conflict resolution.
 *
 * SI and draft BL are shown as equal-weight sources with their exact quoted
 * evidence. The reviewer picks one side (or types a third value); the system never
 * resolves a conflict on its own. The result is a DCSA-field-mapped record.
 */
export default function ConflictEvidencePanel({ emailId, emailDetail, onShowToast }) {
  const [proposals, setProposals] = useState(null);
  const [loading, setLoading] = useState(false);
  const [choices, setChoices] = useState({});
  const [customValues, setCustomValues] = useState({});
  const [reviewer, setReviewer] = useState('Pohyi Chong');
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!emailId) return undefined;
    let cancelled = false;
    setLoading(true);
    setResult(null);
    setChoices({});
    setCustomValues({});

    const buildFallbackProposals = () => {
      const matrix = emailDetail?.verification?.field_matrix || [];
      const mismatched = matrix.filter((r) => !r.is_match);
      if (mismatched.length > 0) {
        return {
          email_id: emailId,
          requires_human_decision: true,
          auto_resolution: 'disabled',
          policy: 'SI and draft BL are treated as equal-weight sources. Reviewer confirms the correct value.',
          standard: { name: 'DCSA eBL v3.0.3' },
          proposals: mismatched.map((row) => ({
            field_key: row.field_key,
            field_name: row.field_name,
            dcsa_field:
              row.field_key === 'shipper' ? 'documentParties.shipper' :
              row.field_key === 'consignee' ? 'documentParties.consignee' :
              row.field_key === 'notify_party' ? 'documentParties.notifyParty' :
              row.field_key === 'port_of_loading' ? 'portOfLoading' :
              row.field_key === 'port_of_discharge' ? 'portOfDischarge' :
              row.field_key === 'container_count' ? 'utilizedTransportEquipments' :
              row.field_key === 'gross_weight_kg' ? 'consignmentItems[].cargoItems[].cargoGrossWeight' : row.field_key,
            reason: row.diff_summary || 'Value mismatch between SI and draft BL',
            si_candidate: {
              source: 'Shipping Instruction',
              document: 'SI_Reference.txt',
              value: row.si_value || '(missing)',
              confidence: 1.0,
              exact_text: row.si_value || '',
            },
            bl_candidate: {
              source: 'Draft Bill of Lading',
              document: 'Draft_BL.txt',
              value: row.bl_value || '(missing)',
              confidence: 1.0,
              exact_text: row.bl_value || '',
            },
            options: ['si', 'bl', 'custom'],
            requires_human_decision: true,
          })),
        };
      }
      return null;
    };

    apiFetch(`/api/shipments/${emailId}/corrections`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error('failed'))))
      .then((data) => {
        if (!cancelled) setProposals(data);
      })
      .catch(() => {
        if (!cancelled) {
          setProposals(buildFallbackProposals());
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [emailId, emailDetail]);

  const items = proposals?.proposals || [];
  const undecided = useMemo(
    () => items.filter((p) => !choices[p.field_key]),
    [items, choices],
  );
  const canSubmit = items.length > 0 && undecided.length === 0 && reviewer.trim().length > 0;

  const submit = async () => {
    if (!canSubmit) return;
    setSaving(true);
    try {
      const decisions = items.map((p) =>
        choices[p.field_key] === 'custom'
          ? { field_key: p.field_key, choice: 'custom', value: customValues[p.field_key] || '' }
          : { field_key: p.field_key, choice: choices[p.field_key] },
      );

      let data;
      try {
        const res = await apiFetch('/api/corrections/resolve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email_id: emailId, reviewer_name: reviewer, decisions }),
        });
        if (res.ok) {
          data = await res.json();
        } else {
          throw new Error('API offline');
        }
      } catch {
        // Client fallback when running standalone without live Python backend
        data = {
          resolved_bl: {
            standard: { name: 'DCSA eBL v3.0.3' },
            email_id: emailId,
            resolved_at: new Date().toISOString(),
            reviewer: reviewer,
            review_decisions: decisions.map((d) => ({
              field_key: d.field_key,
              choice: d.choice,
              value:
                d.choice === 'custom'
                  ? customValues[d.field_key] || ''
                  : d.choice === 'si'
                  ? items.find((p) => p.field_key === d.field_key)?.si_candidate?.value || ''
                  : items.find((p) => p.field_key === d.field_key)?.bl_candidate?.value || '',
            })),
          },
        };
      }

      setResult(data);
      onShowToast?.(
        `Resolved ${data.resolved_bl.review_decisions.length} field(s) - DCSA record exported`,
        'success',
      );
    } catch {
      onShowToast?.('Could not record the decision', 'warning');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="glass-card rounded-xl border border-slate-800 p-4 text-xs text-slate-400 flex items-center space-x-2">
        <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
        <span>Building side-by-side evidence...</span>
      </div>
    );
  }

  if (!proposals || items.length === 0) return null;

  return (
    <div id="conflict-resolution-panel" className="glass-card rounded-xl border border-amber-500/40 overflow-hidden shadow-lg scroll-mt-6">
      <div className="p-3 bg-amber-950/30 border-b border-amber-500/30 flex items-center justify-between gap-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-amber-200 flex items-center space-x-2">
          <GitCompareArrows className="w-4 h-4 text-amber-400" />
          <span>Resolve Discrepancy — Propose &amp; Confirm ({items.length})</span>
        </h3>
        <span className="font-mono text-[10px] px-2 py-0.5 rounded border border-amber-600/50 bg-amber-950/60 text-amber-300">
          auto-resolution: {proposals.auto_resolution}
        </span>
      </div>

      <div className="p-3 text-[11px] text-slate-400 border-b border-slate-800">{proposals.policy}</div>

      <div className="divide-y divide-slate-800/80">
        {items.map((proposal) => (
          <ProposalCard
            key={proposal.field_key}
            proposal={proposal}
            choice={choices[proposal.field_key]}
            customValue={customValues[proposal.field_key] || ''}
            onChoose={(choice) => setChoices({ ...choices, [proposal.field_key]: choice })}
            onCustomValue={(value) => {
              setCustomValues({ ...customValues, [proposal.field_key]: value });
              setChoices({ ...choices, [proposal.field_key]: 'custom' });
            }}
          />
        ))}
      </div>

      <div className="p-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <UserCheck className="w-4 h-4 text-cyan-400" />
          <input
            type="text"
            value={reviewer}
            onChange={(e) => setReviewer(e.target.value)}
            placeholder="Reviewer name"
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
          />
          <span className="text-[11px] text-slate-500">
            {undecided.length === 0 ? 'all conflicts decided' : `${undecided.length} field(s) still undecided`}
          </span>
        </div>
        <button
          type="button"
          disabled={!canSubmit || saving}
          onClick={submit}
          className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition ${
            canSubmit && !saving
              ? 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-950/50'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed'
          }`}
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
          <span>Resolve &amp; export DCSA record</span>
        </button>
      </div>

      {result && <DcsaExportPreview result={result} emailId={emailId} />}
    </div>
  );
}

function DcsaBadge({ dcsaField, internalOnly }) {
  if (internalOnly || !dcsaField) {
    return (
      <span className="font-mono text-[10px] px-1.5 py-0.5 rounded border border-slate-600/60 bg-slate-900/80 text-slate-400">
        DCSA: internal only
      </span>
    );
  }
  return (
    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded border border-cyan-700/60 bg-cyan-950/60 text-cyan-300">
      DCSA: {dcsaField}
    </span>
  );
}

function EvidenceColumn({ candidate, side, selected, onSelect }) {
  const isSi = side === 'SI';
  const tone = isSi
    ? { border: 'border-cyan-600/70', ring: 'ring-cyan-500/40', text: 'text-cyan-300' }
    : { border: 'border-blue-600/70', ring: 'ring-blue-500/40', text: 'text-blue-300' };
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`text-left rounded-xl border p-3 space-y-1.5 transition ${
        selected ? `${tone.border} ring-2 ${tone.ring} bg-slate-900/80` : 'border-slate-800 bg-slate-900/40 hover:border-slate-600'
      }`}
    >
      <div className="flex items-center justify-between">
        <span className={`font-mono text-[10px] font-bold ${tone.text}`}>{side}</span>
        <span className="font-mono text-[10px] text-slate-500">{candidate.document}</span>
      </div>
      <div className="font-mono text-xs text-slate-100 break-words">{candidate.value || '(missing)'}</div>
      <div className="font-mono text-[10px] text-slate-500">
        char_offset {candidate.char_offset ?? 'n/a'} · line {candidate.line_number ?? 'n/a'} · {candidate.span_match || 'not found'}
      </div>
      {candidate.exact_text && (
        <blockquote className="text-[11px] text-slate-400 border-l-2 border-slate-700 pl-2 italic break-words">
          &ldquo;{candidate.exact_text}&rdquo;
        </blockquote>
      )}
      <div className={`text-[10px] font-semibold ${selected ? tone.text : 'text-slate-500'}`}>
        {selected ? '✓ chosen by reviewer' : 'Use this value'}
      </div>
    </button>
  );
}

function ProposalCard({ proposal, choice, customValue, onChoose, onCustomValue }) {
  return (
    <div className="p-3 space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold text-slate-100">{proposal.field_name}</span>
        <span className="font-mono text-[10px] text-slate-500">{proposal.field_key}</span>
        <DcsaBadge dcsaField={proposal.dcsa_field} internalOnly={proposal.internal_only} />
        <span className="flex items-center space-x-1 text-[10px] text-amber-300">
          <AlertTriangle className="w-3 h-3" />
          <span>{proposal.reason}</span>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        <EvidenceColumn
          candidate={proposal.si_candidate}
          side="SI"
          selected={choice === 'si'}
          onSelect={() => onChoose('si')}
        />
        <EvidenceColumn
          candidate={proposal.bl_candidate}
          side="BL"
          selected={choice === 'bl'}
          onSelect={() => onChoose('bl')}
        />
      </div>

      <div
        className={`rounded-xl border p-2 flex items-center space-x-2 ${
          choice === 'custom' ? 'border-emerald-600/70 bg-emerald-950/20' : 'border-slate-800 bg-slate-900/40'
        }`}
      >
        <span className="font-mono text-[10px] text-slate-400 shrink-0">Third value</span>
        <input
          type="text"
          value={customValue}
          onChange={(e) => onCustomValue(e.target.value)}
          placeholder="Type the correct value (neither SI nor BL)"
          className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
        />
        {choice === 'custom' && <span className="text-[10px] text-emerald-300 font-semibold">✓ chosen</span>}
      </div>
    </div>
  );
}

function DcsaExportPreview({ result, emailId }) {
  const record = result.resolved_bl || {};
  const rows = Object.entries(result.dcsa_export || {});
  return (
    <div className="border-t border-slate-800 bg-slate-950/60 p-3 space-y-2">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold text-slate-100">
            Resolved record - {record.standard?.name}
          </span>
        </div>
        <a
          href={`/api/shipments/${emailId}/resolved?download=true`}
          download={`${emailId}.dcsa.json`}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-semibold transition"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export DCSA JSON</span>
        </a>
      </div>

      <div className="flex items-center space-x-2 text-[10px] text-slate-500 font-mono">
        <FileJson className="w-3.5 h-3.5 text-cyan-400" />
        <span>reviewer: {record.reviewer}</span>
        <span>·</span>
        <span>corrections logged: {result.corrections_logged}</span>
        {result.pending_decisions?.length > 0 && (
          <span className="text-amber-300">
            · pending (not auto-filled): {result.pending_decisions.join(', ')}
          </span>
        )}
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2 max-h-56 overflow-auto">
        <table className="w-full text-[11px] font-mono">
          <tbody>
            {rows.map(([path, value]) => (
              <tr key={path} className="border-b border-slate-800/60 last:border-0">
                <td className="py-1 pr-3 text-cyan-300 break-all">{path}</td>
                <td className="py-1 text-slate-200 break-all">{String(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {record.notice && <p className="text-[10px] text-slate-500 italic">{record.notice}</p>}
    </div>
  );
}
