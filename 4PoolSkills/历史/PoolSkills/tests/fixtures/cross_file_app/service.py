def dangerous_lookup(item_id, tenantId):
    # local fixture only: demonstrates source-to-sink static graph; not a live exploit.
    return db.queryRaw('select * from items where id = ' + item_id)
