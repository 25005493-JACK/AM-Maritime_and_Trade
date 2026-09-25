import React, { useState } from 'react';
import { Upload, X, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { apiFetch } from '../api.js';

export default function UploadModal({ isOpen, onClose, onUploadSuccess }) {
  const [vessel, setVessel] = useState('');
  const [voyage, setVoyage] = useState('');
  const [company, setCompany] = useState('');
  const [sender, setSender] = useState('');
  const [siText, setSiText] = useState('');
  const [blText, setBlText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!siText.trim() || !blText.trim()) {
      setError('Please provide both Shipping Instructions and Draft Bill of Lading text.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await apiFetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          si_text: siText,
          bl_text: blText,
          vessel,
          voyage,
          company,
          sender,
          subject: `SI vs Draft BL Verification - ${vessel} ${voyage}`
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Upload failed');
      }

      const data = await res.json();
      setLoading(false);
      onUploadSuccess(data);
      onClose();
    } catch (err) {
      setLoading(false);
      setError(err.message || 'An error occurred during upload.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl bg-slate-900 border border-blue-900/60 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-blue-900/50 bg-slate-950/60">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">Upload Live Document Pair</h2>
              <p className="text-xs text-slate-400">Process dynamic Shipping Instructions (SI) vs Draft Bill of Lading (BL)</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="flex items-center space-x-2 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Metadata Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Vessel Name</label>
              <input
                type="text"
                value={vessel}
                onChange={(e) => setVessel(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-blue-900/60 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                placeholder="EVER ULYSSES"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Voyage</label>
              <input
                type="text"
                value={voyage}
                onChange={(e) => setVoyage(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-blue-900/60 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                placeholder="V.104W"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Company / Shipper</label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-blue-900/60 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                placeholder="Oceanic Freight"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Sender Email</label>
              <input
                type="text"
                value={sender}
                onChange={(e) => setSender(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-blue-900/60 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                placeholder="ops@shipping.com"
              />
            </div>
          </div>

          {/* Document Texts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-cyan-400 flex items-center space-x-1.5">
                  <FileText className="w-3.5 h-3.5" />
                  <span>Shipping Instructions (SI)</span>
                </label>
                <span className="text-[11px] text-slate-500 font-mono">Source Text</span>
              </div>
              <textarea
                rows={10}
                value={siText}
                onChange={(e) => setSiText(e.target.value)}
                className="w-full p-3 bg-slate-950 border border-blue-900/60 rounded-xl text-xs font-mono text-slate-200 leading-relaxed focus:outline-none focus:border-cyan-500"
                placeholder="Paste SI document content..."
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-indigo-400 flex items-center space-x-1.5">
                  <FileText className="w-3.5 h-3.5" />
                  <span>Draft Bill of Lading (BL)</span>
                </label>
                <span className="text-[11px] text-slate-500 font-mono">Carrier Draft</span>
              </div>
              <textarea
                rows={10}
                value={blText}
                onChange={(e) => setBlText(e.target.value)}
                className="w-full p-3 bg-slate-950 border border-blue-900/60 rounded-xl text-xs font-mono text-slate-200 leading-relaxed focus:outline-none focus:border-indigo-500"
                placeholder="Paste Draft BL document content..."
              />
            </div>
          </div>

          {/* Footer Action */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-blue-900/40">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-cyan-600 hover:bg-cyan-500 shadow-lg shadow-cyan-900/40 transition flex items-center space-x-2 cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Running Verification Pipeline...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Process Live Verification</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
