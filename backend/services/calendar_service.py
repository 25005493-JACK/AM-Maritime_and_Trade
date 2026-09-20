import datetime
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

class CalendarService:
    def __init__(self):
        self.google_sync_path = Path(__file__).resolve().parents[1] / "data" / "calendar_google_sync.json"
        self.google_calendar_links = self._load_google_calendar_links()

        # Initial seed vessel schedule data
        self.schedule = [
            {
                "id": "VESSEL-001",
                "vessel_name": "MSC ISABELLA",
                "voyage": "v.240E",
                "carrier": "MSC",
                "destination_port": "Rotterdam (NLRTM)",
                "port_code": "NLRTM",
                "eta_date": "2026-09-22",
                "etd_date": "2026-09-24",
                "total_capacity_teu": 400,
                "allocated_containers": [
                    {"booking_no": "BK-99214", "company": "Global Traders Inc", "containers": 3, "status": "Confirmed"},
                    {"booking_no": "BK-99215", "company": "Euro Retail BV", "containers": 12, "status": "Confirmed"}
                ]
            },
            {
                "id": "VESSEL-002",
                "vessel_name": "EVERSMART",
                "voyage": "v.012W",
                "carrier": "Evergreen",
                "destination_port": "Hamburg (DEHAM)",
                "port_code": "DEHAM",
                "eta_date": "2026-09-25",
                "etd_date": "2026-09-27",
                "total_capacity_teu": 350,
                "allocated_containers": [
                    {"booking_no": "PL-5541", "company": "Pacific Logistics Ltd", "containers": 2, "status": "Confirmed"}
                ]
            },
            {
                "id": "VESSEL-003",
                "vessel_name": "MAERSK MC-KINNEY",
                "voyage": "v.401S",
                "carrier": "Maersk",
                "destination_port": "Los Angeles (USLAX)",
                "port_code": "USLAX",
                "eta_date": "2026-09-28",
                "etd_date": "2026-09-30",
                "total_capacity_teu": 500,
                "allocated_containers": [
                    {"booking_no": "APEX-1049", "company": "Asia Pacific Exports", "containers": 5, "status": "Confirmed"}
                ]
            },
            {
                "id": "VESSEL-004",
                "vessel_name": "CMA CGM ANTOINE",
                "voyage": "v.991N",
                "carrier": "CMA CGM",
                "destination_port": "Tokyo (JPTYO)",
                "port_code": "JPTYO",
                "eta_date": "2026-09-23",
                "etd_date": "2026-09-25",
                "total_capacity_teu": 300,
                "allocated_containers": [
                    {"booking_no": "BK-4410", "company": "Fast Freight GmbH", "containers": 1, "status": "Confirmed"}
                ]
            },
            {
                "id": "VESSEL-005",
                "vessel_name": "OOCL HONG KONG",
                "voyage": "v.108E",
                "carrier": "OOCL",
                "destination_port": "Hong Kong (HKHKG)",
                "port_code": "HKHKG",
                "eta_date": "2026-09-29",
                "etd_date": "2026-10-01",
                "total_capacity_teu": 450,
                "allocated_containers": [
                    {"booking_no": "TW-3029", "company": "Transworld Shipping", "containers": 2, "status": "Confirmed"}
                ]
            }
        ]

        # Auto-extracted booking requests pending calendar confirmation
        self.pending_auto_bookings = [
            {
                "email_id": "MSG-006",
                "booking_no": "AUTO-BK-8891",
                "company": "Oceanic Trade Corp",
                "requested_containers": 8,
                "destination_port": "Rotterdam (NLRTM)",
                "suggested_vessel_id": "VESSEL-001",
                "suggested_vessel_name": "MSC ISABELLA v.240E",
                "status": "Pending Calendar Confirmation"
            }
        ]

    def get_calendar(self, destination_port: Optional[str] = None) -> List[Dict[str, Any]]:
        result = []
        for vessel in self.schedule:
            # Strict port filter evaluation
            if destination_port and destination_port != "ALL":
                p_lower = destination_port.lower()
                v_dest = vessel["destination_port"].lower()
                v_code = vessel["port_code"].lower()
                if p_lower not in v_dest and p_lower not in v_code and v_code not in p_lower:
                    continue

            total_booked = sum(c["containers"] for c in vessel["allocated_containers"])
            utilization_pct = round((total_booked / vessel["total_capacity_teu"]) * 100, 1)

            result.append({
                **vessel,
                "total_booked_containers": total_booked,
                "utilization_pct": utilization_pct,
                "google_calendar": self.google_calendar_links.get(vessel["id"])
            })
        return result

    def _load_google_calendar_links(self) -> Dict[str, Dict[str, Any]]:
        if not self.google_sync_path.exists():
            return {}
        try:
            with self.google_sync_path.open("r", encoding="utf-8") as sync_file:
                value = json.load(sync_file)
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_google_calendar_links(self) -> None:
        self.google_sync_path.parent.mkdir(parents=True, exist_ok=True)
        with self.google_sync_path.open("w", encoding="utf-8") as sync_file:
            json.dump(self.google_calendar_links, sync_file, indent=2)

    def create_google_calendar_link(self, vessel_id: str) -> Dict[str, Any]:
        vessel = next((item for item in self.schedule if item["id"] == vessel_id), None)
        if not vessel:
            return {"status": "error", "message": "Vessel not found"}

        existing = self.google_calendar_links.get(vessel_id)
        if existing:
            return {"status": "already_linked", "vessel_id": vessel_id, **existing}

        eta = datetime.datetime.strptime(vessel["eta_date"], "%Y-%m-%d").date()
        etd = datetime.datetime.strptime(vessel["etd_date"], "%Y-%m-%d").date()
        google_end = etd + datetime.timedelta(days=1)
        details = "\n".join([
            f"Carrier: {vessel['carrier']}",
            f"Destination: {vessel['destination_port']}",
            f"ETA: {vessel['eta_date']}",
            f"ETD: {vessel['etd_date']}",
            f"Vessel schedule ID: {vessel['id']}"
        ])
        params = urlencode({
            "action": "TEMPLATE",
            "text": f"{vessel['vessel_name']} {vessel['voyage']} - Port Call",
            "dates": f"{eta.strftime('%Y%m%d')}/{google_end.strftime('%Y%m%d')}",
            "details": details,
            "location": vessel["destination_port"],
            "trp": "false"
        })
        record = {
            "status": "LINK_CREATED",
            "event_url": f"https://calendar.google.com/calendar/render?{params}",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "vessel_id": vessel_id
        }
        self.google_calendar_links[vessel_id] = record
        self._save_google_calendar_links()
        return {"status": "success", **record}

    def assign_container(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        vessel_id = payload.get("vessel_id")
        booking_no = payload.get("booking_no", f"BK-{datetime.datetime.now().strftime('%M%S')}")
        company = payload.get("company", "Operations Manual Assignment")
        containers = int(payload.get("containers", 1))

        for vessel in self.schedule:
            if vessel["id"] == vessel_id:
                # Add or update allocation
                existing = next((c for c in vessel["allocated_containers"] if c["booking_no"] == booking_no), None)
                if existing:
                    existing["containers"] = containers
                else:
                    vessel["allocated_containers"].append({
                        "booking_no": booking_no,
                        "company": company,
                        "containers": containers,
                        "status": "Manual Assignment"
                    })
                return {"status": "success", "message": f"Assigned {containers} containers to {vessel['vessel_name']}"}

        return {"status": "error", "message": "Vessel not found"}

    def confirm_auto_booking(self, email_id: str) -> Dict[str, Any]:
        pending = next((b for b in self.pending_auto_bookings if b["email_id"] == email_id), None)
        if not pending:
            return {"status": "error", "message": "Pending booking not found"}

        res = self.assign_container({
            "vessel_id": pending["suggested_vessel_id"],
            "booking_no": pending["booking_no"],
            "company": pending["company"],
            "containers": pending["requested_containers"]
        })

        pending["status"] = "Confirmed & Scheduled"
        return res

calendar_service = CalendarService()
