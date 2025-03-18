# -*- coding: utf-8 -*-
from odoo import api, models, fields, _, exceptions


class TechnicalAttributes(models.Model):
    _name = 'technical.attributes.common'
   
    name = fields.Char('Nom')
    product_ids = fields.Many2many('product.template',string="Produit")
    category_ids = fields.Many2many('product.category',string="Catégories")
    technical_attribute_ids = fields.One2many(
        comodel_name="product.technical.attribute", inverse_name="technical_attributes_common_id", string="Fiche Technique"
    )

    def create(self, vals):
        res = super().create(vals)
        res.apply_fiche()
        return res

    def write(self, vals):
        res = super().write(vals)
        self.sudo().apply_fiche()
        return res

    def apply_fiche(self):
        for rec in self:
            total_products = self.env['product.template'].search(
                [(('categ_id', 'child_of', rec.category_ids.ids))]) | rec.product_ids
            for product in total_products:
                new_lines = [(6, 0, [])] + [(0, 0, {
                    'name': attr.name,
                    'is_required': attr.is_required,
                    'type': attr.type,
                    'possible_values': attr.possible_values,
                    'model_id': attr.model_id.id,
                    'product_id': product.id,
                }) for attr in rec.technical_attribute_ids]

                product.write({'technical_attribute_ids': new_lines})

class CrmLeadProductLine(models.Model):
    _name = "product.technical.attribute"
    _inherit = ['mail.thread']
    _description = "Fiche Technique"
    _order = "is_technical asc"

    partner_order_id = fields.Many2one("sale.order", string="Partner Order", tracking=1)
    order_id = fields.Many2one("sale.order", string="Order", tracking=1)
    partner_id = fields.Many2one("res.partner", string="Partner", tracking=1)
    name = fields.Char("Nom", required=True, translate=True, tracking=1)
    product_id = fields.Many2one("product.template", string="Product", index=True, tracking=1)
    is_required = fields.Boolean(string='Requis?', tracking=1)
    is_technical = fields.Boolean(string='Technique?', tracking=1)
    technical_attributes_wizard_id = fields.Many2one("technical.attributes.wizard", tracking=1)
    technical_attributes_common_id = fields.Many2one("technical.attributes.common", tracking=1)
    type = fields.Selection([('text', 'Texte'),
                             ('date', 'Date'),
                             ('selection', 'Selection'),
                             ('table', 'Table'),
                             ('fichier', 'Fichier')],
                            string='Type', tracking=1, default='text', required=True)
    possible_values = fields.Char("Valeurs possibles", tracking=1)
    model_id = fields.Many2one('ir.model', string='Nom de l\'entité BDD', tracking=1)
    model_name = fields.Char(string='Nom de l\'entité BDD', related='model_id.model', tracking=1)
    value = fields.Char("Valeur", tracking=1)
    selection_value = fields.Char(string='Valeur Selection', tracking=1)
    date_value = fields.Date("Date", tracking=1)
    file_value = fields.Binary("Fichier", tracking=1)
    res_id = fields.Many2one('icosnet.common.config', string='Table', tracking=1, domain="[('model_name', '=', model_name)]")


    def _get_domain(self):

        domain = [
            ('model_id', '=', self.model_id),
        ]

        return domain

    def get_possible_values(self, field_name):
        self.ensure_one()
        possible_values = self.possible_values or "[]"
        return eval(possible_values)
    # def write(self,vals):
    #       pass

    # def create(self,vals):
    #       pass

    def redirect_archive_form(self):
        value = {
            'name': self.name,
            'view_mode': 'form',
            'res_model': 'product.technical.attribute',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
        return value

class CommonConfig(models.Model):
    _name = 'icosnet.common.config'

    name = fields.Char(string='Nom')
    model_id = fields.Many2one('ir.model', string='Modele')
    model_name = fields.Char(string='Nom de l\'entité BDD', related='model_id.model')
    res_id = fields.Integer(string='Id de la valeur')
