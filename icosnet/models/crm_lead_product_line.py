from odoo import api, fields, models


class CrmLeadProductLine(models.Model):
    _name = "crm.lead.product.line"
    _description = "Product Line in CRM Lead"


    lead_id = fields.Many2one("crm.lead", string="Lead")
    name = fields.Char("Description", required=True, translate=True, tracking=True)
    product_id = fields.Many2one("product.product", string="Product", index=True, tracking=True)
    product_qty = fields.Integer(string="Product Quantity", default=1, required=True, tracking=True)
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", readonly=True)
    price_unit = fields.Monetary(string="Price Unit")
    currency_id = fields.Many2one('res.currency', related="product_id.company_id.currency_id", readonly=True)
    taxes_id = fields.Many2many('account.tax', 'product_taxes_rel2', 'prod_id', 'tax_id', help="Default taxes used when selling the product.", string='Customer Taxes',
        domain=[('type_tax_use', '=', 'sale')],
        default=lambda self: self.env.companies.account_sale_tax_id or self.env.companies.root_id.account_sale_tax_id,
    )
    is_non_catalog = fields.Boolean(string='Produit hors catalogue?', related="product_id.is_non_catalog")
    
    @api.onchange("product_id")
    def _onchange_product_id(self):
        domain = {}
        if not self.lead_id:
            return

        if not self.product_id:
            self.price_unit = 0.0
            domain["uom_id"] = []
        else:
            product = self.product_id
            self.price_unit = product.list_price

            if product.name:
                self.name = product.name

            if (
                not self.uom_id
                or product.uom_id.category_id.id != self.uom_id.category_id.id
            ):
                self.uom_id = product.uom_id.id
            domain["uom_id"] = [("category_id", "=", product.uom_id.category_id.id)]

            if self.uom_id and self.uom_id.id != product.uom_id.id:
                self.price_unit = product.uom_id._compute_price(
                    self.price_unit, self.uom_id
                )
            if product.taxes_id:
                self.taxes_id = [(6, 0, product.taxes_id.ids)]

        return {"domain": domain}

   

    @api.onchange("uom_id")
    def _onchange_uom_id(self):
        result = {}
        if not self.uom_id:
            self.price_unit = 0.0

        if self.product_id and self.uom_id:
            price_unit = self.product_id.list_price
            self.price_unit = self.product_id.uom_id._compute_price(
                price_unit, self.uom_id
            )

        return result
    
