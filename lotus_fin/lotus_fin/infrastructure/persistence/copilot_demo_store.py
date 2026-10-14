"""Transactional, isolated simulation state; never a business ledger."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from lotus_fin.domain.model.l4_operation_record import L4ActionProposal, L4OperationRecord
from lotus_fin.infrastructure.persistence.l4_mutation_adapters import (
    InMemoryL4OperationLedger, IsolatedTestLotusActionWritePort,
)


class CopilotDemoStore:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def transaction(self, scope, event):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=10)
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS state (scope TEXT PRIMARY KEY, body TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, scope TEXT, event TEXT)")
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT body FROM state WHERE scope=?", (scope,)).fetchone()
            data = json.loads(row[0]) if row else {}
            ledger = InMemoryL4OperationLedger()
            ledger._proposals = {k: L4ActionProposal.model_validate_json(json.dumps(v))
                                 for k, v in data.get("proposals", {}).items()}
            ledger._operations = {k: L4OperationRecord.model_validate_json(json.dumps(v))
                                  for k, v in data.get("operations", {}).items()}
            ledger._proposal_to_operation = data.get("mapping", {})
            ledger._consumed_challenges = set(data.get("consumed", []))
            adapter = IsolatedTestLotusActionWritePort()
            adapter._store = data.get("records", {})
            # Audit must succeed before admitting a simulation operation.
            conn.execute("INSERT INTO audit(scope,event) VALUES (?,?)", (scope, event))
            yield ledger, adapter
            snapshot = {
                "proposals": {k: v.model_dump(mode="json") for k, v in ledger._proposals.items()},
                "operations": {k: v.model_dump(mode="json") for k, v in ledger._operations.items()},
                "mapping": ledger._proposal_to_operation,
                "consumed": sorted(ledger._consumed_challenges), "records": adapter._store,
            }
            conn.execute("INSERT OR REPLACE INTO state(scope,body) VALUES (?,?)",
                         (scope, json.dumps(snapshot, ensure_ascii=False)))
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()
