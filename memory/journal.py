import json
import os
from typing import List, Dict, Any
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "trade_journal.json")

class ReflexionMemory:
    """Self-Learning Reflexion Engine — Logs trade outcomes and synthesizes lessons learned."""

    def __init__(self):
        self.journal: List[Dict[str, Any]] = self._load_journal()

    def _load_journal(self) -> List[Dict[str, Any]]:
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_journal(self):
        try:
            with open(MEMORY_FILE, "w") as f:
                json.dump(self.journal, f, indent=2)
        except Exception:
            pass

    def record_entry(self, symbol: str, strategy: str, confidence: float, audit_trail: Dict[str, Any]) -> str:
        """Log a new trade entry into memory."""
        entry_id = f"TRADE_{len(self.journal) + 1}_{symbol}_{int(datetime.now().timestamp())}"
        record = {
            "id": entry_id,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "strategy": strategy,
            "confidence": confidence,
            "audit_trail": audit_trail,
            "status": "OPEN",
            "pnl_dollars": 0.0,
            "lesson_learned": "Trade active in paper portfolio."
        }
        self.journal.append(record)
        self._save_journal()
        return entry_id

    def record_outcome(self, symbol: str, pnl_dollars: float, pnl_pct: float):
        """Log outcome of a trade and synthesize a post-mortem lesson."""
        for item in reversed(self.journal):
            if item["symbol"] == symbol and item["status"] == "OPEN":
                item["status"] = "CLOSED"
                item["pnl_dollars"] = pnl_dollars
                item["pnl_pct"] = pnl_pct
                
                # Synthesize lesson learned based on outcome
                if pnl_dollars > 0:
                    item["lesson_learned"] = f"WIN: {strategy_type_label(item['strategy'])} on {symbol} validated signal alignment (+${pnl_dollars:.2f}). Maintain threshold."
                else:
                    item["lesson_learned"] = f"LESSON: {strategy_type_label(item['strategy'])} on {symbol} lost -${abs(pnl_dollars):.2f}. Require higher confidence threshold (+10%) for future {symbol} setups."
                
                self._save_journal()
                return item
        return None

    def get_lessons_for_symbol(self, symbol: str) -> List[str]:
        """Retrieve historical lessons learned for a specific ticker symbol."""
        lessons = []
        for item in self.journal:
            if item["symbol"] == symbol and item.get("lesson_learned"):
                lessons.append(item["lesson_learned"])
        return lessons[-3:]  # Return top 3 recent lessons

    def get_all_lessons(self) -> List[Dict[str, Any]]:
        """Return full journal entries for Web UI display."""
        return self.journal[-10:]

def strategy_type_label(strat: str) -> str:
    return strat if strat else "SPREAD_TRADE"

reflexion_memory = ReflexionMemory()
