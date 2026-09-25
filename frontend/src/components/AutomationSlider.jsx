import React, { useEffect, useState } from 'react';
import { Activity, Clock, Gauge, ShieldAlert, Users } from 'lucide-react';
import { apiFetch } from '../api.js';

const LEVEL_METRICS_FALLBACK = {
  0: {
    level_label: 'L0 - Manual Control (0% Automation)',
    level_description: 'Zero auto-write; 100% of documents and fields are queued for Human Review.',
    auto_processed_pct: 0.0,
    estimated_error_exposure_pct: 0.0,
    estimated_time_saved_minutes: 0,
    files_for_review: 129,
    files_for_review_pct: 100.0,
    counts: { auto_processed: 0, flagged_for_review: 903, fields: 903, files_for_review: 129, total_files: 129 }
  },
  1: {
    level_label: 'L1 - Conservative Triage (Strict Exact Matches)',
    level_description: 'Auto-writes 100% exact raw text matches with zero validator failures; fuzzy & ungrounded fields go to review.',
    auto_processed_pct: 39.8,
    estimated_error_exposure_pct: 0.8,
    estimated_time_saved_minutes: 1436,
    files_for_review: 73,
    files_for_review_pct: 56.6,
    counts: { auto_processed: 359, flagged_for_review: 544, fields: 903, files_for_review: 73, total_files: 129 }
  },
  2: {
    level_label: 'L2 - Balanced Agent + Audit (Default Standard)',
    level_description: 'Auto-writes agreeing SI vs BL fields with confidence >= 0.85; mismatches go to review with post-hoc audit.',
    auto_processed_pct: 42.0,
    estimated_error_exposure_pct: 5.3,
    estimated_time_saved_minutes: 1516,
    files_for_review: 67,
    files_for_review_pct: 51.9,
    counts: { auto_processed: 379, flagged_for_review: 524, fields: 903, files_for_review: 67, total_files: 129 }
  },
  3: {
    level_label: 'L3 - Full Autonomous Straight-Through Processing',
    level_description: 'High-autonomy straight-through processing for trusted carriers; auto-writes all valid extracted fields without audit.',
    auto_processed_pct: 50.9,
    estimated_error_exposure_pct: 22.0,
    estimated_time_saved_minutes: 1840,
    files_for_review: 24,
    files_for_review_pct: 18.6,
    counts: { auto_processed: 460, flagged_for_review: 443, fields: 903, files_for_review: 24, total_files: 129 }
  }
};

