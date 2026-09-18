import React, { useState } from 'react';
import { 
  X, 
  AlertTriangle, 
  Check, 
  RotateCcw, 
  ShieldCheck, 
  HelpCircle 
} from 'lucide-react';

export default function HumanReviewModal({ emailDetail, onClose, onSaveOverride }) {
  if (!emailDetail) return null;

  const { email, verification, overrides } = emailDetail;
  const verif = verification || {};
  const siExtracted = verif.si_extracted || {};
  const blExtracted = verif.bl_extracted || {};

  const fields = [
    { key: 'shipper', label: 'Shipper Name & Address' },
    { key: 'consignee', label: 'Consignee' },
    { key: 'notify_party', label: 'Notify Party' },
    { key: 'port_of_loading', label: 'Port of Loading' },
    { key: 'port_of_discharge', label: 'Port of Discharge' },
    { key: 'container_count', label: 'Container Count' },
    { key: 'gross_weight_kg', label: 'Gross Weight (kg)' }
  ];

  const existingSI = overrides?.si_overrides || {};
  const existingBL = overrides?.bl_overrides || {};

  const [siForm, setSiForm] = useState({
    shipper: existingSI.shipper ?? (siExtracted.shipper || ''),
    consignee: existingSI.consignee ?? (siExtracted.consignee || ''),
    notify_party: existingSI.notify_party ?? (siExtracted.notify_party || ''),
    port_of_loading: existingSI.port_of_loading ?? (siExtracted.port_of_loading || ''),
    port_of_discharge: existingSI.port_of_discharge ?? (siExtracted.port_of_discharge || ''),
    container_count: existingSI.container_count ?? (siExtracted.container_count || ''),
    gross_weight_kg: existingSI.gross_weight_kg ?? (siExtracted.gross_weight_kg || '')
  });

  const [blForm, setBlForm] = useState({
    shipper: existingBL.shipper ?? (blExtracted.shipper || ''),
    consignee: existingBL.consignee ?? (blExtracted.consignee || ''),
    notify_party: existingBL.notify_party ?? (blExtracted.notify_party || ''),
    port_of_loading: existingBL.port_of_loading ?? (blExtracted.port_of_loading || ''),
    port_of_discharge: existingBL.port_of_discharge ?? (blExtracted.port_of_discharge || ''),
    container_count: existingBL.container_count ?? (blExtracted.container_count || ''),
    gross_weight_kg: existingBL.gross_weight_kg ?? (blExtracted.gross_weight_kg || '')
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSaveOverride(email.id, siForm, blForm);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-4xl rounded-2xl border border-slate-700 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-4 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <span>Human-in-the-Loop Field Override</span>
                <span className="font-mono text-xs text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/60">
                  {email.id}
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Correct damaged OCR readings, fill missing fields, or override carrier values.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body / Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {verif.human_review_reasons?.length > 0 && (
            <div className="p-3.5 rounded-xl bg-amber-950/30 border border-amber-800/40 text-xs text-amber-300 flex items-start space-x-2">
              <HelpCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <strong className="block text-amber-200">System Escalation Reasons:</strong>
                <ul className="list-disc list-inside mt-1 space-y-0.5">
                  {verif.human_review_reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Side-by-Side Override Inputs */}
          <div className="grid grid-cols-2 gap-6">
            {/* SI Overrides */}
            <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400 border-b border-slate-800 pb-2">
                Shipping Instruction (SI Reference)
              </h4>
              {fields.map((f) => (
                <div key={f.key}>
                  <label className="block text-xs font-medium text-slate-400 mb-1">{f.label}</label>
                  <input
                    type="text"
                    value={siForm[f.key]}
                    onChange={(e) => setSiForm({ ...siForm, [f.key]: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500 transition"
                  />
                </div>
              ))}
            </div>

            {/* BL Overrides */}
            <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-blue-400 border-b border-slate-800 pb-2">
                Draft Bill of Lading (BL)
              </h4>
              {fields.map((f) => (
                <div key={f.key}>
                  <label className="block text-xs font-medium text-slate-400 mb-1">{f.label}</label>
                  <input
                    type="text"
                    value={blForm[f.key]}
                    onChange={(e) => setBlForm({ ...blForm, [f.key]: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500 transition"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Modal Footer Controls */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-lg shadow-cyan-950/50 transition"
            >
              <Check className="w-4 h-4" />
              <span>Save & Re-verify Document</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
