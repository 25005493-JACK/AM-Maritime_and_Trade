import React, { useEffect, useState } from 'react';
import { Activity, Clock, Gauge, ShieldAlert, Users } from 'lucide-react';
import { apiFetch } from '../api.js';

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
      /* the preview still reflects the requested level */
    }
    onLevelChange?.(next);
  };

  const levels = info?.levels || [
    { level: 0, label: 'L0' }, { level: 1, label: 'L1' },
    { level: 2, label: 'L2' }, { level: 3, label: 'L3' },
  ];

  const tiles = [
    {
      key: 'auto_processed_pct',
      label: 'Automation rate',
      value: `${preview?.auto_processed_pct ?? 0}%`,
      hint: `${preview?.counts?.auto_processed ?? 0} fields auto-written`,
      Icon: Gauge,
      tone: 'text-emerald-300',
    },
    {
      key: 'estimated_error_exposure_pct',
      label: 'Estimated error exposure',
      value: `${preview?.estimated_error_exposure_pct ?? 0}%`,
      hint: 'non-exact evidence or failed validator',
      Icon: ShieldAlert,
      tone: 'text-amber-300',
    },
    {
      key: 'time',
      label: 'Time saved',
      value: `${preview?.estimated_time_saved_minutes ?? 0} min`,
      hint: 'review minutes avoided (documented constant)',
      Icon: Clock,
      tone: 'text-cyan-300',
    },
    {
      key: 'review',
      label: 'Fields sent to review',
      value: `${preview?.counts?.flagged_for_review ?? 0}`,
      hint: `${preview?.flagged_for_review_pct ?? 0}% of compared fields`,
      Icon: Users,
      tone: 'text-slate-300',
    },
  ];

  return (
    <div className="glass-card rounded-xl border border-cyan-600/40 overflow-hidden">
      <div className="p-3 bg-cyan-950/20 border-b border-cyan-600/30 flex items-center justify-between gap-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-200 flex items-center space-x-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          <span>Automation level - "AI license"</span>
        </h3>
        <span className="font-mono text-[10px] text-slate-400">
          {loading ? 'recalculating…' : preview?.level_label}
        </span>
      </div>

      <div className="p-4 space-y-4">
        <div>
          <div className="flex justify-between text-[10px] font-mono text-slate-400 mb-1">
            {levels.map((entry) => (
              <span key={entry.level} className={entry.level === level ? 'text-cyan-300 font-semibold' : ''}>
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
            className="w-full accent-cyan-500"
          />
          <p className="text-[11px] text-slate-400 mt-1">{preview?.level_description}</p>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
          {tiles.map(({ key, label, value, hint, Icon, tone }) => (
            <div key={key} className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
              <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-slate-400">
                <Icon className={`w-3.5 h-3.5 ${tone}`} />
                <span>{label}</span>
              </div>
              <div className={`mt-1 text-lg font-semibold ${tone}`}>{value}</div>
              <div className="text-[10px] text-slate-500">{hint}</div>
            </div>
          ))}
        </div>

        {preview && (
          <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-2 text-[10px] text-slate-400 font-mono space-y-0.5">
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
