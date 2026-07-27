# Copyright 2026 Aures Tic
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models


class StockMoveWeightWizard(models.TransientModel):
    _inherit = "weighing.wizard"

    def _get_auto_create_lot_picking_type(self):
        """MRP component consumption moves (move_raw_ids) never carry their
        own picking_type_id, so the base check against move_id.picking_type_id
        never matches for them. Fall back to the production's own picking
        type, which is the natural equivalent for this kind of move."""
        picking_type = super()._get_auto_create_lot_picking_type()
        if not picking_type:
            production = self.move_id.raw_material_production_id
            if production:
                return production.picking_type_id
        return picking_type
