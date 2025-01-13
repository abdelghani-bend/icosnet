# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TechnicalAttributes(models.Model):
    _name = 'technical.attributes.wizard'
    sol_id = fields.Many2one('sale.order.line', string="Ligne de Commande")
    order_id = fields.Many2one('sale.order', related="sol_id.order_id",string="Devis/Commande", store=True)
    partner_id = fields.Many2one('res.partner', related="order_id.partner_id",string="Client", store=True)
    product_id = fields.Many2one('product.product', related="sol_id.product_id",string="Produit", store=True)
    name = fields.Char('Identifiant', compute="_compute_identifiant", store="True")
    technical_attribute_ids = fields.One2many(
        comodel_name="product.technical.attribute", inverse_name="technical_attributes_wizard_id", string="Fiche Technique",
    )

    state = fields.Selection([
        ('active', 'Active'),
        ('cancelled', 'Annulé')
    ], string='Statut', compute='_compute_state', store=True)


    

    @api.depends('sol_id')
    def _compute_identifiant(self):
        def _get_root_category(product):
            
                root_category = product.categ_id
                while root_category.parent_id:
                    root_category = root_category.parent_id
                return root_category
        for rec in self:
            sol = rec.sol_id
            root_category = _get_root_category(sol.product_id)
            account_name = root_category.name
            # name = sol.order_id.partner_id.name.replace(' ','-') if sol else 'Fiche expiré'
            seq =   self.env['ir.sequence'].next_by_code('seq.fiche.technique')
 
            rec.name =  account_name+"-"+seq if account_name else seq

    def action_submit_attributes(self):
        self.env.cr.commit()
        # sol = self.env['sale.order.line'].browse(self._context['active_id'])
        # if not sol.attributes_wizard_id: 
        #     sol.write({'attributes_wizard_id': self.id})
       
    def button_open_order(self):
       
        self.ensure_one()
        return {
            'name': "Devis/Commande",
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': self.order_id.id,
        }


    @api.depends('order_id.state')
    def _compute_state(self):
        for record in self:
            if record.order_id.state == 'cancel':
                record.state = 'cancelled'
            else:
                record.state = 'active'



