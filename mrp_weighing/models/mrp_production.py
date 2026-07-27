# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import ast

from odoo import _, api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    weighing_operations = fields.Boolean(related="picking_type_id.weighing_operations")
    has_weighing_operations = fields.Boolean(compute="_compute_has_weighing_operations")

    @api.depends("move_raw_ids")
    def _compute_has_weighing_operations(self):
        for mrp_production in self:
            mrp_production.has_weighing_operations = mrp_production.move_raw_ids

    def action_weighing_operations(self):
        """Weighing operations for this production order.

        Uses move_raw_ids (components to consume), not move_finished_ids
        (the manufactured output): this button is for weighing what goes
        INTO the production, matching the rest of this module (the weighing
        wizard extension and _close_production() below both operate on
        move_raw_ids already).
        """
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_weighing.weighing_operation_action"
        )
        weight_moves = self.move_raw_ids
        action["name"] = _("Weighing operations for %(name)s", name=self.name)
        action["domain"] = [("id", "in", weight_moves.ids)]
        ctx = dict(
            self.env.context,
            **ast.literal_eval(action["context"]),
            group_by=["production_id"],
            show_weight_detail_buttons=True,
        )
        # We weigh mrp operations that are not in ready state
        ctx.pop("search_default_ready")
        action["context"] = ctx
        return action
