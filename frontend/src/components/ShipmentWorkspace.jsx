import React from 'react';
import {
  AlertTriangle,
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  FileCheck2,
  FileText,
  PackageCheck,
  ShieldCheck,
  XCircle
} from 'lucide-react';

const statusConfig = {
  OK: {
    label: 'Verified',
    tone: 'text-emerald-300 bg-emerald-950/40 border-emerald-500/40',
    icon: CheckCircle2
  },
  MISMATCH: {
    label: 'Mismatch detected',
    tone: 'text-rose-300 bg-rose-950/40 border-rose-500/40',
    icon: XCircle
  },
  NEEDS_REVIEW: {
    label: 'Needs review',
    tone: 'text-amber-300 bg-amber-950/40 border-amber-500/40',
    icon: AlertTriangle
  }
};

export default function ShipmentWorkspace({
  emailDetail,
  calendarData,
  isLoading,
  onOpenInspector,
  onOpenOverride,
  onOpenCalendar
}) {
  if (isLoading || !emailDetail) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-slate-950 text-slate-400 p-8">
        <div className="w-12 h-12 rounded-2xl border border-cyan-500/30 bg-cyan-950/30 flex items-center justify-center mb-4 animate-pulse">
          <PackageCheck className="w-6 h-6 text-cyan-400" />
        </div>
        <h2 className="text-sm font-semibold text-slate-200">Preparing shipment workspace</h2>
        <p className="text-xs text-slate-500 mt-1">Loading the selected shipment context...</p>
      </div>
    );
  }

  const { email, verification, classification } = emailDetail;
  const verif = verification || {};
  const status = verif.status || 'NEEDS_REVIEW';
  const config = statusConfig[status] || statusConfig.NEEDS_REVIEW;
  const StatusIcon = config.icon;
  const mismatchCount = verif.defect_fields?.length || 0;
  const attachments = email.attachments || [];
  const vessel = (calendarData?.schedule || []).find((item) => {
    const vesselName = (email.vessel || '').toLowerCase();
    return vesselName && item.vessel_name.toLowerCase().includes(vesselName);
  });
  const nextAction = verif.recommended_action || 'Review shipment documents and confirm the next operational step.';

  return (
    <div className="flex-1 overflow-y-auto bg-slate-950 p-4 md:p-6">
      <div className="max-w-7xl mx-auto space-y-5">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[11px] uppercase tracking-[0.18em] text-cyan-400 font-semibold">Shipment workspace</span>
              <span className="font-mono text-[11px] text-slate-400 bg-slate-900 border border-slate-700 rounded px-2 py-0.5">{email.id}</span>
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-100 truncate">{email.subject}</h1>
            <p className="text-xs text-slate-400 mt-1">{email.sender} {email.company ? `• ${email.company}` : ''}</p>
          </div>
          <div className={`inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-semibold ${config.tone}`}>
            <StatusIcon className="w-4 h-4" />
            <span>{config.label}</span>
          </div>
        </header>

        <section className="grid grid-cols-2 xl:grid-cols-4 gap-3">
          <div className="glass-card rounded-xl border border-slate-800 p-4">
            <span className="text-[11px] uppercase tracking-wider text-slate-500">Verification</span>
            <div className="flex items-center gap-2 mt-2 text-slate-100 font-semibold">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>{status === 'OK' ? 'All fields matched' : `${mismatchCount || 'Review'} field${mismatchCount === 1 ? '' : 's'} flagged`}</span>
            </div>
          </div>
          <div className="glass-card rounded-xl border border-slate-800 p-4">
            <span className="text-[11px] uppercase tracking-wider text-slate-500">Documents</span>
            <div className="flex items-center gap-2 mt-2 text-slate-100 font-semibold">
              <FileText className="w-4 h-4 text-cyan-400" />
              <span>{attachments.length} attachment{attachments.length === 1 ? '' : 's'}</span>
            </div>
          </div>
          <div className="glass-card rounded-xl border border-slate-800 p-4">
            <span className="text-[11px] uppercase tracking-wider text-slate-500">Vessel / voyage</span>
            <div className="mt-2 text-slate-100 font-semibold truncate">{email.vessel || 'Not identified'}</div>
            <div className="text-[11px] text-slate-500 font-mono mt-0.5">{email.voyage || 'Voyage unavailable'}</div>
          </div>
          <div className="glass-card rounded-xl border border-slate-800 p-4">
            <span className="text-[11px] uppercase tracking-wider text-slate-500">Calendar</span>
            <div className="flex items-center gap-2 mt-2 text-slate-100 font-semibold">
              <CalendarDays className="w-4 h-4 text-cyan-400" />
              <span>{vessel?.google_calendar?.event_url ? 'Google linked' : 'Not linked'}</span>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.5fr)_minmax(20rem,1fr)] gap-4">
          <div className="glass-card rounded-xl border border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2"><FileCheck2 className="w-4 h-4 text-cyan-400" />Verification summary</h2>
                <p className="text-xs text-slate-500 mt-1">The key decision signals for this shipment.</p>
              </div>
              <span className="text-[11px] font-mono text-slate-500">{classification?.category || 'GENERAL'}</span>
            </div>
            <div className="p-4 space-y-3">
              <div className={`rounded-lg border p-3 text-xs ${config.tone}`}>
                {verif.summary_message || 'No summary is available for this shipment yet.'}
              </div>
              {verif.field_matrix?.length > 0 ? (
                <div className="space-y-2">
                  {verif.field_matrix.filter((row) => !row.is_match).slice(0, 4).map((row) => (
                    <div key={row.field_key} className="flex items-center justify-between gap-3 rounded-lg bg-slate-950/70 border border-slate-800 p-3">
                      <div className="min-w-0">
                        <div className="text-xs font-semibold text-slate-200 truncate">{row.field_name}</div>
                        <div className="text-[11px] text-slate-500 mt-1 truncate">SI: {row.si_value} <ArrowRight className="inline w-3 h-3 mx-1" /> BL: {row.bl_value}</div>
                      </div>
                      <span className="text-[10px] uppercase font-mono text-rose-300 border border-rose-500/30 bg-rose-950/30 rounded px-2 py-1">Diff</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-slate-500">No field comparison matrix is available.</div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="glass-card rounded-xl border border-cyan-800/50 p-4">
              <span className="text-[11px] uppercase tracking-[0.16em] text-cyan-400 font-semibold">Recommended next step</span>
              <p className="text-sm text-slate-100 font-medium leading-relaxed mt-2">{nextAction}</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-1 gap-2 mt-4">
                <button onClick={onOpenInspector} className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold px-3 py-2 transition">
                  <FileCheck2 className="w-4 h-4" /> Open document inspector
                </button>
                {status !== 'OK' && (
                  <button onClick={onOpenOverride} className="inline-flex items-center justify-center gap-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-slate-950 text-xs font-semibold px-3 py-2 transition">
                    <AlertTriangle className="w-4 h-4" /> Review or override
                  </button>
                )}
                <button onClick={onOpenCalendar} className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-200 text-xs font-semibold px-3 py-2 transition">
                  <CalendarDays className="w-4 h-4" /> Open vessel calendar
                </button>
              </div>
            </div>

            <div className="glass-card rounded-xl border border-slate-800 p-4">
              <h2 className="text-sm font-bold text-slate-100 mb-3">Shipment context</h2>
              <dl className="space-y-2 text-xs">
                <div className="flex justify-between gap-4"><dt className="text-slate-500">Received</dt><dd className="text-slate-200 text-right">{email.timestamp || 'Unknown'}</dd></div>
                <div className="flex justify-between gap-4"><dt className="text-slate-500">Company</dt><dd className="text-slate-200 text-right truncate">{email.company || 'Not identified'}</dd></div>
                <div className="flex justify-between gap-4"><dt className="text-slate-500">Vessel</dt><dd className="text-slate-200 text-right">{email.vessel || 'Not identified'}</dd></div>
                <div className="flex justify-between gap-4"><dt className="text-slate-500">Documents</dt><dd className="text-slate-200 text-right">{attachments.map((attachment) => typeof attachment === 'string' ? attachment.split(/[\\/]/).pop() : attachment.filename || attachment.path).join(', ') || 'None'}</dd></div>
              </dl>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
