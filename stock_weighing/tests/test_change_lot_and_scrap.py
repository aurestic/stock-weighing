# Copyright 2026 Aures Tic
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestChangeLotAndScrap(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Weighed Product With Lots",
                "type": "consu",
                "is_storable": True,
                "tracking": "lot",
                "uom_id": cls.env.ref("uom.product_uom_kgm").id,
            }
        )
        cls.lot_a = cls.env["stock.lot"].create(
            {"name": "LOT-A", "product_id": cls.product.id}
        )
        cls.lot_b = cls.env["stock.lot"].create(
            {"name": "LOT-B", "product_id": cls.product.id}
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.stock_location, 20.0, lot_id=cls.lot_a
        )

    def _create_move(self):
        move = self.env["stock.move"].create(
            {
                "name": "Test move",
                "product_id": self.product.id,
                "product_uom_qty": 10.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        move._action_confirm()
        move._action_assign()
        return move

    def test_change_lot_creates_audit_log_and_updates_line(self):
        move = self._create_move()
        line = move.move_line_ids
        self.assertEqual(line.lot_id, self.lot_a)

        action = line.action_open_change_lot_wizard()
        self.assertEqual(action["context"]["default_move_line_id"], line.id)

        wizard = self.env["weighing.change.lot.wizard"].create(
            {
                "move_line_id": line.id,
                "new_lot_id": self.lot_b.id,
                "reason": "Lote equivocado al asignar",
            }
        )
        wizard.action_change_lot()

        self.assertEqual(line.lot_id, self.lot_b)
        log = self.env["stock.move.line.lot.change"].search(
            [("move_line_id", "=", line.id)]
        )
        self.assertEqual(len(log), 1)
        self.assertEqual(log.old_lot_id, self.lot_a)
        self.assertEqual(log.new_lot_id, self.lot_b)
        self.assertEqual(log.reason, "Lote equivocado al asignar")

    def test_change_lot_to_the_same_lot_is_rejected(self):
        move = self._create_move()
        line = move.move_line_ids
        wizard = self.env["weighing.change.lot.wizard"].create(
            {
                "move_line_id": line.id,
                "new_lot_id": self.lot_a.id,
                "reason": "no-op",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_change_lot()

    def test_action_scrap_from_weighing_prefills_from_the_line(self):
        move = self._create_move()
        line = move.move_line_ids
        line.qty_picked = 4.5
        action = line.action_scrap_from_weighing()
        ctx = action["context"]
        self.assertEqual(ctx["default_product_id"], self.product.id)
        self.assertEqual(ctx["default_lot_id"], self.lot_a.id)
        self.assertEqual(ctx["default_location_id"], self.stock_location.id)
        self.assertEqual(ctx["default_scrap_qty"], 4.5)
        self.assertEqual(action["res_model"], "stock.scrap")
        self.assertEqual(action["target"], "new")
