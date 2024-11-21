from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"
    
    rc = fields.Char(string="N° Registre de commerce")
    ca = fields.Char(string="Code d'activité")
    number_article = fields.Char(string="N° Article d\'imposition")
    nif = fields.Char(string="N° identification fiscale")
    nis = fields.Char(string="N° identification statistique")
