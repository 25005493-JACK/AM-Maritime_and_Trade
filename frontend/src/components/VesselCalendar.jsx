import React, { useState } from 'react';
import { 
  Calendar as CalendarIcon, 
  Ship, 
  Filter, 
  Plus, 
  Sparkles, 
  CheckCircle2, 
  Package, 
  Anchor,
  Clock,
  Layers
} from 'lucide-react';

export default function VesselCalendar({ 
  calendarData, 
  selectedPort, 
  onPortChange, 
  onAssignContainer, 
  onAutoConfirmBooking 
}) {
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [targetVesselId, setTargetVesselId] = useState('');
  const [assignForm, setAssignForm] = useState({
    booking_no: '',
    company: '',
    containers: 1
  });

  const schedule = calendarData?.schedule || [];
  const pendingBookings = calendarData?.pending_bookings || [];
  const availablePorts = calendarData?.available_ports || [];

  // Unassigned Cargo Pool for Drag/Drop / Quick Assign
  const unassignedCargo = [
    { booking_no: 'UNASSIGNED-BK-101', company: 'Global Traders Inc', containers: 6, destination_port: 'Rotterdam (NLRTM)' },
    { booking_no: 'UNASSIGNED-BK-102', company: 'Pacific Logistics Ltd', containers: 4, destination_port: 'Hamburg (DEHAM)' },
    { booking_no: 'UNASSIGNED-BK-103', company: 'Fast Freight GmbH', containers: 2, destination_port: 'Tokyo (JPTYO)' }
  ];

  const handleFormSubmit = (e) => {
    e.preventDefault();
    onAssignContainer({
      vessel_id: targetVesselId,
      booking_no: assignForm.booking_no || `BK-MANUAL-${Math.floor(Math.random() * 1000)}`,
      company: assignForm.company || 'Manual Container Allocation',
      containers: parseInt(assignForm.containers) || 1
    });
    setShowAssignModal(false);
    setAssignForm({ booking_no: '', company: '', containers: 1 });
  };

  const handleQuickAssignCargo = (cargoItem, vesselId) => {
    onAssignContainer({
      vessel_id: vesselId,
      booking_no: cargoItem.booking_no,
      company: cargoItem.company,
      containers: cargoItem.containers
    });
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950">
      {/* Calendar Header Bar */}
      <div className="p-4 border-b border-slate-800 glass-panel flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <CalendarIcon className="w-5 h-5 text-cyan-400" />
            <span>Dynamic Vessel & Container Scheduling Calendar</span>
          </h2>
          <p className="text-xs text-slate-400">
            Real-time port scheduling, automated booking sync, and container slot allocation.
          </p>
        </div>

        {/* Global Destination Port Filter Dropdown */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-700 px-3 py-1.5 rounded-xl shadow">
            <Filter className="w-4 h-4 text-cyan-400" />
            <span className="text-xs text-slate-400 font-medium">Destination Port Filter:</span>
            <select
              value={selectedPort}
              onChange={(e) => onPortChange(e.target.value)}
              className="bg-transparent text-xs font-bold text-cyan-300 focus:outline-none cursor-pointer"
            >
              {availablePorts.map((port) => (
                <option key={port} value={port} className="bg-slate-900 text-slate-200">
                  {port === 'ALL' ? '🌐 All Destination Ports (Global View)' : port}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => {
              if (schedule.length > 0) setTargetVesselId(schedule[0].id);
              setShowAssignModal(true);
            }}
            className="px-3.5 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow transition"
          >
            <Plus className="w-4 h-4" />
            <span>Manual Container Slot Assignment</span>
          </button>
        </div>
      </div>

      {/* Main Calendar Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Automated Booking Integration Banner */}
        {pendingBookings.length > 0 && (
          <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 via-indigo-950/50 to-slate-900 border border-indigo-500/40 shadow-xl flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center shrink-0">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                  Automated Booking Integration (AI Inbox Auto-Sync)
                </h4>
                <p className="text-sm font-medium text-slate-100 mt-0.5">
                  Extracted booking inquiry from <strong className="text-cyan-400">{pendingBookings[0].company}</strong> ({pendingBookings[0].requested_containers} containers for {pendingBookings[0].destination_port})
                </p>
                <span className="text-[11px] text-slate-400 font-mono">
                  Suggested Target Vessel: {pendingBookings[0].suggested_vessel_name}
                </span>
              </div>
            </div>

            <button
              onClick={() => onAutoConfirmBooking(pendingBookings[0].email_id)}
              disabled={pendingBookings[0].status.includes("Confirmed")}
              className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 shadow transition ${
                pendingBookings[0].status.includes("Confirmed")
                  ? 'bg-slate-800 text-emerald-400 border border-emerald-500/30'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-950/50'
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{pendingBookings[0].status.includes("Confirmed") ? 'Booking Scheduled' : 'Confirm to Calendar'}</span>
            </button>
          </div>
        )}

        {/* Global Port Strict Filtering Notice Banner */}
        {selectedPort !== 'ALL' && (
          <div className="p-3 rounded-xl bg-slate-900/80 border border-cyan-500/30 text-xs text-cyan-300 flex items-center justify-between font-mono">
            <span>
              Showing vessels strictly filtered for <strong>{selectedPort}</strong> ({schedule.length} ship(s) arriving).
            </span>
            <button 
              onClick={() => onPortChange('ALL')}
              className="text-slate-400 hover:text-slate-200 underline text-[11px]"
            >
              Clear Filter (Show All Ports)
            </button>
          </div>
        )}

        {/* Unassigned Cargo Dock Banner */}
        <div className="p-4 rounded-xl glass-card border border-slate-800 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Unassigned Cargo Dock (Quick Assign to Vessel)</span>
          </h4>
          <div className="grid grid-cols-3 gap-3">
            {unassignedCargo.map((item, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-xs font-mono">
                <div>
                  <span className="text-cyan-400 font-bold block">{item.booking_no}</span>
                  <span className="text-slate-300">{item.company} ({item.containers} TEU)</span>
                </div>
                {schedule.length > 0 && (
                  <button
                    onClick={() => handleQuickAssignCargo(item, schedule[0].id)}
                    className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-[11px]"
                  >
                    Assign
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Vessel Schedules Grid */}
        <div className="grid grid-cols-2 gap-6">
          {schedule.map((vessel) => (
            <div key={vessel.id} className="glass-card rounded-xl border border-slate-800 p-5 space-y-4 hover:border-slate-700 transition">
              <div className="flex items-start justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-cyan-950/60 text-cyan-400 border border-cyan-800/60 flex items-center justify-center">
                    <Ship className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                      <span>{vessel.vessel_name}</span>
                      <span className="text-xs font-mono text-cyan-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-700">
                        {vessel.voyage}
                      </span>
                    </h3>
                    <div className="flex items-center space-x-2 text-xs text-slate-400 mt-0.5">
                      <Anchor className="w-3.5 h-3.5 text-slate-500" />
                      <span>Carrier: <strong className="text-slate-200">{vessel.carrier}</strong></span>
                      <span>•</span>
                      <span>Destination: <strong className="text-cyan-300">{vessel.destination_port}</strong></span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => {
                    setTargetVesselId(vessel.id);
                    setShowAssignModal(true);
                  }}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 flex items-center space-x-1 transition"
                  title="Assign container to this ship"
                >
                  <Plus className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Assign</span>
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80">
                  <span className="text-slate-500 flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>ETA / ETD Dates:</span>
                  </span>
                  <div className="text-slate-200 font-bold mt-1">
                    {vessel.eta_date} <span className="text-slate-500">→</span> {vessel.etd_date}
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Capacity TEU:</span>
                    <strong className="text-cyan-400">{vessel.total_booked_containers} / {vessel.total_capacity_teu} TEU</strong>
                  </div>
                  <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden mt-2 border border-slate-800">
                    <div 
                      className={`h-full transition-all duration-300 ${
                        vessel.utilization_pct > 90 ? 'bg-rose-500' : vessel.utilization_pct > 75 ? 'bg-amber-400' : 'bg-cyan-400'
                      }`}
                      style={{ width: `${Math.min(vessel.utilization_pct, 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1">
                  <Package className="w-3.5 h-3.5 text-slate-500" />
                  <span>Allocated Container Bookings ({vessel.allocated_containers.length}):</span>
                </h4>
                <div className="space-y-1.5">
                  {vessel.allocated_containers.map((c, i) => (
                    <div key={i} className="p-2 rounded bg-slate-900/90 border border-slate-800 flex items-center justify-between text-xs font-mono">
                      <div className="flex items-center space-x-2">
                        <span className="text-cyan-400 font-bold">{c.booking_no}</span>
                        <span className="text-slate-300">{c.company}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="bg-cyan-950/80 text-cyan-300 px-2 py-0.5 rounded border border-cyan-800/60 text-[11px]">
                          {c.containers} container(s)
                        </span>
                        <span className="text-slate-500 text-[10px]">{c.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Manual Container Slot Assignment Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="glass-panel w-full max-w-lg rounded-2xl border border-slate-700 shadow-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <Package className="w-5 h-5 text-cyan-400" />
              <span>Manual Container Allocation to Vessel</span>
            </h3>

            <form onSubmit={handleFormSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Target Vessel & Port Schedule:</label>
                <select
                  value={targetVesselId}
                  onChange={(e) => setTargetVesselId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                >
                  {schedule.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.vessel_name} ({v.voyage}) - {v.destination_port}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Booking Reference No:</label>
                <input
                  type="text"
                  placeholder="e.g. BK-2026-99"
                  value={assignForm.booking_no}
                  onChange={(e) => setAssignForm({ ...assignForm, booking_no: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Company / Shipper Name:</label>
                <input
                  type="text"
                  placeholder="e.g. Global Logistics Inc"
                  value={assignForm.company}
                  onChange={(e) => setAssignForm({ ...assignForm, company: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Container Count (TEU):</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={assignForm.containers}
                  onChange={(e) => setAssignForm({ ...assignForm, containers: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAssignModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold shadow-lg shadow-cyan-950/50"
                >
                  Confirm Allocation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
