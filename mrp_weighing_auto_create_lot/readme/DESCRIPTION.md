Makes `auto_create_lot` (from Weighing assistant auto create lot) keep
working for MRP component consumption moves whose `picking_type_id` was
never populated.

Standard Odoo sets `picking_type_id` on `mrp.production.move_raw_ids` when
the production is created, so this normally isn't needed. It matters for
productions where that field is missing (seen in practice on data
migrated from an older Odoo version): this module falls back to the
production's own picking type instead.
