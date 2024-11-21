# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'


 
    @api.depends('lead_id')
    def _compute_action(self):
        for convert in self:
            if not convert.lead_id:
                convert.action = 'nothing'
            else:
                partner = convert.lead_id._find_matching_partner()
                
                if partner:
                    missing_fields = partner._is_crm_opportunity_convertible()
                    if  missing_fields!=True:
                           raise UserError(_("Les informations du client associé à cette opportunité ne sont pas entièrement renseignées. Veuillez compléter :  %s " % ', '.join(missing_fields)))
                        
                    convert.action = 'exist'
                elif convert.lead_id.contact_name:
                    convert.action = 'create'
                else:
                    convert.action = 'nothing'