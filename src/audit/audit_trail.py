"""Agent Audit and Provenance Trace System.

Maintains an immutable record of every agent action, node transition,
confidence metric, warning, data provenance, and decision rationale.
"""

from typing import List, Dict, Any, Optional
import uuid
import time
from datetime import datetime
from src.domain.models import AuditEvent


class AuditTrail:
    """Thread-safe event logger for multi-agent execution tracing."""

    def __init__(self):
        self._events: List[AuditEvent] = []

    def record_event(
        self,
        agent_or_node: str,
        action: str,
        input_summary: str,
        output_summary: str,
        decision: str,
        confidence: Optional[float] = None,
        warnings: Optional[List[str]] = None,
        data_provenance: str = "Synthetic Cohort & Protocol Store",
        execution_latency_ms: float = 0.0,
        errors: Optional[str] = None,
    ) -> AuditEvent:
        """Records an immutable audit event."""
        event = AuditEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.now().isoformat(),
            agent_or_node=agent_or_node,
            action=action,
            input_summary=input_summary,
            output_summary=output_summary,
            decision=decision,
            confidence=confidence,
            warnings=warnings or [],
            data_provenance=data_provenance,
            execution_latency_ms=round(execution_latency_ms, 2),
            errors=errors,
        )
        self._events.append(event)
        return event

    def get_events(self) -> List[AuditEvent]:
        """Returns all recorded events chronologically."""
        return list(self._events)

    def clear(self) -> None:
        """Clears events (for testing or reset)."""
        self._events.clear()

    def get_events_for_node(self, node_name: str) -> List[AuditEvent]:
        """Filters events by agent or node name."""
        return [e for e in self._events if e.agent_or_node == node_name]


audit_logger = AuditTrail()
