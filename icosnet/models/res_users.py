# -*- coding: utf-8 -*-


from odoo import api, models, fields, _, exceptions


class ResUsers(models.Model):
    _inherit = "res.users"


    @api.model_create_multi
    def create(self, vals_list):
        
        res = super().create(vals_list)
        if not res.has_group('sales_team.group_sale_manager'):

            group = self.env.ref('base.group_allow_export', False)
            group.write({'users': [(3, res.id)]})
            
        return res
    
    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if not rec.has_group('sales_team.group_sale_manager'):

                group = self.env.ref('base.group_allow_export', False)
                group.write({'users': [(3, rec.id)]})
        return res  