Makes `auto_create_lot` (from Weighing assistant auto create lot) work for
MRP component consumption moves too, not just regular picking transfers.

Component consumption moves (`mrp.production.move_raw_ids`) never carry
their own `picking_type_id`, so the base check against the picking type's
`auto_create_lot` flag never matches for them. This module falls back to
the production's own picking type instead.
