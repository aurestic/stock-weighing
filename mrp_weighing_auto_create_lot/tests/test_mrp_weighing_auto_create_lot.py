# Copyright 2026 Aures Tic
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import Form, TransactionCase


class TestMrpWeighingAutoCreateLot(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manufacture_route = cls.env.ref("mrp.route_warehouse0_manufacture")

        cls.component = cls.env["product.product"].create(
            {
                "name": "Test Component AutoLot",
                "type": "consu",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "tracking": "lot",
                "is_storable": True,
                "auto_create_lot": True,
            }
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.component, cls.env.ref("stock.stock_location_stock"), 100
        )
        cls.finished = cls.env["product.product"].create(
            {
                "name": "Test Finished AutoLot",
                "type": "consu",
                "is_storable": True,
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "route_ids": [(6, 0, [cls.manufacture_route.id])],
            }
        )
        cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "product_uom_id": cls.env.ref("uom.product_uom_unit").id,
                "type": "normal",
                "bom_line_ids": [
                    (0, 0, {"product_id": cls.component.id, "product_qty": 1})
                ],
            }
        )

    def _create_production(self):
        production_form = Form(self.env["mrp.production"])
        production_form.product_id = self.finished
        production_form.product_qty = 1
        production = production_form.save()
        production.action_confirm()
        # Set on the production's own picking type, whichever warehouse it
        # ended up using -- guessing it in advance is fragile in a
        # multi-warehouse database.
        production.picking_type_id.auto_create_lot = True
        return production

    def test_auto_create_lot_prefers_the_moves_own_picking_type(self):
        """Standard Odoo sets move_raw_ids.picking_type_id via
        _get_move_raw_values(): for a normally-created production this
        module changes nothing, the move's own value wins."""
        production = self._create_production()
        move = production.move_raw_ids
        self.assertTrue(move.picking_type_id)
        wizard = self.env["weighing.wizard"].create({"move_id": move.id})
        resolved = wizard._get_auto_create_lot_picking_type()
        self.assertEqual(resolved, move.picking_type_id)
        self.assertTrue(resolved.auto_create_lot)

    def test_auto_create_lot_falls_back_to_production_picking_type(self):
        """Some productions (seen in practice on data migrated from an
        older Odoo version, where this FK was never populated) have
        move_raw_ids with no picking_type_id of their own. This module's
        fallback is what makes auto_create_lot still work for those."""
        production = self._create_production()
        move = production.move_raw_ids
        move.picking_type_id = False
        wizard = self.env["weighing.wizard"].create({"move_id": move.id})
        self.assertEqual(
            wizard._get_auto_create_lot_picking_type(),
            production.picking_type_id,
        )
        self.assertTrue(wizard._get_auto_create_lot_picking_type().auto_create_lot)
