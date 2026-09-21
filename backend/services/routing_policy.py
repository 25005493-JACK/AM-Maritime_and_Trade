"""
Bayesian Routing Policy (Thompson Sampling / Multi-Armed Bandit) (Feature B).

Per sender_domain (and optionally per field_name), maintains a Beta-Bernoulli
posterior over "should we trust the AI Agent's extraction for this sender, or
route straight to human?" — updated online from real outcomes, no training set needed.
"""
import os
import json
import random
import datetime
from typing import Dict, Any, List, Optional

from backend.services.event_logger import get_connection, event_logger
from backend.services.reflection import extract_domain

DEFAULT_ROUTING_THRESHOLD = 0.6


def _backup_policy_path() -> str:
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(workspace_root, "data", "routing_policy.json")


def _read_backup_policies() -> Dict[str, Dict[str, Any]]:
    p = _backup_policy_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}
    return {}


def _save_backup_policies(data: Dict[str, Dict[str, Any]]):
    p = _backup_policy_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    try:
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    except Exception as ex:
        print(f"[RoutingPolicy] Failed to write backup: {ex}")


def _policy_key(sender_domain: str, field_name: Optional[str] = None) -> str:
    domain = extract_domain(sender_domain)
    return f"{domain}:{field_name or '*'}"


def get_policy(sender_domain: str, field_name: Optional[str] = None) -> Dict[str, Any]:
    """Fetches the routing policy for a sender/field, or initializes uniform prior Beta(1, 1)."""
    domain = extract_domain(sender_domain)
    fn_val = field_name if field_name else "*"

    conn = get_connection()
    if conn is not None:
        try:
            row = conn.execute("""
                SELECT sender_domain, field_name, alpha, beta, last_updated
                FROM routing_policy
                WHERE sender_domain = ? AND field_name = ?
            """, [domain, fn_val]).fetchone()

            if row:
                alpha, beta = float(row[2]), float(row[3])
                return {
                    "sender_domain": row[0],
                    "field_name": None if row[1] == "*" else row[1],
                    "alpha": alpha,
                    "beta": beta,
                    "mean_trust": round(alpha / (alpha + beta), 3),
                    "outcomes_count": int(round(alpha + beta - 2.0)),
                    "last_updated": str(row[4]),
                }
        except Exception as ex:
            print(f"[RoutingPolicy] DuckDB read failed: {ex}")

    # Fallback to backup
    backups = _read_backup_policies()
    key = _policy_key(domain, field_name)
    if key in backups:
        rec = backups[key]
        alpha = float(rec.get("alpha", 1.0))
        beta = float(rec.get("beta", 1.0))
        return {
            "sender_domain": domain,
            "field_name": field_name,
            "alpha": alpha,
            "beta": beta,
            "mean_trust": round(alpha / (alpha + beta), 3),
            "outcomes_count": int(round(alpha + beta - 2.0)),
            "last_updated": rec.get("last_updated", ""),
        }

    # Initialize default uniform prior Beta(1.0, 1.0)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {
        "sender_domain": domain,
        "field_name": field_name,
        "alpha": 1.0,
        "beta": 1.0,
        "mean_trust": 0.5,
        "outcomes_count": 0,
        "last_updated": now_iso,
    }


