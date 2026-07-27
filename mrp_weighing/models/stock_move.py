# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

# Real mrp.workorder operation names for the "weighing" step in ENTRA's
# routings (Pesadas / Aprovisionamiento Lineas), matching either the exact
# name or "<name> - ..." -- same rule mesboard's operationNamesDomain()
# uses, so this stays consistent with how the boards group workorders.
WEIGHING_OPERATION_NAMES = ("PESADA", "APROVISIONAMIENTO LINEAS")


def _is_weighing_workorder(workorder):
    name = (workorder.name or "").upper()
    return any(
        name == op_name or name.startswith(f"{op_name} - ")
        for op_name in WEIGHING_OPERATION_NAMES
    )


class StockMove(models.Model):
    _inherit = "stock.move"

    is_has_production = fields.Boolean(compute="_compute_is_has_production")

    @api.depends("move_line_ids", "move_orig_ids")
    def _compute_is_has_production(self):
        self.is_has_production = False
        for move in self:
            move.is_has_production = bool(
                move.created_production_id or move.move_orig_ids.mapped("production_id")
            )

    def _has_weigh_domain(self):
        # Components measured in Units (packaging, caps, boxes...) never
        # show up on the weighing screen otherwise, even when they still
        # need to be picked for a manufacturing order.
        domain = super()._has_weigh_domain()
        unit_category = self.env.ref(
            "uom.product_uom_categ_unit", raise_if_not_found=False
        )
        if not unit_category:
            return domain
        return expression.OR(
            [
                domain,
                [
                    ("raw_material_production_id", "!=", False),
                    ("product_uom_category_id", "=", unit_category.id),
                ],
            ]
        )

    def action_finish_weighing_workorder(self):
        """Finish the Pesadas/Aprovisionamiento workorder of THIS move's own
        manufacturing order, once it is fully weighed. Scoped to a single
        order/movement on purpose: it must never sweep everything pending
        at the workcenter."""
        self.ensure_one()
        production = self.raw_material_production_id
        if not production:
            raise UserError(_("This movement isn't linked to a manufacturing order."))
        if production.state == "cancel":
            # Seen in migrated data: a workorder left "ready" on a
            # production that is itself cancelled -- nothing to finish.
            raise UserError(_("This manufacturing order is cancelled."))
        workorders = production.workorder_ids.filtered(
            lambda wo: wo.state not in ("done", "cancel") and _is_weighing_workorder(wo)
        )
        if not workorders:
            raise UserError(
                _("There's no pending weighing/provisioning operation for this order.")
            )
        pending_lines = production.move_raw_ids.move_line_ids.filtered(
            lambda line: line.move_id.state not in ("done", "cancel")
            and not line.picked
        )
        if pending_lines:
            raise UserError(
                _(
                    "%(count)s line(s) of this order are not fully weighed yet.",
                    count=len(pending_lines),
                )
            )
        workorders.button_finish()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": _("Manufacturing order finished."),
                "type": "success",
            },
        }

    @api.model
    def action_mrp_production_weighing(self):
        """Used in the start screen"""
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_production_action")
        action["views"] = [[False, "kanban"], [False, "list"], [False, "form"]]
        ctx = {"search_default_todo": True}
        action["context"] = ctx
        return action

    def action_add_move_line(self):
        action = super().action_add_move_line()
        if not self.production_id.lot_producing_id:
            production_id = self.move_orig_ids.production_id
            if (
                production_id
                and self.product_id == production_id.product_id
                and production_id.state == "done"
            ):
                raise ValidationError(_("You can not add weight, the MO is done."))
            return action
        default_lot_id = False
        if self.product_id == self.production_id.product_id:
            default_lot_id = self.production_id.lot_producing_id.id
        else:
            last_lot = self.move_line_ids.lot_id[-1:]
            if last_lot:
                default_lot_id = last_lot.id
            elif self.has_tracking:
                lot = self.env["stock.lot"].search(
                    [
                        ("company_id", "=", self.company_id.id),
                        ("product_id", "=", self.product_id.id),
                        ("name", "=", self.production_id.lot_producing_id.name),
                    ],
                    limit=1,
                )
                if lot:
                    default_lot_id = lot.id
                else:
                    sml = self.move_line_ids[:1]
                    if not sml:
                        sml = self.env["stock.move.line"].new(
                            {
                                "lot_name": self.production_id.lot_producing_id.name,
                                "product_id": self.product_id.id,
                                "company_id": self.company_id.id,
                            }
                        )
                    sml._create_and_assign_production_lot()
                    default_lot_id = sml.lot_id.id
        if default_lot_id:
            action["context"].update({"default_lot_id": default_lot_id})
        return action
