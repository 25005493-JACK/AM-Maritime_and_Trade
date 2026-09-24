import React, { useState, useEffect } from 'react';
import {
  Brain,
  TrendingUp,
  RefreshCw,
  Search,
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  Cpu,
  UserCheck,
  Layers,
  History,
  Info,
  Clock
} from 'lucide-react';
import { apiFetch } from '../api.js';

export function ReflectionsPanel({ reflectionsBySender, onRefresh }) {
  const [filter, setFilter] = useState('');
  const senders = Object.keys(reflectionsBySender || {}).sort();

  const filteredSenders = senders.filter((s) =>
    s.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="glass-card rounded-xl border border-slate-800 p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-purple-950/60 border border-purple-500/40 text-purple-300">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <span>Reflexion Episodic Memory Buffer</span>
              <span className="text-[10px] font-mono font-normal px-2 py-0.5 rounded-full bg-purple-950/50 text-purple-300 border border-purple-700/50">
                {Object.values(reflectionsBySender || {}).flat().length} Lessons
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Natural-language lessons learned from human corrections and retrieved into prompt context.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Filter by sender domain..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500"
            />
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              title="Refresh memories"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {filteredSenders.length === 0 ? (
        <div className="p-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
          <Brain className="w-8 h-8 mx-auto mb-2 text-slate-600 opacity-60" />
          <p>No episodic memories found for this filter.</p>
          <p className="text-[11px] text-slate-600 mt-1">
            Lessons are generated automatically whenever a human reviewer overrides or corrects an AI extraction.
          </p>
        </div>
      ) : (
        <div className="space-y-4 max-h-[500px] overflow-y-auto pr-1">
          {filteredSenders.map((sender) => {
            const items = reflectionsBySender[sender] || [];
            return (
              <div key={sender} className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-3.5 space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-200">{sender}</span>
                    <span className="text-[10px] text-slate-500 font-mono">({items.length} lessons)</span>
                  </div>
                  <span className="text-[10px] font-mono text-purple-400 bg-purple-950/40 border border-purple-800/50 px-2 py-0.5 rounded">
                    Total Reuses: {items.reduce((acc, curr) => acc + (curr.times_retrieved || 0), 0)}
                  </span>
                </div>

                <div className="space-y-2">
                  {items.map((ref) => (
                    <div
                      key={ref.id}
                      className="rounded-lg border border-purple-900/30 bg-purple-950/20 p-2.5 space-y-1.5"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 text-[10px]">
                        <div className="flex items-center gap-2">
                          <span className="px-1.5 py-0.5 rounded font-mono font-semibold bg-slate-800 text-cyan-300 border border-slate-700">
                            {ref.doc_type || 'SI'}
                          </span>
                          {ref.field_name && (
                            <span className="px-1.5 py-0.5 rounded font-mono bg-slate-800 text-purple-300 border border-slate-700">
                              Field: {ref.field_name}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-slate-400 font-mono">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-slate-500" />
                            {new Date(ref.created_at).toLocaleDateString()}
                          </span>
                          <span
                            className={`font-semibold px-2 py-0.5 rounded border ${
                              (ref.times_retrieved || 0) > 0
                                ? 'bg-emerald-950/50 border-emerald-700/60 text-emerald-300'
                                : 'bg-slate-800 border-slate-700 text-slate-400'
                            }`}
                          >
                            Retrieved {ref.times_retrieved || 0} times
                          </span>
                        </div>
                      </div>

                      <p className="text-xs text-purple-100/90 italic pl-2.5 border-l-2 border-purple-500 font-sans leading-relaxed">
                        &ldquo;{ref.reflection_text}&rdquo;
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function AgentLearningDashboard() {
  const [policies, setPolicies] = useState([]);
  const [reflectionsData, setReflectionsData] = useState({ total: 0, by_sender: {} });
  const [loading, setLoading] = useState(true);
  const [searchDomain, setSearchDomain] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [polRes, refRes] = await Promise.all([
        apiFetch('/api/routing-policy'),
        apiFetch('/api/reflections')
      ]);

      if (polRes.ok) {
        const polJson = await polRes.json();
        setPolicies(polJson.policies || []);
      }
      if (refRes.ok) {
        const refJson = await refRes.json();
        setReflectionsData(refJson);
      }
    } catch (err) {
      console.error('Failed to load learning data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredPolicies = policies.filter((p) =>
    (p.sender_domain || '').toLowerCase().includes(searchDomain.toLowerCase())
  );

  const totalOutcomes = policies.reduce((acc, curr) => acc + (curr.outcomes_count || 0), 0);
  const avgTrust = policies.length > 0
    ? Math.round((policies.reduce((acc, curr) => acc + curr.mean_trust, 0) / policies.length) * 100)
    : 50;

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-950 text-slate-100">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 shadow-md shadow-indigo-900/40">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-bold tracking-tight text-slate-100">
              Agent Self-Learning & Routing Dashboard
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Online, feedback-driven learning: Thompson Sampling dynamically balances AI trust vs. human review per sender, 
            while Reflexion episodic memory stores and reuses natural language lessons from human corrections.
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400 font-medium">Average Posterior Trust</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-cyan-300">{avgTrust}%</span>
            <span className="text-[11px] text-slate-500 font-mono">across all senders</span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-2">
            <div
              className="bg-gradient-to-r from-indigo-500 to-cyan-400 h-full rounded-full transition-all duration-500"
              style={{ width: `${avgTrust}%` }}
            />
          </div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400 font-medium">Total Feedback Outcomes</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-indigo-300">{totalOutcomes}</span>
            <span className="text-[11px] text-slate-500 font-mono">human corrections & confirms</span>
          </div>
          <p className="text-[10px] text-slate-400 mt-2">
            Online Beta-Bernoulli updates (&alpha; / &beta; parameters)
          </p>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-xs text-slate-400 font-medium">Episodic Memories Active</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-purple-300">{reflectionsData.total || 0}</span>
            <span className="text-[11px] text-slate-500 font-mono">
              across {reflectionsData.senders_count || 0} sender domains
            </span>
          </div>
          <p className="text-[10px] text-slate-400 mt-2">
            Prompt-injected on future documents from same sender
          </p>
        </div>
      </div>

      {/* Main Section: Bayesian Routing Table */}
      <div className="glass-card rounded-xl border border-slate-800 p-4 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              <span>Bayesian Routing Policy (Thompson Sampling)</span>
            </h3>
            <p className="text-xs text-slate-400">
              Each sender maintains a Beta(&alpha;, &beta;) posterior. Sampling above 60% routes to AI; below routes human-first.
            </p>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search sender domain..."
              value={searchDomain}
              onChange={(e) => setSearchDomain(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        {filteredPolicies.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
            <TrendingUp className="w-8 h-8 mx-auto mb-2 text-slate-600 opacity-60" />
            <p>No routing policies recorded yet.</p>
            <p className="text-[11px] text-slate-600 mt-1">
              Policies will automatically calibrate as documents are processed and reviewed.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                  <th className="pb-2 font-medium">Sender Domain</th>
                  <th className="pb-2 font-medium">Trust Score (Mean)</th>
                  <th className="pb-2 font-medium">Posterior Distribution</th>
                  <th className="pb-2 font-medium">Feedback Count</th>
                  <th className="pb-2 font-medium">Current Routing Stance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {filteredPolicies.map((pol) => {
                  const pct = Math.round(pol.mean_trust * 100);
                  const isHighTrust = pct >= 60;
                  return (
                    <tr key={`${pol.sender_domain}-${pol.field_name || '*'}`} className="hover:bg-slate-900/40 transition">
                      <td className="py-2.5 text-slate-200 font-semibold font-sans">
                        {pol.sender_domain}
                        {pol.field_name && (
                          <span className="block text-[10px] text-cyan-400 font-mono">
                            Field: {pol.field_name}
                          </span>
                        )}
                      </td>
                      <td className="py-2.5">
                        <div className="flex items-center gap-2">
                          <span className={`font-bold ${isHighTrust ? 'text-emerald-400' : 'text-amber-400'}`}>
                            {pct}%
                          </span>
                          <div className="w-24 bg-slate-800 h-2 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                isHighTrust
                                  ? 'bg-emerald-500'
                                  : pct >= 40
                                  ? 'bg-amber-500'
                                  : 'bg-rose-500'
                              }`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-2.5 text-slate-400 text-[11px]">
                        <span className="text-emerald-300">&alpha;={pol.alpha}</span>
                        <span className="mx-1 text-slate-600">/</span>
                        <span className="text-rose-300">&beta;={pol.beta}</span>
                      </td>
                      <td className="py-2.5 text-slate-300">
                        {pol.outcomes_count} outcomes
                      </td>
                      <td className="py-2.5">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-[10px] ${
                            isHighTrust
                              ? 'bg-emerald-950/50 border-emerald-600/60 text-emerald-300'
                              : 'bg-amber-950/50 border-amber-600/60 text-amber-300'
                          }`}
                        >
                          {isHighTrust ? <Cpu className="w-3 h-3" /> : <UserCheck className="w-3 h-3" />}
                          <span>{isHighTrust ? 'AI Extraction First' : 'Human-First Favored'}</span>
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Reflexion Episodic Memory Buffer View */}
      <ReflectionsPanel
        reflectionsBySender={reflectionsData.by_sender}
        onRefresh={fetchData}
      />
    </div>
  );
}
