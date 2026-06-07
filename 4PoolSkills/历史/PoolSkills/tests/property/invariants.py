INVARIANTS = [
  'tenant_id in request must match authenticated tenant context',
  'role escalation fields cannot be mass assigned by non-admin roles',
  'amount, price, credit, coupon and refund transitions must be server-side recomputed',
  'state machine transitions must reject skipped or reversed states',
  'async job result retrieval must bind job owner and tenant',
]
