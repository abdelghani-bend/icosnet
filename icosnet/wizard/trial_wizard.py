# -*- coding: utf-8 -*-

from odoo import api, fields, models



class SubscriptionTrial(models.TransientModel):
    _name = 'subscription.trial'

    trial_start =  fields.Date(
        string='Début d\'essai',
        required=True
    )
    trial_end =  fields.Date(
        string='Fin d\'essai',
        required=True
    )


    def action_submit_trial(self):
       parent_subscription = self.env['sale.order'].browse(self._context['active_id']) 
       parent_subscription.write({'subscription_state':'8_trial','trial_start':self.trial_start, 'trial_end':self.trial_end})