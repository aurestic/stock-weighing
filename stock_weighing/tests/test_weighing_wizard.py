# Copyright 2026 Aures Tic
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import TransactionCase


class TestWeighingWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Weighed Product",
                "type": "consu",
                "is_storable": True,
                "uom_id": cls.env.ref("uom.product_uom_kgm").id,
            }
        )
        cls.quant = cls.env["stock.quant"].create(
            {
                "product_id": cls.product.id,
                "quantity": 20,
                "location_id": cls.stock_location.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.quant.action_apply_inventory()

    def _create_move(self, qty=10.0):
        move = self.env["stock.move"].create(
            {
                "name": "Test move",
                "product_id": self.product.id,
                "product_uom_qty": qty,
                "product_uom": self.product.uom_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        move._action_confirm()
        move._action_assign()
        return move

    def test_record_weight_sets_picked_and_quantity(self):
        """A move line weighed directly (no enclosing picking, e.g. a bare
        MRP component move) must end up with `quantity` synced to the
        weighed amount and `picked` set, or stock._action_done() silently
        leaves the move as-is instead of validating what was weighed."""
        move = self._create_move(qty=10.0)
        line = move.move_line_ids
        self.assertEqual(line.quantity, 10.0)
        self.assertFalse(line.picked)
        wizard = self.env["weighing.wizard"].create(
            {
                "move_id": move.id,
                "selected_move_line_id": line.id,
                "weight": 4.5,
            }
        )
        wizard.record_weight()
        self.assertEqual(line.quantity, 4.5)
        self.assertTrue(line.picked)
        move._action_done()
        self.assertEqual(move.state, "done")
        self.assertEqual(move.move_line_ids.quantity, 4.5)

    def test_record_weight_reset_unpicks_the_line(self):
        move = self._create_move(qty=10.0)
        line = move.move_line_ids
        wizard = self.env["weighing.wizard"].create(
            {
                "move_id": move.id,
                "selected_move_line_id": line.id,
                "weight": 4.5,
            }
        )
        wizard.record_weight()
        self.assertTrue(line.picked)
        wizard.weight = 0.0
        wizard.record_weight()
        self.assertFalse(line.has_recorded_weight)
        self.assertFalse(line.picked)
