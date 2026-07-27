# Copyright 2026 Aures Tic
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, fields, models
from odoo.exceptions import UserError


class WeighingChangeLotWizard(models.TransientModel):
    _name = "weighing.change.lot.wizard"
    _description = "Change the lot of an already weighed line, with a reason"

    move_line_id = fields.Many2one(
        comodel_name="stock.move.line", required=True, readonly=True
    )
    product_id = fields.Many2one(related="move_line_id.product_id", readonly=True)
    old_lot_id = fields.Many2one(related="move_line_id.lot_id", readonly=True)
    new_lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="New lot",
        required=True,
        domain="[('product_id', '=', product_id)]",
    )
    reason = fields.Char(required=True)

    def action_change_lot(self):
        self.ensure_one()
        if self.new_lot_id == self.old_lot_id:
            raise UserError(_("Select a different lot than the current one."))
        self.env["stock.move.line.lot.change"].create(
            {
                "move_line_id": self.move_line_id.id,
                "old_lot_id": self.old_lot_id.id,
                "new_lot_id": self.new_lot_id.id,
                "reason": self.reason,
            }
        )
        self.move_line_id.lot_id = self.new_lot_id
        return {"type": "ir.actions.act_window_close"}
