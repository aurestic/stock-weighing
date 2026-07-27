# Copyright 2026 Aures Tic
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class StockMoveWeightWizard(models.TransientModel):
    _inherit = "weighing.wizard"

    def _get_auto_create_lot_picking_type(self):
        """Standard Odoo sets picking_type_id on move_raw_ids via
        mrp.production._get_move_raw_values(), so this fallback normally
        never triggers. It matters for productions where that FK was
        never populated (seen in practice on data migrated from an older
        Odoo version): fall back to the production's own picking type,
        the natural equivalent for this kind of move."""
        picking_type = super()._get_auto_create_lot_picking_type()
        if not picking_type:
            production = self.move_id.raw_material_production_id
            if production:
                return production.picking_type_id
        return picking_type
