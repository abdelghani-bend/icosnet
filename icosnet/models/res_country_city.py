# -*- coding: utf-8 -*-


from odoo import models, fields

class City(models.Model):
    _name = 'res.country.city'
   

    name = fields.Char(string='Nom', required=True)
    state_id = fields.Many2one('res.country.state', string='Region')
    zip = fields.Char(string='Code Postal')