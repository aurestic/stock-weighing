# Copyright 2026 Aures Tic
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class StockMoveLineLotChange(models.Model):
    _name = "stock.move.line.lot.change"
    _description = "Audit trail of lot changes made from the weighing screen"
    _order = "create_date desc"

    move_line_id = fields.Many2one(
        comodel_name="stock.move.line", required=True, ondelete="cascade", index=True
    )
    old_lot_id = fields.Many2one(comodel_name="stock.lot", string="Previous lot")
    new_lot_id = fields.Many2one(
        comodel_name="stock.lot", string="New lot", required=True
    )
    reason = fields.Char(required=True)
    user_id = fields.Many2one(
        comodel_name="res.users", default=lambda self: self.env.user, required=True
    )
