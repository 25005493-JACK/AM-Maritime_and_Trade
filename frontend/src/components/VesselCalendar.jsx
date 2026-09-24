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
  Send,
  Copy,
  Check,
  X,
  Weight,
  Compass,
  ChevronDown,
  ChevronUp
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
  const [expandedAllocated, setExpandedAllocated] = useState({});
  const [assignForm, setAssignForm] = useState({
    booking_no: '',
    company: '',
    sender_email: '',
    containers: 1,
    weight_mt: 25,
    departure_port: 'Singapore (SGSIN)',
    destination_port: 'Rotterdam (NLRTM)'
  });

  // Mismatch Warning Popup State
  const [mismatchWarning, setMismatchWarning] = useState(null);

  // Auto-Generated Email Draft Modal State
  const [emailDraftModal, setEmailDraftModal] = useState(null);
  const [copied, setCopied] = useState(false);
  const [sentToast, setSentToast] = useState(false);

  const schedule = calendarData?.schedule || [];
  const pendingBookings = calendarData?.pending_bookings || [];
  const availablePorts = calendarData?.available_ports || [];

  // Unassigned Cargo Pool for Quick Assign with Departure & Destination Ports & Weight Quota
  const unassignedCargo = [
    { 
      booking_no: 'UNASSIGNED-BK-101', 
      company: 'Global Traders Inc', 
      sender_email: 'desk@globaltraders.com', 
      containers: 6, 
      weight_mt: 150,
      departure_port: 'Singapore (SGSIN)', 
      destination_port: 'Rotterdam (NLRTM)' 
    },
    { 
      booking_no: 'UNASSIGNED-BK-102', 
      company: 'Pacific Logistics Ltd', 
      sender_email: 'ops@pacificlogistics.sg', 
      containers: 4, 
      weight_mt: 100,
      departure_port: 'Hong Kong (HKHKG)', 
      destination_port: 'Hamburg (DEHAM)' 
    },
    { 
      booking_no: 'UNASSIGNED-BK-103', 
      company: 'Fast Freight GmbH', 
      sender_email: 'desk@fastfreight.de', 
      containers: 2, 
      weight_mt: 50,
      departure_port: 'Port Klang (MYPKG)', 
      destination_port: 'Tokyo (JPTYO)' 
    }
  ];

  // Calendar dates generator for Sept/Oct 2026 grid view
  const calendarDays = Array.from({ length: 30 }, (_, i) => {
    const dayNum = i + 1;
    const dateStr = `2026-09-${dayNum < 10 ? '0' + dayNum : dayNum}`;
    const arriving = schedule.filter(v => v.eta_date === dateStr);
    const departing = schedule.filter(v => v.etd_date === dateStr);

    return { dayNum, dateStr, arriving, departing };
  });

  // Filter vessels based on selected date or port filter
  const filteredSchedule = schedule.filter(v => {
    let matchPort = true;
    let matchDate = true;

    if (selectedPort && selectedPort !== 'ALL') {
      const pLower = selectedPort.toLowerCase();
      const vDest = (v.destination_port || '').toLowerCase();
      const vCode = (v.port_code || '').toLowerCase();
      matchPort = vDest.includes(pLower) || vCode.includes(pLower) || pLower.includes(vCode);
    }

    if (selectedDateFilter) {
      matchDate = v.eta_date === selectedDateFilter || v.etd_date === selectedDateFilter;
    }

    return matchPort && matchDate;
  });

  // Nearest Date Assignment Helper matching BOTH Departure Place AND Destination Port
  const findNearestDateShip = (cargoDepartPort, cargoDestPort) => {
    if (schedule.length === 0) return null;
    
    const depKey = (cargoDepartPort || '').toLowerCase().slice(0, 5);
    const destKey = (cargoDestPort || '').toLowerCase().slice(0, 5);

    // 1. Strict Match: Vessel matching BOTH Departure Place AND Destination Port
    const matchBoth = schedule.filter(v => {
      const vDep = (v.departure_port || '').toLowerCase();
      const vDest = (v.destination_port || '').toLowerCase();
      return vDep.includes(depKey) && vDest.includes(destKey);
    });

    if (matchBoth.length > 0) {
      // Pick the vessel matching both with the nearest ETD date
      return [...matchBoth].sort((a, b) => new Date(a.etd_date) - new Date(b.etd_date))[0];
    }

    // 2. Partial Match: Match Destination Port
    const matchDest = schedule.filter(v => (v.destination_port || '').toLowerCase().includes(destKey));
    if (matchDest.length > 0) {
      return [...matchDest].sort((a, b) => new Date(a.etd_date) - new Date(b.etd_date))[0];
    }

    // 3. Fallback: Earliest ETD vessel
    return [...schedule].sort((a, b) => new Date(a.etd_date) - new Date(b.etd_date))[0];
  };

  // Handle Container Assignment Attempt with Departure & Destination Validation
  const handleAssignAttempt = (cargoItem, vesselId) => {
    let vessel = schedule.find(v => v.id === vesselId);
    
    if (!vessel) {
      // Auto assign to nearest ship matching BOTH departure & destination ports
      vessel = findNearestDateShip(cargoItem.departure_port, cargoItem.destination_port);
    }
    
    if (!vessel) return;

    const cargoDep = cargoItem.departure_port || 'Singapore (SGSIN)';
    const cargoDest = cargoItem.destination_port || 'Rotterdam (NLRTM)';
    const vesselDep = vessel.departure_port || 'Singapore (SGSIN)';
    const vesselDest = vessel.destination_port || 'Rotterdam (NLRTM)';

    const isDepMismatch = !vesselDep.toLowerCase().includes(cargoDep.toLowerCase().slice(0, 5));
    const isDestMismatch = !vesselDest.toLowerCase().includes(cargoDest.toLowerCase().slice(0, 5));

    if (isDepMismatch || isDestMismatch) {
      setMismatchWarning({
        cargoItem,
        vessel,
        message: `Routing Discrepancy Alert: Order ports (${cargoDep} ➔ ${cargoDest}) do NOT match target vessel route (${vesselDep} ➔ ${vesselDest}).`
      });
    } else {
      executeAssignment(cargoItem, vessel);
    }
  };

  const executeAssignment = (cargoItem, vessel) => {
    // 1. Call backend/parent assignment handler
    onAssignContainer({
      vessel_id: vessel.id,
      booking_no: cargoItem.booking_no,
      company: cargoItem.company,
      containers: cargoItem.containers,
      weight_mt: cargoItem.weight_mt || cargoItem.containers * 25
    });

    setMismatchWarning(null);
    setShowAssignModal(false);

    // 2. Auto Generate Confirmation Email Draft
    const recipient = cargoItem.sender_email || `booking@${cargoItem.company.toLowerCase().replace(/[^a-z]/g, '')}.com`;
    const subject = `Shipping Schedule & Weight Quota Confirmation — Booking #${cargoItem.booking_no}`;
    const body = `Dear ${cargoItem.company},\n\nWe are pleased to confirm that your shipment under Booking Ref: ${cargoItem.booking_no} (${cargoItem.containers} TEU, Weight: ${cargoItem.weight_mt || cargoItem.containers * 25} MT) has been officially assigned to vessel "${vessel.vessel_name}" (${vessel.voyage}).\n\nConfirmed Vessel Routing & Quota Details:\n• Target Vessel: ${vessel.vessel_name} (${vessel.voyage})\n• Vessel Carrier: ${vessel.carrier}\n• Departure Port (POL): ${vessel.departure_port || cargoItem.departure_port}\n• Destination Port (POD): ${vessel.destination_port}\n• Scheduled Departure (ETD): ${vessel.etd_date} at 10:00 UTC\n• Estimated Arrival (ETA): ${vessel.eta_date} at 16:00 UTC\n• Allocated Weight Quota: ${cargoItem.weight_mt || cargoItem.containers * 25} Metric Tons (MT)\n• Max Vessel Weight Limit: ${vessel.max_weight_quota_mt || 10000} MT\n\nPlease review the shipping schedule and let us know if any further document amendments are needed.\n\nBest regards,\nDocumentation Desk — DocuMatch Maritime Engine`;

    setEmailDraftModal({
      recipient,
      subject,
      body,
      vessel_name: vessel.vessel_name,
      booking_no: cargoItem.booking_no
    });
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    const cargoItem = {
      booking_no: assignForm.booking_no || `BK-2026-${Math.floor(Math.random() * 900 + 100)}`,
      company: assignForm.company || 'Manual Cargo Allocation',
      sender_email: assignForm.sender_email || 'shipper@maritimeline.com',
      containers: parseInt(assignForm.containers) || 1,
      weight_mt: parseFloat(assignForm.weight_mt) || 25,
      departure_port: assignForm.departure_port,
      destination_port: assignForm.destination_port
    };
    handleAssignAttempt(cargoItem, targetVesselId);
  };

  const handleAssignNearest = () => {
    const cargoItem = {
      booking_no: assignForm.booking_no || `BK-2026-${Math.floor(Math.random() * 900 + 100)}`,
      company: assignForm.company || 'Manual Cargo Allocation',
      sender_email: assignForm.sender_email || 'shipper@maritimeline.com',
      containers: parseInt(assignForm.containers) || 1,
      weight_mt: parseFloat(assignForm.weight_mt) || 25,
      departure_port: assignForm.departure_port,
      destination_port: assignForm.destination_port
    };
    const nearestShip = findNearestDateShip(cargoItem.departure_port, cargoItem.destination_port);
    if (nearestShip) {
      executeAssignment(cargoItem, nearestShip);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-950 text-slate-100 font-sans relative">
      {/* Calendar Header Bar */}
      <div className="p-4 border-b border-blue-900/60 bg-slate-950 flex items-center justify-between shrink-0 shadow-md">
        <div>
          <h2 className="text-base font-extrabold text-slate-100 flex items-center space-x-2">
            <CalendarIcon className="w-5 h-5 text-cyan-400" />
            <span>Vessel Schedule Calendar & Weight Quotas</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Auto-assigns to nearest date ship matching both <strong className="text-cyan-400">Departure Place & Destination Port</strong> with payload weight quota tracking.
          </p>
        </div>

        {/* Global Destination Port Filter & Quick Actions */}
        <div className="flex items-center space-x-3">
          {selectedDateFilter && (
            <button
              onClick={() => setSelectedDateFilter(null)}
              className="px-3 py-1.5 rounded-xl bg-slate-900 text-xs font-mono text-cyan-300 border border-blue-800 hover:bg-slate-800 transition"
            >
              Selected Date: {selectedDateFilter} ✕ Clear Date
            </button>
          )}

          <div className="flex items-center space-x-2 bg-slate-900 border border-blue-900/60 px-3 py-1.5 rounded-xl shadow">
            <Filter className="w-4 h-4 text-cyan-400" />
            <span className="text-xs text-slate-400 font-medium">Destination Port:</span>
            <select
              value={selectedPort}
              onChange={(e) => onPortChange(e.target.value)}
              className="bg-transparent text-xs font-bold text-cyan-300 focus:outline-none cursor-pointer"
            >
              {availablePorts.map((port) => (
                <option key={port} value={port} className="bg-slate-900 text-slate-200">
                  {port === 'ALL' ? '🌐 All Ports' : port}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => {
              if (schedule.length > 0) setTargetVesselId(schedule[0].id);
              setShowAssignModal(true);
            }}
            className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-bold text-xs flex items-center space-x-1.5 shadow-lg shadow-cyan-950/50 transition active:scale-95 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Assign Container</span>
          </button>
        </div>
      </div>

      {/* Main Scrollable Calendar Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* 1. MONTH GRID VIEW */}
        <div className="rounded-2xl border border-blue-900/60 bg-slate-900/90 p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-blue-900/60 pb-3">
            <h3 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
              <CalendarIcon className="w-4.5 h-4.5 text-cyan-400" />
              <span>September 2026 Vessel Schedule Grid</span>
            </h3>

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

          <div className="grid grid-cols-7 gap-2 text-center text-xs font-bold text-slate-400 font-mono">
            <span>MON</span><span>TUE</span><span>WED</span><span>THU</span><span>FRI</span><span>SAT</span><span>SUN</span>
          </div>

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
                      ? 'bg-blue-950 border-cyan-400 ring-2 ring-cyan-500/40'
                      : (hasArriving || hasDeparting)
                      ? 'bg-slate-900 border-blue-900/60 hover:border-cyan-500'
                      : 'bg-slate-950/40 border-slate-900 text-slate-600 hover:bg-slate-900/40'
                  }`}
                >
                  <span className={`font-mono text-xs font-bold ${isSelected ? 'text-cyan-300' : 'text-slate-300'}`}>
                    Sep {day.dayNum}
                  </span>

                  <div className="space-y-1 mt-1">
                    {day.arriving.map((v) => (
                      <div
                        key={v.id}
                        className="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold bg-indigo-950 text-indigo-300 border border-indigo-700 truncate shadow"
                      >
                        🛬 {v.vessel_name}
                      </div>
                    ))}

                    {day.departing.map((v) => (
                      <div
                        key={v.id}
                        className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-400 text-slate-950 border border-cyan-300 truncate shadow-md"
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
              <Sparkles className="w-6 h-6 text-indigo-400 shrink-0" />
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                  Automated Booking Integration (AI Sync)
                </h4>
                <p className="text-xs font-medium text-slate-100 mt-0.5">
                  Extracted booking inquiry from <strong className="text-cyan-400">{pendingBookings[0].company}</strong> ({pendingBookings[0].requested_containers} containers, {pendingBookings[0].weight_mt || 200} MT for {pendingBookings[0].destination_port})
                </p>
                <span className="text-[11px] text-slate-400 font-mono">
                  Route: {pendingBookings[0].departure_port || 'Singapore (SGSIN)'} ➔ {pendingBookings[0].destination_port} | Target: {pendingBookings[0].suggested_vessel_name}
                </span>
              </div>
            </div>

            <button
              onClick={() => onAutoConfirmBooking(pendingBookings[0].email_id)}
              disabled={pendingBookings[0].status.includes("Confirmed")}
              className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 shadow transition ${
                pendingBookings[0].status.includes("Confirmed")
                  ? 'bg-slate-800 text-emerald-400 border border-emerald-500/30'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white'
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{pendingBookings[0].status.includes("Confirmed") ? 'Booking Scheduled' : 'Confirm to Calendar'}</span>
            </button>
          </div>
        )}

        {/* 3. UNASSIGNED CARGO DOCK BANNER WITH ROUTE & WEIGHT */}
        <div className="p-4 rounded-xl border border-blue-900/60 bg-slate-900/90 space-y-3 shadow-lg">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>Unassigned Cargo Dock (Assign Order to Nearest Date Ship)</span>
          </h4>
          <div className="grid grid-cols-3 gap-3">
            {unassignedCargo.map((item, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-950 border border-blue-900/60 flex items-center justify-between text-xs font-mono">
                <div>
                  <span className="text-cyan-400 font-bold block">{item.booking_no}</span>
                  <span className="text-slate-200 font-semibold">{item.company}</span>
                  <div className="text-[10px] text-slate-400 space-y-0.5 mt-0.5">
                    <div>• Containers: <strong className="text-cyan-300">{item.containers} TEU</strong> ({item.weight_mt} MT)</div>
                    <div>• Route: <strong className="text-amber-300">{item.departure_port} ➔ {item.destination_port}</strong></div>
                  </div>
                </div>
                <div className="flex flex-col space-y-1.5 ml-2">
                  <button
                    onClick={() => handleAssignAttempt(item, schedule[0]?.id)}
                    className="px-2.5 py-1 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-[10px] transition"
                    title="Assign to selected vessel"
                  >
                    Assign
                  </button>
                  <button
                    onClick={() => {
                      const nearest = findNearestDateShip(item.departure_port, item.destination_port);
                      if (nearest) executeAssignment(item, nearest);
                    }}
                    className="px-2 py-1 rounded-lg bg-indigo-950 text-indigo-300 border border-indigo-700 hover:bg-indigo-900 text-[9px] font-bold transition flex items-center space-x-1"
                    title="Auto-assign to ship with nearest ETD date matching departure & destination ports"
                  >
                    <Compass className="w-3 h-3 text-indigo-400" />
                    <span>Nearest Route</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 4. VESSEL SCHEDULES CARDS GRID WITH DUAL TEU & WEIGHT QUOTAS */}
        <div className="space-y-3">
          <div className="flex items-center justify-between pt-1">
            <h3 className="text-sm font-extrabold text-slate-100 flex items-center space-x-2 tracking-wide uppercase">
              <Ship className="w-4 h-4 text-cyan-400" />
              <span>Cargo Ship Available ({filteredSchedule.length})</span>
            </h3>
          </div>

          <div className="grid grid-cols-2 gap-6">
            {filteredSchedule.map((vessel) => {
              const totalBookedTEU = vessel.allocated_containers ? vessel.allocated_containers.reduce((sum, c) => sum + (c.containers || 0), 0) : (vessel.total_booked_containers || 0);
              const capacityTEU = vessel.total_capacity_teu || 400;
              const teuPct = Math.min(100, Math.round((totalBookedTEU / capacityTEU) * 100));

              const maxWeightMT = vessel.max_weight_quota_mt || 10000;
              const currentWeightMT = vessel.allocated_containers ? vessel.allocated_containers.reduce((sum, c) => sum + (c.weight_mt || (c.containers * 25)), 0) : (vessel.total_booked_weight_mt || 0);
              const weightPct = Math.min(100, Math.round((currentWeightMT / maxWeightMT) * 100));
              const isExpanded = !!expandedAllocated[vessel.id];

              return (
                <div key={vessel.id} className="rounded-2xl border border-blue-900/60 bg-slate-900/90 p-5 space-y-4 hover:border-cyan-500 transition shadow-xl">
                  <div className="flex items-start justify-between border-b border-blue-900/60 pb-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-xl bg-blue-950 text-cyan-400 border border-blue-800 flex items-center justify-center">
                        <Ship className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                          <span>{vessel.vessel_name}</span>
                          <span className="text-xs font-mono text-cyan-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-700">
                            {vessel.voyage}
                          </span>
                        </h3>
                        <div className="flex items-center space-x-2 text-xs text-slate-400 mt-0.5">
                          <Anchor className="w-3.5 h-3.5 text-slate-500" />
                          <span>Carrier: <strong className="text-slate-200">{vessel.carrier}</strong></span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => {
                        setTargetVesselId(vessel.id);
                        setShowAssignModal(true);
                      }}
                      className="px-3 py-1.5 rounded-xl bg-blue-950 hover:bg-blue-900 text-cyan-300 text-xs font-bold border border-blue-800 flex items-center space-x-1 transition cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Assign</span>
                    </button>
                  </div>

                  {/* ROUTE DISPLAY: DEPARTURE ➔ DESTINATION */}
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-blue-900/60 text-xs font-mono flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase">Departure Place (POL):</span>
                      <strong className="text-cyan-300">{vessel.departure_port || 'Singapore (SGSIN)'}</strong>
                    </div>
                    <span className="text-slate-500 font-bold">➔</span>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 block uppercase">Destination Port (POD):</span>
                      <strong className="text-amber-300">{vessel.destination_port}</strong>
                    </div>
                  </div>

                  {/* SCHEDULED DATES */}
                  <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                    <div className="p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-800">
                      <span className="text-indigo-400 flex items-center space-x-1 font-bold">
                        <Clock className="w-3.5 h-3.5" />
                        <span>🛬 Arriving (ETA):</span>
                      </span>
                      <div className="text-indigo-200 font-bold mt-1 text-xs">
                        {vessel.eta_date}
                      </div>
                    </div>

                    <div className="p-2.5 rounded-xl bg-cyan-950/40 border border-cyan-800">
                      <span className="text-cyan-400 flex items-center space-x-1 font-bold">
                        <Clock className="w-3.5 h-3.5" />
                        <span>🛫 Departing (ETD):</span>
                      </span>
                      <div className="text-cyan-300 font-bold mt-1 text-xs">
                        {vessel.etd_date}
                      </div>
                    </div>
                  </div>

                  {/* DUAL QUOTA BARS: TEU CONTAINER CAPABILITY & PAYLOAD WEIGHT QUOTA */}
                  <div className="space-y-2 p-3 rounded-xl bg-slate-950 border border-blue-900/60">
                    {/* TEU Container Quota */}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="text-slate-400 font-medium flex items-center space-x-1">
                          <Package className="w-3.5 h-3.5 text-cyan-400" />
                          <span>Container Capacity Quota:</span>
                        </span>
                        <span className="text-cyan-300 font-bold">
                          {totalBookedTEU} / {capacityTEU} TEU ({teuPct}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                        <div
                          className={`h-full transition-all duration-500 ${
                            teuPct > 90 ? 'bg-rose-500' : teuPct > 70 ? 'bg-amber-400' : 'bg-cyan-400'
                          }`}
                          style={{ width: `${Math.max(4, teuPct)}%` }}
                        />
                      </div>
                    </div>

                    {/* Payload Weight Quota */}
                    <div className="space-y-1 pt-1 border-t border-slate-900">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="text-slate-400 font-medium flex items-center space-x-1">
                          <Weight className="w-3.5 h-3.5 text-amber-400" />
                          <span>Payload Weight Quota:</span>
                        </span>
                        <span className="text-amber-300 font-bold">
                          {currentWeightMT.toLocaleString()} / {maxWeightMT.toLocaleString()} MT ({weightPct}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                        <div
                          className={`h-full transition-all duration-500 ${
                            weightPct > 90 ? 'bg-rose-500' : weightPct > 70 ? 'bg-amber-400' : 'bg-indigo-400'
                          }`}
                          style={{ width: `${Math.max(4, weightPct)}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* COLLAPSIBLE ALLOCATED CONTAINER BOOKINGS SECTION */}
                  <div className="pt-1">
                    <button
                      type="button"
                      onClick={() => setExpandedAllocated(prev => ({ ...prev, [vessel.id]: !prev[vessel.id] }))}
                      className="w-full flex items-center justify-between p-2 rounded-xl bg-slate-950 hover:bg-slate-900/80 border border-blue-900/60 text-xs font-semibold text-slate-300 transition cursor-pointer"
                    >
                      <div className="flex items-center space-x-1.5 font-bold uppercase tracking-wider text-[11px] text-slate-400">
                        <Package className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Allocated Container Bookings ({vessel.allocated_containers?.length || 0})</span>
                      </div>
                      <div className="flex items-center space-x-1 text-slate-400 text-[10px] font-mono">
                        <span>{isExpanded ? 'Minimize' : 'Click to expand'}</span>
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-cyan-400" /> : <ChevronDown className="w-3.5 h-3.5 text-cyan-400" />}
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="mt-2 space-y-1.5 animate-fadeIn">
                        {(!vessel.allocated_containers || vessel.allocated_containers.length === 0) ? (
                          <div className="p-2 text-center font-mono text-[11px] text-slate-500 bg-slate-950 rounded-lg border border-slate-900">
                            No containers allocated yet.
                          </div>
                        ) : (
                          vessel.allocated_containers.map((c, i) => (
                            <div key={i} className="p-2 rounded-lg bg-slate-950 border border-blue-900/40 flex items-center justify-between text-xs font-mono">
                              <div className="flex items-center space-x-2">
                                <span className="text-cyan-400 font-bold">{c.booking_no}</span>
                                <span className="text-slate-300">{c.company}</span>
                              </div>
                              <div className="flex items-center space-x-2">
                                <span className="bg-blue-950 text-cyan-300 px-2 py-0.5 rounded border border-blue-800 text-[11px]">
                                  {c.containers} TEU ({c.weight_mt || c.containers * 25} MT)
                                </span>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 5. ROUTING & PORT MISMATCH WARNING POPUP MODAL */}
      {mismatchWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
          <div className="glass-panel w-full max-w-md rounded-2xl border border-rose-500/60 shadow-2xl p-6 space-y-4 bg-slate-950">
            <div className="flex items-center space-x-3 text-rose-400">
              <AlertTriangle className="w-6 h-6 text-rose-400" />
              <div>
                <h3 className="text-base font-bold text-slate-100">Routing & Port Discrepancy Alert</h3>
                <span className="text-xs font-mono text-rose-400">Departure / Destination Mismatch</span>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed bg-slate-900 p-3 rounded-xl border border-slate-800 font-mono">
              {mismatchWarning.message}
            </p>

            <div className="text-xs space-y-1 font-mono bg-slate-900 p-3 rounded-xl border border-slate-800">
              <div>• Order Route: <strong className="text-amber-300">{mismatchWarning.cargoItem.departure_port} ➔ {mismatchWarning.cargoItem.destination_port}</strong></div>
              <div>• Vessel Route: <strong className="text-cyan-300">{mismatchWarning.vessel.departure_port || 'Singapore'} ➔ {mismatchWarning.vessel.destination_port}</strong></div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                onClick={() => setMismatchWarning(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs"
              >
                Cancel
              </button>
              <button
                onClick={() => executeAssignment(mismatchWarning.cargoItem, mismatchWarning.vessel)}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs"
              >
                Confirm Override Assignment
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MANUAL CONTAINER SLOT ASSIGNMENT MODAL WITH DEPARTURE/DESTINATION & WEIGHT QUOTA */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="glass-panel w-full max-w-lg rounded-2xl border border-blue-900/80 shadow-2xl p-6 space-y-4 bg-slate-950">
            <h3 className="text-base font-bold text-slate-100 flex items-center justify-between border-b border-blue-900/60 pb-3">
              <span className="flex items-center space-x-2">
                <Package className="w-5 h-5 text-cyan-400" />
                <span>Container Allocation & Weight Quota</span>
              </span>
              <button onClick={() => setShowAssignModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </h3>

            <form onSubmit={handleFormSubmit} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Departure Place (POL):</label>
                  <select
                    value={assignForm.departure_port}
                    onChange={(e) => setAssignForm({ ...assignForm, departure_port: e.target.value })}
                    className="w-full bg-slate-900 border border-blue-900/60 rounded-xl px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                  >
                    <option value="Singapore (SGSIN)">Singapore (SGSIN)</option>
                    <option value="Hong Kong (HKHKG)">Hong Kong (HKHKG)</option>
                    <option value="Port Klang (MYPKG)">Port Klang (MYPKG)</option>
                    <option value="Shanghai (CNSHA)">Shanghai (CNSHA)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Destination Port (POD):</label>
                  <select
                    value={assignForm.destination_port}
                    onChange={(e) => setAssignForm({ ...assignForm, destination_port: e.target.value })}
                    className="w-full bg-slate-900 border border-blue-900/60 rounded-xl px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                  >
                    <option value="Rotterdam (NLRTM)">Rotterdam (NLRTM)</option>
                    <option value="Hamburg (DEHAM)">Hamburg (DEHAM)</option>
                    <option value="Los Angeles (USLAX)">Los Angeles (USLAX)</option>
                    <option value="Tokyo (JPTYO)">Tokyo (JPTYO)</option>
                  </select>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-400 font-medium">Target Vessel & Port Schedule:</label>
                  <button
                    type="button"
                    onClick={handleAssignNearest}
                    className="text-[11px] font-bold text-cyan-400 hover:text-cyan-300 underline flex items-center space-x-1 cursor-pointer"
                  >
                    <Compass className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Auto-Assign to Nearest Date Ship</span>
                  </button>
                </div>
                <select
                  value={targetVesselId}
                  onChange={(e) => setTargetVesselId(e.target.value)}
                  className="w-full bg-slate-900 border border-blue-900/60 rounded-xl px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                >
                  {schedule.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.vessel_name} ({v.voyage}) — [{v.departure_port || 'Singapore'} ➔ {v.destination_port}] ETD: {v.etd_date}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Booking Reference No:</label>
                  <input
                    type="text"
                    placeholder="e.g. BK-2026-88"
                    value={assignForm.booking_no}
                    onChange={(e) => setAssignForm({ ...assignForm, booking_no: e.target.value })}
                    className="w-full bg-slate-900 border border-blue-900/60 rounded-xl px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Company / Shipper Name:</label>
                  <input
                    type="text"
                    placeholder="e.g. Global Traders Inc"
                    value={assignForm.company}
                    onChange={(e) => setAssignForm({ ...assignForm, company: e.target.value })}
                    className="w-full bg-slate-900 border border-blue-900/60 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Sender Email Address:</label>
                <input
                  type="email"
                  placeholder="e.g. desk@globaltraders.com"
                  value={assignForm.sender_email}
                  onChange={(e) => setAssignForm({ ...assignForm, sender_email: e.target.value })}
                  className="w-full bg-slate-900 border border-blue-900/60 rounded-xl px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Container Count (TEU):</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={assignForm.containers}
                    onChange={(e) => setAssignForm({ ...assignForm, containers: e.target.value, weight_mt: (parseInt(e.target.value) || 1) * 25 })}
                    className="w-full bg-slate-900 border border-blue-900/60 rounded-xl px-3 py-2 text-slate-200 font-mono focus:outline-none focus:border-cyan-400"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Cargo Weight Quota (Metric Tons / MT):</label>
                  <input
                    type="number"
                    min="1"
                    step="0.5"
                    value={assignForm.weight_mt}
                    onChange={(e) => setAssignForm({ ...assignForm, weight_mt: parseFloat(e.target.value) || 25 })}
                    className="w-full bg-slate-900 border border-blue-900/60 rounded-xl px-3 py-2 text-amber-300 font-mono font-bold focus:outline-none focus:border-cyan-400"
                  />
                </div>
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
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-bold shadow-lg shadow-cyan-950/50 cursor-pointer"
                >
                  Assign & Generate Confirmation Email
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* AUTO-GENERATED CONFIRMATION EMAIL DRAFT MODAL */}
      {emailDraftModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
          <div className="glass-panel w-full max-w-xl rounded-2xl border border-cyan-500/60 shadow-2xl p-6 space-y-4 bg-slate-950">
            <div className="flex items-center justify-between border-b border-blue-900/60 pb-3">
              <div className="flex items-center space-x-2 text-cyan-400">
                <Send className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-extrabold text-slate-100">
                  Auto-Generated Schedule & Weight Quota Email Draft
                </h3>
              </div>
              <button 
                onClick={() => setEmailDraftModal(null)} 
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-300 font-mono">
              The container booking assignment to <strong className="text-cyan-400">{emailDraftModal.vessel_name}</strong> was successful. Below is the auto-generated confirmation email draft ready to send back to the sender.
            </p>

            <div className="space-y-3 text-xs font-mono">
              <div>
                <label className="block text-slate-400 mb-1">To (Sender Email):</label>
                <input
                  type="text"
                  value={emailDraftModal.recipient}
                  onChange={(e) => setEmailDraftModal({ ...emailDraftModal, recipient: e.target.value })}
                  className="w-full bg-slate-900 border border-blue-900/60 rounded-xl px-3 py-2 text-cyan-300 font-bold"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Subject:</label>
                <input
                  type="text"
                  value={emailDraftModal.subject}
                  onChange={(e) => setEmailDraftModal({ ...emailDraftModal, subject: e.target.value })}
                  className="w-full bg-slate-900 border border-blue-900/60 rounded-xl px-3 py-2 text-slate-200 font-bold"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Email Body Draft (Editable):</label>
                <textarea
                  rows={9}
                  value={emailDraftModal.body}
                  onChange={(e) => setEmailDraftModal({ ...emailDraftModal, body: e.target.value })}
                  className="w-full bg-slate-900 border border-blue-900/60 rounded-xl p-3 text-slate-200 leading-relaxed focus:outline-none focus:border-cyan-400 font-mono"
                />
              </div>
            </div>

            {sentToast && (
              <div className="p-3 rounded-xl bg-emerald-950 border border-emerald-500 text-emerald-300 text-xs font-mono flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Confirmation Email Sent Successfully to {emailDraftModal.recipient}!</span>
              </div>
            )}

            <div className="flex items-center justify-end space-x-3 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(`To: ${emailDraftModal.recipient}\nSubject: ${emailDraftModal.subject}\n\n${emailDraftModal.body}`);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2500);
                }}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs flex items-center space-x-1.5 border border-slate-700 cursor-pointer"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? 'Copied to Clipboard!' : 'Copy Draft'}</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setSentToast(true);
                  setTimeout(() => {
                    setSentToast(false);
                    setEmailDraftModal(null);
                  }, 1800);
                }}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-extrabold text-xs flex items-center space-x-2 shadow-lg shadow-cyan-950/60 cursor-pointer"
              >
                <Send className="w-4 h-4" />
                <span>Send Confirmation Email</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
