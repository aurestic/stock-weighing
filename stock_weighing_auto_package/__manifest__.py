# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Weighing auto package",
    "summary": "Auto create package for every weighing operation",
    "version": "15.0.1.1.0",
    "development_status": "Beta",
    "category": "Warehouse",
    "website": "https://github.com/OCA/stock-weighing",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "stock_weighing",
    ],
    "data": ["wizards/weighing_wizard_views.xml"],
    "installable": True,
}