def sample_trust(
    sender_domain: str,
    field_name: Optional[str] = None,
    threshold: float = DEFAULT_ROUTING_THRESHOLD,
    email_id: Optional[str] = None,
    shipment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Thompson Sampling: draws a sample from Beta(alpha, beta).
    If sample > threshold -> route to AI extraction.
    Else -> skip AI, route straight to Human Review Queue.
    Logs routing_decision DuckDB event.
    """
    domain = extract_domain(sender_domain)
    policy = get_policy(domain, field_name)
    alpha = policy["alpha"]
    beta = policy["beta"]
    mean_trust = alpha / (alpha + beta)

    # Thompson Sampling draw:
    sampled_trust = random.betavariate(alpha, beta)
    route_to_ai = sampled_trust > threshold

    decision = "ai" if route_to_ai else "human_first"
    reason = (
        None if route_to_ai else
        "Routing policy currently favors human-first for this sender based on recent outcomes."
    )

    result = {
        "sender_domain": domain,
        "field_name": field_name,
        "alpha": round(alpha, 2),
        "beta": round(beta, 2),
        "mean_trust": round(mean_trust, 3),
        "sampled_trust": round(sampled_trust, 3),
        "threshold": threshold,
        "route_to_ai": route_to_ai,
        "decision": decision,
        "reason": reason,
    }

    event_logger.log_routing_decision(
        sender_domain=domain,
        field_name=field_name,
        decision=decision,
        sampled_trust=round(sampled_trust, 3),
        mean_trust=round(mean_trust, 3),
        threshold=threshold,
        email_id=email_id,
        shipment_id=shipment_id
    )

    return result


def update_routing_policy(
    sender_domain: str,
    field_name: Optional[str] = None,
    ai_was_correct: bool = True,
    email_id: Optional[str] = None,
    shipment_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Online Bayesian update:
    If ai_was_correct: alpha += 1. Else: beta += 1.
    Persists updated distribution and logs routing_policy_updated event.
    """
    domain = extract_domain(sender_domain)
    policy = get_policy(domain, field_name)

    alpha = policy["alpha"] + (1.0 if ai_was_correct else 0.0)
    beta = policy["beta"] + (0.0 if ai_was_correct else 1.0)
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now_dt.isoformat()
    fn_val = field_name if field_name else "*"

    # 1. Update DuckDB
    conn = get_connection()
    if conn is not None:
        try:
            # Check if row exists
            existing = conn.execute("""
                SELECT 1 FROM routing_policy WHERE sender_domain = ? AND field_name = ?
            """, [domain, fn_val]).fetchone()

            if existing:
                conn.execute("""
                    UPDATE routing_policy
                    SET alpha = ?, beta = ?, last_updated = ?
                    WHERE sender_domain = ? AND field_name = ?
                """, [alpha, beta, now_dt, domain, fn_val])
            else:
                conn.execute("""
                    INSERT INTO routing_policy (sender_domain, field_name, alpha, beta, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, [domain, fn_val, alpha, beta, now_dt])
        except Exception as ex:
            print(f"[RoutingPolicy] DuckDB update failed: {ex}")

    # 2. Update JSON backup
    backups = _read_backup_policies()
    key = _policy_key(domain, field_name)
    backups[key] = {
        "sender_domain": domain,
        "field_name": field_name,
        "alpha": alpha,
        "beta": beta,
        "mean_trust": round(alpha / (alpha + beta), 3),
        "last_updated": now_iso,
    }
    _save_backup_policies(backups)

    # 3. Log event
    event_logger.log_routing_policy_updated(
        sender_domain=domain,
        field_name=field_name,
        alpha=alpha,
        beta=beta,
        ai_was_correct=ai_was_correct,
        email_id=email_id,
        shipment_id=shipment_id
    )

    return {
        "sender_domain": domain,
        "field_name": field_name,
        "alpha": alpha,
        "beta": beta,
        "mean_trust": round(alpha / (alpha + beta), 3),
        "outcomes_count": int(round(alpha + beta - 2.0)),
        "last_updated": now_iso,
    }


def get_all_policies() -> List[Dict[str, Any]]:
    """Returns all sender policies sorted by most interactions first."""
    rows_dict: Dict[str, Dict[str, Any]] = {}

    conn = get_connection()
    if conn is not None:
        try:
            rows = conn.execute("""
                SELECT sender_domain, field_name, alpha, beta, last_updated
                FROM routing_policy
            """).fetchall()

            for r in rows:
                dom = r[0]
                fn = None if r[1] == "*" else r[1]
                alpha = float(r[2])
                beta = float(r[3])
                k = f"{dom}:{fn or '*'}"
                rows_dict[k] = {
                    "sender_domain": dom,
                    "field_name": fn,
                    "alpha": round(alpha, 2),
                    "beta": round(beta, 2),
                    "mean_trust": round(alpha / (alpha + beta), 3),
                    "outcomes_count": int(round(alpha + beta - 2.0)),
                    "last_updated": str(r[4]),
                }
        except Exception as ex:
            print(f"[RoutingPolicy] Failed to read policies from DuckDB: {ex}")

    # Merge with backup
    backups = _read_backup_policies()
    for k, b in backups.items():
        if k not in rows_dict:
            alpha = float(b.get("alpha", 1.0))
            beta = float(b.get("beta", 1.0))
            rows_dict[k] = {
                "sender_domain": b.get("sender_domain", "unknown"),
                "field_name": b.get("field_name"),
                "alpha": round(alpha, 2),
                "beta": round(beta, 2),
                "mean_trust": round(alpha / (alpha + beta), 3),
                "outcomes_count": int(round(alpha + beta - 2.0)),
                "last_updated": b.get("last_updated", ""),
            }

    # Sort by total outcomes descending, then mean trust
    result = list(rows_dict.values())
    result.sort(key=lambda x: (-x["outcomes_count"], -x["mean_trust"], x["sender_domain"]))
    return result
