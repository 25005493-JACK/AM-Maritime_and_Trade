import React, { useState } from 'react';
import { 
  X, 
  Upload, 
  FileText, 
  AlertTriangle, 
  CheckCircle2, 
  Ship, 
  ArrowRight,
  Layers,
  Paperclip
} from 'lucide-react';
import { apiFetch } from '../api.js';

const SAMPLE_MISMATCH_SI = `SHIPPING INSTRUCTION
========================================
Shipper: PACIFIC MERCHANDISE EXPORTS PTE LTD
  10 MARINA BOULEVARD, #25-01 MARINA BAY FINANCIAL CENTRE, SINGAPORE 018983
Consignee: GLOBAL FREIGHT LOGISTICS LLC
  SUITE 400, 1200 BRICKELL AVENUE, MIAMI, FL 33131, UNITED STATES
Notify Party: SAME AS CONSIGNEE
Port of Loading: SINGAPORE (SGSIN)
Port of Discharge: HOUSTON, US (USHOU)
Container Count: 3 x 40'HC
Gross Weight: 48,250 KG
Commodity: ELECTRONIC CONSUMER COMPONENTS
Vessel & Voyage: EVER GIVEN V.042W
Booking No: BKG-2026-9941
`;

const SAMPLE_MISMATCH_BL = `BILL OF LADING (DRAFT)
========================================
Shipper: PACIFIC MERCHANDISE EXPORTS PTE LTD
  10 MARINA BOULEVARD, #25-01 MARINA BAY FINANCIAL CENTRE, SINGAPORE 018983
Consignee: GLOBAL FREIGHT LOGISTICS LLC
  SUITE 400, 1200 BRICKELL AVENUE, MIAMI, FL 33131, UNITED STATES
Notify Party: SAME AS CONSIGNEE
Port of Loading: SINGAPORE (SGSIN)
Port of Discharge: HOUSTON, US (USHOU)
Container Count: 4 x 40'HC
Gross Weight: 64,300 KG
Commodity: ELECTRONIC CONSUMER COMPONENTS
Vessel & Voyage: EVER GIVEN V.042W
B/L Reference: BL-PAC-9941
`;

const SAMPLE_MATCH_SI = `SHIPPING INSTRUCTION
========================================
Shipper: APRIL FINE PAPER TRADING FZE
  JEBEL ALI FREE ZONE, DUBAI, UAE
Consignee: TRANSWORLD PUBLISHING LTD
  45 BEDFORD SQUARE, LONDON WC1B 3DP, UNITED KINGDOM
Notify Party: TRANSWORLD PUBLISHING LTD
Port of Loading: JEBEL ALI, UAE (AEJEA)
Port of Discharge: ROTTERDAM, NETHERLANDS (NLRTM)
Container Count: 2 x 40'HC
Gross Weight: 35,400 KG
Commodity: COATED ART PAPER IN ROLLS
Vessel & Voyage: MSC ISABELLA V.2601E
Booking No: BKG-MATCH-8812
`;

const SAMPLE_MATCH_BL = `BILL OF LADING (DRAFT)
========================================
Shipper: APRIL FINE PAPER TRADING FZE
  JEBEL ALI FREE ZONE, DUBAI, UAE
Consignee: TRANSWORLD PUBLISHING LTD
  45 BEDFORD SQUARE, LONDON WC1B 3DP, UNITED KINGDOM
Notify Party: TRANSWORLD PUBLISHING LTD
Port of Loading: JEBEL ALI, UAE (AEJEA)
Port of Discharge: ROTTERDAM, NETHERLANDS (NLRTM)
Container Count: 2 x 40'HC
Gross Weight: 35,400 KG
Commodity: COATED ART PAPER IN ROLLS
Vessel & Voyage: MSC ISABELLA V.2601E
B/L Reference: BL-MATCH-8812
`;

