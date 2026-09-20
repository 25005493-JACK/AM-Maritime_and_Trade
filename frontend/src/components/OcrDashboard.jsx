import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, CheckCircle2, FileText, RefreshCw, Search, ScanText } from 'lucide-react';

const statusLabel = {
  ready: 'Ready',
  needs_review: 'Needs review',
  unreadable: 'Unreadable'
};

function Metric({ label, value, detail, tone = 'text-slate-100' }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 px-5 py-4">
      <p className="text-xs font-medium text-slate-400">{label}</p>
      <p className={`mt-2 text-3xl font-semibold tracking-tight ${tone}`}>{value}</p>
      <p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p>
    </div>
  );
}

function DocumentCard({ document }) {
  const [copied, setCopied] = useState(false);
  const emailNumber = document.email_number
    ? String(document.email_number).padStart(3, '0')
    : document.email_id;
  const isReady = document.status === 'ready';

  const copyText = async () => {
    if (!document.text || !navigator.clipboard) return;
    await navigator.clipboard.writeText(document.text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 px-5 py-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-md bg-cyan-500/10 px-2 py-1 font-mono text-xs font-semibold text-cyan-300">
              Email #{emailNumber}
            </span>
            <span className="rounded-md bg-slate-800 px-2 py-1 text-xs font-semibold text-slate-300">
              {document.document_type}
            </span>
            <span className={`rounded-md px-2 py-1 text-xs font-semibold ${isReady
              ? 'bg-emerald-500/10 text-emerald-300'
              : 'bg-amber-500/10 text-amber-300'}`}>
              {statusLabel[document.status] || document.status}
            </span>
          </div>
          <h3 className="mt-3 truncate text-sm font-semibold text-slate-100">{document.filename}</h3>
          <p className="mt-1 truncate text-xs text-slate-500">{document.subject}</p>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span>{document.method}</span>
          <span>{document.page_count} page{document.page_count === 1 ? '' : 's'}</span>
          <span>{document.field_count}/7 fields</span>
          {document.benchmark_accuracy_pct != null && (
            <span className="font-semibold text-cyan-300">
              {document.benchmark_accuracy_pct}% benchmark
            </span>
          )}
        </div>
      </div>

      <div className="px-5 py-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">Extracted text</p>
          <button
            type="button"
            onClick={copyText}
            disabled={!document.text}
            className="text-xs font-medium text-cyan-300 transition hover:text-cyan-200 disabled:cursor-not-allowed disabled:text-slate-600"
          >
            {copied ? 'Copied' : 'Copy text'}
          </button>
        </div>
        {document.text ? (
          <pre className="max-w-full overflow-x-auto whitespace-pre rounded-xl border border-slate-800 bg-slate-950/80 p-4 font-mono text-xs leading-6 text-slate-300">
            {document.text}
          </pre>
        ) : (
          <div className="flex items-start gap-2 rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 text-xs leading-5 text-amber-200">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{document.error || 'No text could be extracted from this PDF.'}</span>
          </div>
        )}
        {document.error && document.text && (
          <p className="mt-3 text-xs text-amber-300">Review note: {document.error}</p>
        )}
      </div>
    </article>
  );
}

export default function OcrDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/ocr/dashboard');
      if (!response.ok) throw new Error(`Server returned ${response.status}`);
      setData(await response.json());
    } catch (caught) {
      setError(caught.message || 'The OCR dashboard could not be loaded.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const documents = useMemo(() => {
    const query = search.trim().toLowerCase();
    return (data?.documents || []).filter((document) => {
      const matchesSearch = !query || [
        document.email_id,
        document.filename,
        document.subject,
        document.text
      ].some((value) => String(value || '').toLowerCase().includes(query));
      const matchesFilter = filter === 'all'
        || (filter === 'ocr' && document.ocr_page_count > 0)
        || (filter === 'text' && document.method === 'Text layer')
        || (filter === 'review' && document.status !== 'ready');
      return matchesSearch && matchesFilter;
    });
  }, [data, search, filter]);

  const summary = data?.summary;

  return (
    <div className="h-screen flex-1 overflow-y-auto bg-slate-950">
      <div className="mx-auto max-w-6xl space-y-8 px-6 py-8 lg:px-10">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">
              <ScanText className="h-4 w-4" /> Document intelligence
            </div>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">PDF OCR Dashboard</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Inspect every PDF attachment, the text extracted for each email, and the accuracy measured on searchable PDFs.
            </p>
          </div>
          <button
            type="button"
            onClick={load}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:bg-slate-800 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
        </header>

        {error && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-200">
            {error}
          </div>
        )}

        {loading && !data ? (
          <div className="flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-sm text-slate-300">
            <RefreshCw className="h-5 w-5 animate-spin text-cyan-400" /> Reading PDFs and running the OCR benchmark…
          </div>
        ) : summary && (
          <>
            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="OCR summary">
              <Metric
                label="OCR benchmark accuracy"
                value={summary.ocr_accuracy_pct == null ? '—' : `${summary.ocr_accuracy_pct}%`}
                detail={`${summary.benchmark_pages} searchable pages compared with their text layer`}
                tone="text-cyan-300"
              />
              <Metric
                label="PDF attachments"
                value={summary.total_pdfs}
                detail={`${summary.searchable_pdfs} searchable · ${summary.ocr_pdfs} scanned`}
              />
              <Metric
                label="Scanned field coverage"
                value={summary.ocr_field_coverage_pct == null ? '—' : `${summary.ocr_field_coverage_pct}%`}
                detail="Required shipment fields found in OCR text"
                tone="text-emerald-300"
              />
              <Metric
                label="Needs review"
                value={summary.needs_review}
                detail="Unreadable documents or incomplete OCR results"
                tone={summary.needs_review ? 'text-amber-300' : 'text-emerald-300'}
              />
            </section>

            <section className="flex items-start gap-3 rounded-2xl border border-cyan-500/20 bg-cyan-500/5 px-5 py-4 text-xs leading-6 text-slate-300">
              <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-cyan-400" />
              <p>
                <strong className="text-slate-100">How accuracy is measured:</strong> PyMuPDF OCR is compared character by character with the existing text layer of searchable PDFs after case and whitespace normalisation. This benchmark covers {summary.benchmark_pages} page{summary.benchmark_pages === 1 ? '' : 's'}. The {summary.scan_pages_without_reference} scanned page{summary.scan_pages_without_reference === 1 ? '' : 's'} have no verified transcript, so their true OCR accuracy is unverified. Field coverage is a separate completeness check.
                {summary.benchmark_warning && <span className="block pt-1 text-amber-300">Benchmark note: {summary.benchmark_warning}</span>}
              </p>
            </section>

            <section className="space-y-4" aria-label="Extracted PDF text">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <h2 className="flex items-center gap-2 text-xl font-semibold text-white">
                    <FileText className="h-5 w-5 text-cyan-400" /> Extracted text by email
                  </h2>
                  <p className="mt-1 text-xs text-slate-400">Showing {documents.length} of {summary.total_pdfs} PDF attachments. Full text is shown below each document.</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <label className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 text-slate-400">
                    <Search className="h-4 w-4" />
                    <input
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      placeholder="Search email or text"
                      className="w-48 bg-transparent py-2 text-xs text-slate-100 outline-none placeholder:text-slate-500"
                    />
                  </label>
                  <select
                    value={filter}
                    onChange={(event) => setFilter(event.target.value)}
                    className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 outline-none"
                  >
                    <option value="all">All PDFs</option>
                    <option value="ocr">Scanned / OCR</option>
                    <option value="text">Searchable text</option>
                    <option value="review">Needs review</option>
                  </select>
                </div>
              </div>

              {documents.length ? (
                <div className="space-y-4">
                  {documents.map((document) => (
                    <DocumentCard key={`${document.email_id}:${document.filename}`} document={document} />
                  ))}
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8 text-center text-sm text-slate-400">
                  No PDF attachments match this search.
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}
