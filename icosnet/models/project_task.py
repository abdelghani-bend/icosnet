# -*- coding: utf-8 -*-


from odoo import api, models, fields, _, exceptions

class Task(models.Model):
    _inherit = "project.task"

    order_partner_id = fields.Many2one('res.partner', string="Client", compute='_compute_partner_id')
    order_id = fields.Many2one('sale.order', related="sale_line_id.order_id")

    state = fields.Selection(selection_add=[
            ('5_disapproved', 'Défavorable'),
        ] , ondelete={'5_disapproved': 'set default'})

    def _compute_partner_id(self):
        for rec in self:
            rec.order_partner_id = rec.sale_line_id.order_id.partner_id
   
    def action_open_fiche_technique(self):
        self.ensure_one()
        res_id = self.env['technical.attributes.wizard'].search([('sol_id','=',self.sale_line_id.id)])
        return {
            'name': 'Fiche Technique',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'technical.attributes.wizard',
            'res_id': res_id.id,
            'target': 'current',
        }