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
  Layers,
  AlertTriangle,
  X,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

export default function VesselCalendar({ 
  calendarData, 
  selectedPort, 
  onPortChange, 
  onAssignContainer, 
  onAutoConfirmBooking 
}) {
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedDateFilter, setSelectedDateFilter] = useState(null);
  const [targetVesselId, setTargetVesselId] = useState('');
  const [assignForm, setAssignForm] = useState({
    booking_no: '',
    company: '',
    containers: 1,
    destination_port: 'Rotterdam (NLRTM)'
  });

  // Mismatch Warning Popup State
  const [mismatchWarning, setMismatchWarning] = useState(null);

  const schedule = calendarData?.schedule || [];
  const pendingBookings = calendarData?.pending_bookings || [];
  const availablePorts = calendarData?.available_ports || [];

  // Unassigned Cargo Pool for Quick Assign
  const unassignedCargo = [
    { booking_no: 'UNASSIGNED-BK-101', company: 'Global Traders Inc', containers: 6, destination_port: 'Rotterdam (NLRTM)' },
    { booking_no: 'UNASSIGNED-BK-102', company: 'Pacific Logistics Ltd', containers: 4, destination_port: 'Hamburg (DEHAM)' },
    { booking_no: 'UNASSIGNED-BK-103', company: 'Fast Freight GmbH', containers: 2, destination_port: 'Tokyo (JPTYO)' }
  ];

  // Calendar dates generator for Sept/Oct 2026 grid view
  const calendarDays = Array.from({ length: 30 }, (_, i) => {
    const dayNum = i + 1;
    const dateStr = `2026-09-${dayNum < 10 ? '0' + dayNum : dayNum}`;
    
    // Check arriving & departing vessels for this date
    const arriving = schedule.filter(v => v.eta_date === dateStr);
    const departing = schedule.filter(v => v.etd_date === dateStr);

    return {
      dayNum,
      dateStr,
      arriving,
      departing
    };
  });

  // Filter vessels based on selected date or port filter
  const filteredSchedule = schedule.filter(v => {
    let matchPort = true;
    let matchDate = true;

    if (selectedPort && selectedPort !== 'ALL') {
      const pLower = selectedPort.lower ? selectedPort.lower() : selectedPort.toLowerCase();
      const vDest = v.destination_port.toLowerCase();
      const vCode = v.port_code.toLowerCase();
      matchPort = vDest.includes(pLower) || vCode.includes(pLower) || pLower.includes(vCode);
    }

    if (selectedDateFilter) {
      matchDate = v.eta_date === selectedDateFilter || v.etd_date === selectedDateFilter;
    }

    return matchPort && matchDate;
  });

  // Handle Container Assignment with Destination Mismatch Check
  const handleAssignAttempt = (cargoItem, vesselId) => {
    const vessel = schedule.find(v => v.id === vesselId);
    if (!vessel) return;

    // Normalize port names for check
    const cargoPort = cargoItem.destination_port || 'Rotterdam (NLRTM)';
    const vesselPort = vessel.destination_port;

    const isMismatch = !vesselPort.toLowerCase().includes(cargoPort.toLowerCase().slice(0, 5));

    if (isMismatch) {
      // Trigger warning popup modal
      setMismatchWarning({
        cargoItem,
        vessel,
        message: `Destination Mismatch Alert: Order destination "${cargoPort}" does NOT match target vessel destination "${vesselPort}".`
      });
    } else {
      // Direct assignment
      executeAssignment(cargoItem, vesselId);
    }
  };

  const executeAssignment = (cargoItem, vesselId) => {
    onAssignContainer({
      vessel_id: vesselId,
      booking_no: cargoItem.booking_no,
      company: cargoItem.company,
      containers: cargoItem.containers
    });
    setMismatchWarning(null);
    setShowAssignModal(false);
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    const cargoItem = {
      booking_no: assignForm.booking_no || `BK-MANUAL-${Math.floor(Math.random() * 1000)}`,
      company: assignForm.company || 'Manual Container Allocation',
      containers: parseInt(assignForm.containers) || 1,
      destination_port: assignForm.destination_port
    };
    handleAssignAttempt(cargoItem, targetVesselId);
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950 relative">
      {/* Calendar Header Bar */}
      <div className="p-4 border-b border-slate-800 glass-panel flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <CalendarIcon className="w-5 h-5 text-cyan-400" />
            <span>Interactive Vessel Schedule Calendar Grid</span>
          </h2>
          <p className="text-xs text-slate-400">
            Click dates to jump to vessel departures (<span className="text-cyan-400 font-bold">Neon Blue</span>) & arrivals (<span className="text-indigo-400 font-bold">Navy Blue</span>).
          </p>
        </div>

        {/* Global Destination Port Filter & Quick Actions */}
        <div className="flex items-center space-x-3">
          {selectedDateFilter && (
            <button
              onClick={() => setSelectedDateFilter(null)}
              className="px-3 py-1.5 rounded-xl bg-slate-800 text-xs font-mono text-cyan-300 border border-slate-700 hover:bg-slate-700 transition"
            >
              Selected Date: {selectedDateFilter} ✕ Clear Date
            </button>
          )}

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
                  {port === 'ALL' ? '🌐 All Destination Ports' : port}
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
            <span>Assign Container</span>
          </button>
        </div>
      </div>

      {/* Main Scrollable Calendar Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* 1. INITIAL INTERACTIVE CALENDAR MONTH GRID VIEW */}
        <div className="glass-card rounded-2xl border border-slate-800 p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
              <CalendarIcon className="w-4.5 h-4.5 text-cyan-400" />
              <span>September 2026 Vessel Schedule Grid</span>
            </h3>

            {/* Legend for Arriving vs Departing */}
            <div className="flex items-center space-x-4 text-xs font-mono">
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full bg-indigo-900 border border-indigo-500"></span>
                <span className="text-indigo-300 font-semibold">Arriving (Navy Blue)</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400"></span>
                <span className="text-cyan-400 font-bold">Departing (Neon Blue)</span>
              </span>
            </div>
          </div>

          {/* 7-Day Header Row */}
          <div className="grid grid-cols-7 gap-2 text-center text-xs font-bold text-slate-400 font-mono">
            <span>MON</span><span>TUE</span><span>WED</span><span>THU</span><span>FRI</span><span>SAT</span><span>SUN</span>
          </div>

          {/* 30-Day Grid Cells */}
          <div className="grid grid-cols-7 gap-2 text-xs">
            {calendarDays.map((day) => {
              const isSelected = selectedDateFilter === day.dateStr;
              const hasArriving = day.arriving.length > 0;
              const hasDeparting = day.departing.length > 0;

              return (
                <div
                  key={day.dateStr}
                  onClick={() => setSelectedDateFilter(isSelected ? null : day.dateStr)}
                  className={`min-h-[72px] p-2 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? 'bg-cyan-950/60 border-cyan-400 ring-2 ring-cyan-500/40'
                      : (hasArriving || hasDeparting)
                      ? 'bg-slate-900/90 border-slate-700/80 hover:border-slate-500'
                      : 'bg-slate-950/40 border-slate-800/60 text-slate-600 hover:bg-slate-900/40'
                  }`}
                >
                  <span className={`font-mono text-xs font-bold ${isSelected ? 'text-cyan-300' : 'text-slate-300'}`}>
                    Sep {day.dayNum}
                  </span>

                  <div className="space-y-1 mt-1">
                    {/* Navy Blue Arriving Vessels */}
                    {day.arriving.map((v) => (
                      <div
                        key={v.id}
                        className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-indigo-950 text-indigo-300 border border-indigo-700/80 truncate shadow"
                        title={`Arriving ETA: ${v.vessel_name} (${v.destination_port})`}
                      >
                        🛬 {v.vessel_name}
                      </div>
                    ))}

                    {/* Neon Blue Departing Vessels */}
                    {day.departing.map((v) => (
                      <div
                        key={v.id}
                        className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-400 text-slate-950 border border-cyan-300 truncate shadow-md shadow-cyan-950/50"
                        title={`Departing ETD: ${v.vessel_name} (${v.destination_port})`}
                      >
                        🛫 {v.vessel_name}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 2. AUTOMATED BOOKING INTEGRATION BANNER */}
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

        {/* 3. UNASSIGNED CARGO DOCK BANNER */}
        <div className="p-4 rounded-xl glass-card border border-slate-800 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Unassigned Cargo Dock (Assign Order to Vessel)</span>
          </h4>
          <div className="grid grid-cols-3 gap-3">
            {unassignedCargo.map((item, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-xs font-mono">
                <div>
                  <span className="text-cyan-400 font-bold block">{item.booking_no}</span>
                  <span className="text-slate-300">{item.company} ({item.containers} TEU)</span>
                  <span className="text-[10px] text-slate-500 block">Dest: {item.destination_port}</span>
                </div>
                {schedule.length > 0 && (
                  <button
                    onClick={() => handleAssignAttempt(item, schedule[0].id)}
                    className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-[11px]"
                  >
                    Assign
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 4. VESSEL SCHEDULES LIST/GRID */}
        <div className="grid grid-cols-2 gap-6">
          {filteredSchedule.map((vessel) => (
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
                {/* Navy Blue Arrival Tag */}
                <div className="p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-800/80">
                  <span className="text-indigo-400 flex items-center space-x-1 font-bold">
                    <Clock className="w-3.5 h-3.5" />
                    <span>🛬 Arriving (Navy Blue):</span>
                  </span>
                  <div className="text-indigo-200 font-bold mt-1 text-sm">
                    {vessel.eta_date}
                  </div>
                </div>

                {/* Neon Blue Departure Tag */}
                <div className="p-2.5 rounded-lg bg-cyan-950/40 border border-cyan-800/80">
                  <span className="text-cyan-400 flex items-center space-x-1 font-bold">
                    <Clock className="w-3.5 h-3.5" />
                    <span>🛫 Departing (Neon Blue):</span>
                  </span>
                  <div className="text-cyan-300 font-bold mt-1 text-sm">
                    {vessel.etd_date}
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

      {/* 5. DESTINATION MISMATCH WARNING POPUP MODAL */}
      {mismatchWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
          <div className="glass-panel w-full max-w-md rounded-2xl border border-rose-500/60 shadow-2xl p-6 space-y-4">
            <div className="flex items-center space-x-3 text-rose-400">
              <div className="w-10 h-10 rounded-xl bg-rose-950/80 border border-rose-800 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-6 h-6 text-rose-400" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-100">Destination Mismatch Alert</h3>
                <span className="text-xs font-mono text-rose-400">Routing Discrepancy Flagged</span>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed bg-slate-900 p-3 rounded-xl border border-slate-800 font-mono">
              {mismatchWarning.message}
            </p>

            <div className="text-xs space-y-1 font-mono bg-slate-900/60 p-3 rounded-xl border border-slate-800/80">
              <div>• Order Destination: <strong className="text-amber-400">{mismatchWarning.cargoItem.destination_port}</strong></div>
              <div>• Vessel Destination: <strong className="text-cyan-400">{mismatchWarning.vessel.destination_port}</strong></div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                onClick={() => setMismatchWarning(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs"
              >
                Cancel Assignment
              </button>
              <button
                onClick={() => executeAssignment(mismatchWarning.cargoItem, mismatchWarning.vessel.id)}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-lg shadow-rose-950/50"
              >
                Confirm Mismatched Assignment
              </button>
            </div>
          </div>
        </div>
      )}

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
                <label className="block text-slate-400 mb-1">Order Destination Port:</label>
                <select
                  value={assignForm.destination_port}
                  onChange={(e) => setAssignForm({ ...assignForm, destination_port: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                >
                  <option value="Rotterdam (NLRTM)">Rotterdam (NLRTM)</option>
                  <option value="Hamburg (DEHAM)">Hamburg (DEHAM)</option>
                  <option value="Los Angeles (USLAX)">Los Angeles (USLAX)</option>
                  <option value="Tokyo (JPTYO)">Tokyo (JPTYO)</option>
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