export default function UploadDocsModal({ isOpen, onClose, onUploadSuccess, targetEmail }) {
  const [uploadMode, setUploadMode] = useState('text'); // 'text' or 'file'
  const [subject, setSubject] = useState(targetEmail?.subject || 'RE: TO CONFIRM DOCS _ LIVE DEMO _ USHOU _ PACIFIC EXPORTS');
  const [sender, setSender] = useState(targetEmail?.sender || 'docs@pacificmerchandise.com');
  const [vessel, setVessel] = useState(targetEmail?.vessel || 'EVER GIVEN');
  const [voyage, setVoyage] = useState(targetEmail?.voyage || 'V.042W');
  const [company, setCompany] = useState(targetEmail?.company || 'Pacific Merchandise');

  const [siText, setSiText] = useState(SAMPLE_MISMATCH_SI);
  const [blText, setBlText] = useState(SAMPLE_MISMATCH_BL);

  const [siFile, setSiFile] = useState(null);
  const [blFile, setBlFile] = useState(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  React.useEffect(() => {
    if (targetEmail && isOpen) {
      if (targetEmail.subject) setSubject(targetEmail.subject);
      if (targetEmail.sender) setSender(targetEmail.sender);
      if (targetEmail.company) setCompany(targetEmail.company);
      if (targetEmail.vessel) setVessel(targetEmail.vessel);
      if (targetEmail.voyage) setVoyage(targetEmail.voyage);
    }
  }, [targetEmail, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);
    setErrorMsg(null);

    try {
      let res;
      if (uploadMode === 'file' && (siFile || blFile)) {
        const formData = new FormData();
        if (siFile) formData.append('si_file', siFile);
        if (blFile) formData.append('bl_file', blFile);
        formData.append('subject', subject);
        formData.append('sender', sender);
        formData.append('vessel', vessel);
        formData.append('voyage', voyage);
        formData.append('company', company);
        if (targetEmail?.id) formData.append('target_email_id', targetEmail.id);
        if (siText && !siFile) formData.append('si_text', siText);
        if (blText && !blFile) formData.append('bl_text', blText);

        res = await apiFetch('/api/upload', {
          method: 'POST',
          body: formData
        });
      } else {
        if (!siText.trim()) throw new Error('Please provide Shipping Instruction (SI) text');
        if (!blText.trim()) throw new Error('Please provide draft Bill of Lading (BL) text');

        res = await apiFetch('/api/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            subject,
            sender,
            vessel,
            voyage,
            company,
            target_email_id: targetEmail?.id,
            si_text: siText,
            bl_text: blText
          })
        });
      }

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      if (onUploadSuccess) {
        onUploadSuccess(data);
      }
      onClose();
    } catch (err) {
      console.error('Upload failed:', err);
      setErrorMsg(err.message || 'Failed to upload document pair');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-panel w-full max-w-4xl rounded-2xl border border-blue-800/80 shadow-2xl bg-slate-900/95 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header Bar */}
        <div className="p-4 bg-gradient-to-r from-blue-950 via-slate-900 to-indigo-950 border-b border-blue-900/60 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-cyan-950/50">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-extrabold text-slate-100 flex items-center space-x-2">
                <span>Upload New SI + BL Pair for Real Pipeline Verification</span>
                <span className="text-[10px] bg-cyan-950 text-cyan-300 font-mono px-2 py-0.5 rounded border border-cyan-700/60 font-bold">
                  LIVE ENGINE
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Upload real shipping documents to run entity extraction and cross-document comparison.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scoped Order Context Bar */}
        {targetEmail && (
          <div className="px-6 py-2 bg-gradient-to-r from-blue-950 via-cyan-950/40 to-blue-950 border-b border-cyan-800/40 flex items-center justify-between font-mono text-xs text-cyan-300 shrink-0">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              <span className="font-bold text-slate-200">Scoped Order Context:</span>
              <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-700 text-cyan-400 font-bold">{targetEmail.id}</span>
              <span>•</span>
              <span>Company: <strong className="text-white">{targetEmail.company || targetEmail.sender}</strong></span>
            </div>
            <span className="text-[11px] text-slate-400 font-semibold">Locked to Email & Company Order</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4">
          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-950/80 border border-rose-600 text-rose-300 text-xs font-medium flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Preset Samples & Quick Load */}
          <div className="flex items-center justify-between bg-slate-950/80 p-2.5 rounded-xl border border-blue-900/40 text-xs">
            <span className="font-bold text-slate-300 flex items-center space-x-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>Quick Test Presets for Specific Companies:</span>
            </span>
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={() => {
                  setCompany('Pacific Merchandise Exports');
                  setSubject('RE: TO CONFIRM DOCS _ LIVE DEMO _ USHOU _ PACIFIC EXPORTS');
                  setSender('docs@pacificmerchandise.com');
                  setVessel('EVER GIVEN');
                  setVoyage('V.042W');
                  setSiText(SAMPLE_MISMATCH_SI);
                  setBlText(SAMPLE_MISMATCH_BL);
                }}
                className="px-2.5 py-1 rounded-lg bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 border border-rose-700/60 font-semibold text-[11px] transition"
              >
                Pacific Merchandise (Mismatch)
              </button>
              <button
                type="button"
                onClick={() => {
                  setCompany('April Fine Paper Trading FZE');
                  setSubject('RE: TO CONFIRM DOCS _ MATCH DEMO _ NLRTM _ APRIL FINE PAPER');
                  setSender('docs@aprilfinepaper.com');
                  setVessel('MSC ISABELLA');
                  setVoyage('V.2601E');
                  setSiText(SAMPLE_MATCH_SI);
                  setBlText(SAMPLE_MATCH_BL);
                }}
                className="px-2.5 py-1 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-700/60 font-semibold text-[11px] transition"
              >
                April Fine Paper (Clean Match)
              </button>
            </div>
          </div>

          {/* Metadata Controls */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                Company / Shipper
              </label>
              <input
                type="text"
                placeholder="Company Name"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="w-full bg-slate-950 border border-blue-900/60 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 font-mono"
                required
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                Subject
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full bg-slate-950 border border-blue-900/60 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 font-mono"
                required
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                Sender Email
              </label>
              <input
                type="email"
                value={sender}
                onChange={(e) => setSender(e.target.value)}
                className="w-full bg-slate-950 border border-blue-900/60 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 font-mono"
                required
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                Vessel & Voyage
              </label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  placeholder="Vessel"
                  value={vessel}
                  onChange={(e) => setVessel(e.target.value)}
                  className="w-1/2 bg-slate-950 border border-blue-900/60 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
                />
                <input
                  type="text"
                  placeholder="Voyage"
                  value={voyage}
                  onChange={(e) => setVoyage(e.target.value)}
                  className="w-1/2 bg-slate-950 border border-blue-900/60 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 font-mono"
                />
              </div>
            </div>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center space-x-3 pt-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Input Mode:</span>
            <button
              type="button"
              onClick={() => setUploadMode('text')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                uploadMode === 'text'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-transparent'
              }`}
            >
              Document Text (Direct Paste / Edit)
            </button>
            <button
              type="button"
              onClick={() => setUploadMode('file')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                uploadMode === 'file'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-transparent'
              }`}
            >
              File Upload (.txt, .pdf, .docx)
            </button>
          </div>

          {/* Documents Input Columns */}
          {uploadMode === 'text' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Shipping Instruction (SI) */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-cyan-400 flex items-center space-x-1.5">
                    <FileText className="w-4 h-4" />
                    <span>Shipping Instruction (SI) Text</span>
                  </label>
                  <span className="text-[10px] text-slate-500 font-mono">Source of Truth</span>
                </div>
                <textarea
                  value={siText}
                  onChange={(e) => setSiText(e.target.value)}
                  rows={14}
                  className="w-full bg-slate-950 border border-blue-900/60 rounded-xl p-3 text-xs text-slate-200 font-mono leading-relaxed focus:outline-none focus:border-cyan-400 resize-none selection:bg-cyan-900"
                  placeholder="Paste Shipping Instruction content here..."
                  required
                />
              </div>

              {/* Draft Bill of Lading (BL) */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-indigo-400 flex items-center space-x-1.5">
                    <FileText className="w-4 h-4" />
                    <span>Draft Bill of Lading (BL) Text</span>
                  </label>
                  <span className="text-[10px] text-slate-500 font-mono">Carrier Draft for Verification</span>
                </div>
                <textarea
                  value={blText}
                  onChange={(e) => setBlText(e.target.value)}
                  rows={14}
                  className="w-full bg-slate-950 border border-blue-900/60 rounded-xl p-3 text-xs text-slate-200 font-mono leading-relaxed focus:outline-none focus:border-indigo-400 resize-none selection:bg-indigo-900"
                  placeholder="Paste draft Bill of Lading content here..."
                  required
                />
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
              {/* File upload SI */}
              <div className="p-6 rounded-2xl border-2 border-dashed border-cyan-500/40 bg-slate-950/60 text-center space-y-3">
                <Paperclip className="w-8 h-8 text-cyan-400 mx-auto" />
                <div>
                  <h4 className="text-xs font-bold text-slate-200">Shipping Instruction (SI)</h4>
                  <p className="text-[11px] text-slate-400 mt-1">Upload .txt, .pdf, or .docx file</p>
                </div>
                <input
                  type="file"
                  accept=".txt,.pdf,.docx,.xlsx"
                  onChange={(e) => setSiFile(e.target.files[0])}
                  className="text-xs text-slate-400 file:mr-2 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-cyan-950 file:text-cyan-300 hover:file:bg-cyan-900 cursor-pointer"
                />
                {siFile && <p className="text-xs text-cyan-300 font-mono font-bold">{siFile.name}</p>}
              </div>

              {/* File upload BL */}
              <div className="p-6 rounded-2xl border-2 border-dashed border-indigo-500/40 bg-slate-950/60 text-center space-y-3">
                <Paperclip className="w-8 h-8 text-indigo-400 mx-auto" />
                <div>
                  <h4 className="text-xs font-bold text-slate-200">Draft Bill of Lading (BL)</h4>
                  <p className="text-[11px] text-slate-400 mt-1">Upload .txt, .pdf, or .docx file</p>
                </div>
                <input
                  type="file"
                  accept=".txt,.pdf,.docx,.xlsx"
                  onChange={(e) => setBlFile(e.target.files[0])}
                  className="text-xs text-slate-400 file:mr-2 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-950 file:text-indigo-300 hover:file:bg-indigo-900 cursor-pointer"
                />
                {blFile && <p className="text-xs text-indigo-300 font-mono font-bold">{blFile.name}</p>}
              </div>
            </div>
          )}

          {/* Footer Controls */}
          <div className="flex items-center justify-between pt-4 border-t border-blue-900/60">
            <span className="text-xs text-slate-400 font-mono">
              Real pipeline execution: Classifier &rarr; Entity Extractor &rarr; Normalizer &rarr; Comparator &rarr; Event Logger
            </span>

            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-2 rounded-xl bg-gradient-to-r from-blue-600 via-cyan-500 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-slate-950 font-extrabold text-xs flex items-center space-x-2 shadow-lg shadow-cyan-950/60 transition active:scale-95 disabled:opacity-50 cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    <span>Processing Through Pipeline...</span>
                  </>
                ) : (
                  <>
                    <ArrowRight className="w-4 h-4" />
                    <span>Process Through Real Pipeline</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
