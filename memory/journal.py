import json
import os
from typing import List, Dict, Any
from datetime import datetime

_JOURNAL_FILE = os.path.join(os.path.dirname(__file__), "trade_journal.json")


class ReflexionMemory:
    """Persists trade history and extracts lessons for the AI committee."""

    def __init__(self):
        self.journal: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if os.path.exists(_JOURNAL_FILE):
            try:
                with open(_JOURNAL_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        try:
            with open(_JOURNAL_FILE, "w") as f:
                json.dump(self.journal, f, indent=2)
        except Exception:
            pass

    def record_entry(self, symbol: str, strategy: str, confidence: float) -> str:
        entry_id = f"T{len(self.journal)+1}_{symbol}_{int(datetime.now().timestamp())}"
        self.journal.append({
            "id": entry_id,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "strategy": strategy,
            "confidence": confidence,
            "status": "OPEN",
            "pnl_dollars": 0.0,
            "lesson_learned": "Trade active in portfolio.",
        })
        self._save()
        return entry_id

    def record_outcome(self, symbol: str, pnl_dollars: float, pnl_pct: float):
        for item in reversed(self.journal):
            if item["symbol"] == symbol and item["status"] == "OPEN":
                item["status"] = "CLOSED"
                item["pnl_dollars"] = round(pnl_dollars, 2)
                item["pnl_pct"] = round(pnl_pct, 2)
                if pnl_dollars > 0:
                    item["lesson_learned"] = f"WIN +${pnl_dollars:.2f} ({pnl_pct:.1f}%). Signal confirmed valid."
                else:
                    item["lesson_learned"] = f"LOSS -${abs(pnl_dollars):.2f} ({pnl_pct:.1f}%). Require stronger catalyst next time."
                self._save()
                return item
        return None

    def get_lessons_for_symbol(self, symbol: str) -> List[str]:
        return [
            item["lesson_learned"]
            for item in self.journal
            if item["symbol"] == symbol and item.get("lesson_learned")
        ][-3:]

    def get_all_entries(self) -> List[Dict[str, Any]]:
        return self.journal[-10:]


reflexion_memory = ReflexionMemory()
