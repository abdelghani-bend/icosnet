# Copyright 2019 NaN (http://www.nan-tic.com) - Àngel Àlvarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Product Pack",
    "version": "17.0.1.1.0",
    "category": "Product",
    "summary": "This module allows you to set a product as a Pack",
    "website": "https://github.com/OCA/product-pack",
    "author": "NaN·tic, ADHOC SA, Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["ernestotejeda"],
    "license": "AGPL-3",
    "depends": ["product"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_pack_line_views.xml",
        "views/product_template_views.xml",
        "views/product_product_views.xml",
    ],
    "demo": ["demo/product_product_demo.xml", "demo/product_pack_line_demo.xml"],
    "installable": True,
    "auto_install": False,
    "application": False,
}