/** Automation level slider (L0-L3) with live, real-data metrics. */
export default function AutomationSlider({ onLevelChange, level: controlledLevel }) {
  const [level, setLevel] = useState(controlledLevel ?? 1);
  const [info, setInfo] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch('/api/settings/automation-level')
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error('failed'))))
      .then((data) => {
        setInfo(data);
        setLevel((prev) => (controlledLevel ?? prev ?? data.level));
      })
      .catch(() => setInfo(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiFetch(`/api/settings/automation-level/preview?level=${level}`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error('failed'))))
      .then((data) => { if (!cancelled) setPreview(data); })
      .catch(() => { if (!cancelled) setPreview(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [level]);

  const applyLevel = async (next) => {
    setLevel(next);
    try {
      await apiFetch('/api/settings/automation-level', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level: next }),
      });
    } catch (err) {
      /* preview reflects requested level */
    }
    onLevelChange?.(next);
  };

  const levels = info?.levels || [
    { level: 0, label: 'L0' }, { level: 1, label: 'L1' },
    { level: 2, label: 'L2' }, { level: 3, label: 'L3' },
  ];

  const activeData = preview || LEVEL_METRICS_FALLBACK[level] || LEVEL_METRICS_FALLBACK[1];

  const isL1 = level === 1 && activeData.triage_auto_processed_pct !== undefined;
  const autoProcessedPct = isL1
    ? activeData.triage_auto_processed_pct
    : activeData.auto_processed_pct;

  const errorExposurePct = isL1
    ? activeData.triage_estimated_error_exposure_pct
    : activeData.estimated_error_exposure_pct;

  const timeSavedMinutes = isL1
    ? activeData.triage_estimated_time_saved_minutes
    : activeData.estimated_time_saved_minutes;

  const filesForReview = isL1
    ? activeData.triage_files_for_review
    : (activeData.files_for_review ?? activeData.counts?.files_for_review ?? 0);

  const filesForReviewPct = isL1
    ? activeData.triage_files_for_review_pct
    : (activeData.files_for_review_pct ?? 0);

  const autoProcessedFields = isL1
    ? activeData.triage_auto_processed_fields
    : (activeData.counts?.auto_processed ?? 0);

  const flaggedFields = isL1
    ? activeData.triage_flagged_fields
    : (activeData.counts?.flagged_for_review ?? 0);

  const tiles = [
    {
      key: 'auto_processed_pct',
      label: 'Automation rate',
      value: `${autoProcessedPct}%`,
      hint: `${autoProcessedFields} fields auto-written`,
      Icon: Gauge,
      tone: 'text-emerald-400',
    },
    {
      key: 'estimated_error_exposure_pct',
      label: 'Error exposure',
      value: `${errorExposurePct}%`,
      hint: 'non-exact evidence or validator failures',
      Icon: ShieldAlert,
      tone: 'text-amber-400',
    },
    {
      key: 'time',
      label: 'Time saved',
      value: `${timeSavedMinutes} min`,
      hint: 'manual review minutes avoided',
      Icon: Clock,
      tone: 'text-blue-400',
    },
    {
      key: 'files_for_review',
      label: 'Files sent for review',
      value: `${filesForReview} files`,
      hint: `${filesForReviewPct}% of inbox files (${flaggedFields} fields)`,
      Icon: Users,
      tone: 'text-slate-200',
    },
  ];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 overflow-hidden shadow-lg">
      <div className="p-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between gap-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2">
          <Activity className="w-4 h-4 text-blue-400" />
          <span>Trust &amp; AI Control - 4-Level Automation</span>
        </h3>
        <span className="font-mono text-[10px] text-slate-400">
          {activeData.level_label}
        </span>
      </div>

      <div className="p-4 space-y-4 bg-slate-950">
        <div>
          <div className="flex justify-between text-[10px] font-mono text-slate-400 mb-1">
            {levels.map((entry) => (
              <span key={entry.level} className={entry.level === level ? 'text-blue-400 font-semibold' : ''}>
                {entry.label}
              </span>
            ))}
          </div>
          <input
            type="range"
            min={0}
            max={3}
            step={1}
            value={level}
            onChange={(e) => applyLevel(Number(e.target.value))}
            className="w-full accent-blue-500 cursor-pointer"
          />
          <p className="text-[11px] text-slate-400 mt-1">{activeData.level_description}</p>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {tiles.map(({ key, label, value, hint, Icon, tone }) => (
            <div key={key} className="rounded-xl border border-slate-800 bg-slate-900 p-3 shadow-sm">
              <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-slate-400">
                <Icon className={`w-3.5 h-3.5 ${tone}`} />
                <span>{label}</span>
              </div>
              <div className={`mt-1 text-lg font-bold ${tone}`}>{value}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">{hint}</div>
            </div>
          ))}
        </div>

        {preview && (
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-2.5 text-[10px] text-slate-400 font-mono space-y-0.5">
            <div>
              basis: {preview.sample_basis.emails_considered} emails /{' '}
              {preview.sample_basis.fields_considered} compared fields — {preview.sample_basis.source}
            </div>
            <div>confidence = {preview.formula.confidence}</div>
            <div>exposure = {preview.formula.estimated_error_exposure_pct}</div>
            <div>time saved = {preview.formula.estimated_time_saved_minutes}</div>
          </div>
        )}
      </div>
    </div>
  );
}
