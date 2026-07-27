# Copyright 2026 Aures Tic
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import Form, TransactionCase


class TestMrpWeighingAutoCreateLot(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manufacture_route = cls.env.ref("mrp.route_warehouse0_manufacture")
        cls.warehouse = cls.env["stock.warehouse"].search([], limit=1)
        cls.manufacturing_picking_type = cls.warehouse.manu_type_id
        cls.manufacturing_picking_type.auto_create_lot = True

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
        return production

    def test_raw_material_move_has_no_picking_type(self):
        """Confirms the real-world gap this module fixes: component
        consumption moves never carry their own picking_type_id."""
        production = self._create_production()
        self.assertFalse(production.move_raw_ids.picking_type_id)

    def test_auto_create_lot_falls_back_to_production_picking_type(self):
        production = self._create_production()
        move = production.move_raw_ids
        wizard = self.env["weighing.wizard"].create({"move_id": move.id})
        self.assertEqual(
            wizard._get_auto_create_lot_picking_type(),
            production.picking_type_id,
        )
        self.assertTrue(wizard._get_auto_create_lot_picking_type().auto_create_lot)
