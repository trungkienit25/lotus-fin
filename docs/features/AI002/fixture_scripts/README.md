# AI002-00B local fixture scripts

**Technical reproduction guide only.** The current AI002 product/architecture/gate authority is [AI002 Master SSOT v1](../AI002_MASTER_SSOT_V1.md); the current machine oracle is [gold manifest](../AI002_GOLD_FIXTURE_MANIFEST.yaml). Older narrative in this README describes the 00B ERP transaction fixture and does not define current product decisions.

The 00C [direct commitment JSON](direct_confirmed_commitments.json) is an explicit **test-author declaration only**, not an ERPNext transaction, actual SME commitment or production source. [build_gold.py](build_gold.py) calculates both 30-day oracle cases with Decimal and no AI002 production engine import.

These scripts were run only against approved local Docker site `frontend` on 2026-09-26. They create **synthetic test data** via ERPNext document insert/submit APIs, not direct GL/AR/AP seeds. Run in this order: `setup.py`, `transactions.py`, `payments.py`, then read-only `verify.py`. `security_rollback.py` creates temporary least-privilege users/permissions and rolls them back; run it through `exec(open(path).read(), globals())` so its probe functions retain their imports. `logging_canary.py` uses fake sentinel values only. Do not run setup/transaction scripts against production or another company without adapting and reviewing them. Existing fixture voucher IDs and independent expected results are in [gold manifest](../AI002_GOLD_FIXTURE_MANIFEST.yaml).

The scripts are evidence/reproduction aids, not the AI002 forecast engine or a migration. Company and invoice/payment creation have existence checks; do not assume a partially failed rerun is safe without checking the ERPNext state. The fixture remains in the local test site. The security test users are rolled back.
