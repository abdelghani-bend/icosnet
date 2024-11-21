from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from markupsafe import Markup
from collections import defaultdict
import requests
import random
import string
import base64
import json
import logging
from phpserialize import *

_logger = logging.getLogger(__name__)



class SaleOrder(models.Model):
    _inherit = "sale.order"
    technical_attribute_ids = fields.One2many(
        comodel_name="product.technical.attribute", inverse_name="order_id", string="Fiche Technique"
    )

    subscription_state = fields.Selection(selection_add=[
            ('8_trial', 'Trial'),
        ],
        
    )
    trial_start =  fields.Date(
        string='Début d\'essai',
      
    )
    
    trial_end =  fields.Date(
        string='Fin d\'essai',
      
    )

    # order_line = fields.One2many(
    #     comodel_name='sale.order.line',
    #     inverse_name='order_id',
    #     string="Order Lines",
    #     copy=True, auto_join=True, tracking=True)

    validation_percent = fields.Float('Taux de validation')
    whmcs_orderid = fields.Char(string="Identifiant WHMCS")
    payment_method = fields.Selection([
        ('icosccp', 'ICOSCCP'),
        ('icosbanque', 'ICOSBanque'),
        ('icoscash', 'ICOSCash'),
    ], string='Méthode de Paiement', default='icosccp')




    @api.onchange('company_id')
    def _onchange_company_id_warning(self):
        self.show_update_pricelist = True
        if self.order_line and self.state == 'draft' and not self.env.context.get('from_crm_lead', False):
            return {
                'warning': {
                    'title': _("Warning for the change of your quotation's company"),
                    'message': _("Changing the company of an existing quotation might need some "
                                 "manual adjustments in the details of the lines. You might "
                                 "consider updating the prices."),
                }
            }
    



    @api.onchange('order_line')
    def onchange_order_line_2(self):
        data = self.order_line.mapped('product_id.technical_attribute_ids').read(['name','is_required'])
        for item in data:
            del item['id']  
        
        self.technical_attribute_ids =  [(6, 0, [])]
        self.technical_attribute_ids =  [(0, 0, d) for d in data]
    
    
    def action_confirm(self):

        if self.order_line:
            
            field_dict = {
            'piece_identite': 'Piece Identite',
            'registre_commerce': 'Registre de Commerce',
            'autorisation_arpce': 'Autorisation ARPCE',
            'inapi': 'INAPI',
            'formulaire_nd_dz': 'Formulaire ND.DZ',
            'procuration_dz': 'Procuration .dz',
            'formulaire_caracteristiques': 'Formulaire des Caracteristiques',
            'lettre_consentement': 'Lettre de Consentement',
            'procuration_sms': 'Procuration SMS',
            'lettre_fixation_sender_id': 'Lettre de Fixation Sender ID',
            'lettre_exploitation_fo_fms': "Lettre d'Exploitation FO/FMS",
            'capture_cnrc': 'Capture CNRC',
            'carte_fiscale': 'Carte fiscale',
            'conditions_vente': 'Conditions générales de vente + conditions particulières de vente'
            }
         
        
            missing_required_values = [record.name for record in self.order_line.attributes_wizard_id.technical_attribute_ids if record.is_required and not (record.value or (record.selection_value and record.selection_value!='als')  or record.date_value or record.file_value or record.res_id)]
            if missing_required_values:
                 raise UserError(_(" Veuillez compléter les champs requis dans la fiche technique. \n Champs : %s " % ', '.join(missing_required_values) ))
            for attribute in self.technical_attribute_ids:
                attribute_tuple = (attribute.name,  attribute.value, attribute.order_id)
                partner_tuples = {(attr.name, attr.value ,attr.partner_order_id) for attr in self.partner_id.technical_attribute_ids}
                if attribute_tuple[:2] not in {(t[0], t[1]) for t in partner_tuples} and\
                    attribute_tuple[2] not in [t[2] for t in partner_tuples] :

                    self.partner_id.write({
                    'technical_attribute_ids': [(0, 0, {'name': attribute.name, 'value': attribute.value, 'partner_order_id': self.id})]
                })
            products = self.order_line.mapped('product_template_id')
            all_missing_documents = set()
            for product in products:
                data = product.read(list(field_dict.keys()))[0]
                required_documents = [field_dict[key] for key, value in data.items() if value and key != 'id']
                partner_documents = set(self.partner_id.document_ids.mapped('name'))
                missing_documents = set(required_documents) - partner_documents
            all_missing_documents.update(missing_documents)
            if all_missing_documents:
                  raise UserError(_(" Veuillez compléter les documents nécessaires pour ce client en fonction du type de produits inclus dans cette commande. \n Documents : %s " % ', '.join(missing_documents) ))
        
        
        if self.partner_id and  self.partner_id._is_sale_convertible()!=True:
                 missing_fields = self.partner_id._is_sale_convertible()
                 raise UserError(_("Les informations du client associé à cette commande ne sont pas entièrement renseignées. Veuillez compléter :  %s " % ', '.join(missing_fields)))

        if not all(task.state =='03_approved' for task in self.tasks_ids):
             raise UserError(_(" Veuillez attendre l'approbation de toutes les tâches d'étude de faisabilité "))

        
        if self.opportunity_id:
            self.opportunity_id.stage_id = self.env['crm.stage'].search([('is_won','=',True)], limit=1)
        
        
        # if not self._check_client_exists_whmcs():
        #     self._add_client_whmcs()
        res = super().action_confirm()

        whmcs_products = self.order_line.filtered(lambda l: l.product_id.recurring_invoice and l.product_id.pid_whmcs).mapped('product_id').mapped('pid_whmcs')
        
        self._add_order_whmcs(whmcs_products)
        return res

    
    def _add_client_whmcs(self):
        partner = self.partner_id
        
        # custom_fields2 = [{"id":1, "value":base64.b64encode((partner.number_registre).encode()) },
        #     { "id":2, "value": base64.b64encode((partner.number_carte_fiscale).encode()) },
        #     {"id":6, "value": base64.b64encode((partner.number_nif).encode())},
        #     { "id":20, "value":   base64.b64encode(('Commercial: '+ partner + ' ' + partner.firstname).encode())}]
        custom_fields = {
            'Registre Commerce': partner.number_registre,
            'NIS': partner.number_carte_fiscale,
            'NIF': partner.number_nif,
            'Code Client': "c123456789",
            'Commercial':  partner.firstname + ' '+ partner.lastname,
            'un client existant': "Non",
            'ICRM':  partner.id,
            # 'Commercial': partner.lastname + ' ' + partner.firstname,
            'crm_integration': "true",
        }
        serialized_fields = dumps(custom_fields)

# Encode the serialized data to base64
        encoded_fields = base64.b64encode(serialized_fields).decode('utf-8')
        
        b64_custom_fields = base64.b64encode(json.dumps(custom_fields).encode())

        url = 'https://espace-client.icosnet.com.dz/includes/api.php'

        if not partner.password2:
            partner._generate_random_password(12)
        username = '5aIRfD2bqyKVjQglUR25ejtoALfdCa4u'
        password = 'Bkw8nvL72cVXW2rp6GolcLZEkoFnUC79'
        new_client = {
            'action': 'AddClient',
            'username': username,
            'password': password,
            'firstname': partner.name,
            'lastname': partner.name,
            'email': partner.email,
            'address1': partner.street,
            'city': partner.city,
            'companyname': partner.name,
            'state': partner.state_id.name,
            'postcode': partner.zip,
            'country': partner.country_id.code,
            'phonenumber': partner.phone,
            'password2': partner.password2,
            'currency': partner.currency_id.name,
            'customfields': encoded_fields,
            'noemail': True,
            'skipvalidation' : 'true',
            'responsetype': 'json'

           
        }

       
        response = requests.post(url, data=new_client)

      
        if response.status_code == 200:
            response_data = response.json()
            if response_data['result'] == 'success':
                self.partner_id.whmcs_clientid = response_data['clientid']
                print("Client added successfully:")
                _logger.info(" ||||||||| Client added successfully:")
                _logger.info(response_data)
                
            else:
                
                raise UserError(_("Failed to add client :  %s " %  response_data['message'] ))
                # print("Failed to add client:", response_data['message'])
        else:
            raise UserError(_("Failed to connect to WHMCS API: :  %s " %  response.status_code ))
            # print("Failed to connect to WHMCS API:", response.status_code)
    
    def _check_client_exists_whmcs(self):
        url = 'https://espace-client.icosnet.com.dz/includes/api.php'
        identifier = '5aIRfD2bqyKVjQglUR25ejtoALfdCa4u'
        secret = 'Bkw8nvL72cVXW2rp6GolcLZEkoFnUC79'
        
        payload = {
            'action': 'GetClients',
            'identifier': identifier,
            'secret': secret,
            'search': self.partner_id.email,  
            'responsetype': 'json'
        }
    
        
        response = requests.post(url, data=payload, verify=False)
        
        
        client_data = response.json()
    
        
        if client_data['result'] == 'success' and int(client_data['totalresults']) > 0:
            return True 
        else:
            return False  


    def _add_order_whmcs(self, pids):
        partner = self.partner_id
        api_url = 'https://espace-client.icosnet.com.dz/includes/api.php'
        username = '5aIRfD2bqyKVjQglUR25ejtoALfdCa4u'
        password = 'Bkw8nvL72cVXW2rp6GolcLZEkoFnUC79'
        params = {
            'action': 'AddOrder',
            'username': username,
            'password': password,
            'clientid': partner.whmcs_clientid,
            'pid': pids,      
            'domain': None,  
            'idnlanguage': 'fre',   
            'billingcycle': self.plan_id.name,  
            'paymentmethod': self.payment_method,
            'responsetype': 'json',     
            'noemail': 'true',          
            'noinvoiceemail': 'true',  
            
        }

     
        response = requests.post(api_url, params=params)

        if response.status_code == 200:
            client_data = response.json()
            if client_data['result'] == 'success':
                self.whmcs_orderid = client_data['orderid']
                _logger.info( " ||||||||| Order added successfully:") 
            else:
                raise UserError(_("Failed to add order :  %s " %  client_data['message'] ))

           

    
    
    
    
    def _compute_show_project_and_task_button(self):
        is_project_manager = self.env.user.has_group('project.group_project_manager')
        show_button_ids = self.env['sale.order.line']._read_group([
            ('order_id', 'in', self.ids),
            ('product_id.detailed_type', '=', 'service'),
        ], aggregates=['order_id:array_agg'])[0][0]
        for order in self:
            order.show_project_button = order.id in show_button_ids and order.project_count
            order.show_task_button = order.show_project_button or order.tasks_count
            order.show_create_project_button = is_project_manager and order.id in show_button_ids and not order.project_count and order.order_line.product_template_id.filtered(lambda x: x.service_policy in ['delivered_timesheet', 'delivered_milestones'])

    def start_trial(self):
        action = {
            'name': 'Trial Subscription',
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.trial',
            'view_mode': 'form',
            'view_id': self.env.ref('icosnet.view_subscription_trial_form').id,
            'target': 'new',
            'context': {'default_trial_end': self.trial_end},
            
        }
        return action
    
    
    
    def action_merge_orders(self):
        order_ids = self.browse(self._context['active_ids'])
        if len(order_ids) < 2:
            raise UserError(_(" Veuillez selectionner au moins deux devis"))
        if len(order_ids.mapped('partner_id'))>1:
            raise UserError(_(" Veuillez s'assurer que les devis ont le meme client"))
        if any(state=='cancel' for state in order_ids.mapped('state')):
            raise UserError(_("Pas possible de fusioner un devis annulé"))
        
        if  any(order.state != 'draft' for order in order_ids):
            raise UserError(_("Veuillez selectionner des devis seulement"))
    
        merged_order_lines = defaultdict(lambda: 0)
        order_line_data = []

        for order in order_ids:
            for line in order.order_line:
                if not line.pack_parent_line_id:
                    merged_order_lines[line.product_id.id] += line.product_uom_qty

        merged_order = self.env['sale.order'].create({
            'partner_id': order_ids[0].partner_id.id,
            'date_order': fields.Datetime.now(),
            'opportunity_id': order_ids[0].opportunity_id.id if order_ids[0].opportunity_id == order_ids[1].opportunity_id else False,
        })

        for product_id, quantity in merged_order_lines.items():
            order_line_data.append((0, 0, {
                'product_id': product_id,
                'product_uom_qty': quantity,
            }))

        
        merged_order.with_context({'do_not_expand_pack_line': True}).write({
            'order_line': order_line_data,
        })

        for order in order_ids:
            order.action_cancel() 

        # return {'type': 'ir.actions.act_window_close'}

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': merged_order.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _cron_trial_end_notification(self):
        today = datetime.today().date()
        tomorrow = today + relativedelta(days=1)
        nearly_expired_trials = self.search([('trial_end', '=', today)])
        for order in nearly_expired_trials:
            order.activity_schedule(
                'icosnet.mail_act_icosnet_trial_to_renew', order.trial_end,
                user_id=order.user_id.id)
            self.env['bus.bus']._sendone(order.user_id.partner_id, 'simple_notification', {
                    'type': 'danger',
                    'message': _("%s : Période d\'éssai s\'éxpire aujourd\'hui. Veuillez donner suite à ce devis." % order.name),
                    'sticky': True,
         })

    def write(self,vals):
        res = super().write(vals)
        if self.state == 'cancel':
            self.tasks_ids.write({'state': '1_canceled'})
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
  



    # product_id = fields.Many2one(
    #     comodel_name='product.product',
    #     string="Product",
    #     change_default=True, ondelete='restrict', check_company=True, index='btree_not_null',
    #     domain="[('sale_ok', '=', True)]", tracking=True)

    is_non_catalog = fields.Boolean(string='Produit hors catalogue?', related="product_id.is_non_catalog")
    attributes_wizard_id = fields.Many2one('technical.attributes.wizard')
    
    attributes_button_visible = fields.Boolean(compute="_compute_attributes_button_visible",store="True")
    
  
    def _timesheet_create_project_quotation(self):
        """ Generate project for the given so line, and link it.
            :param project: record of project.project in which the task should be created
            :return task: record of the created task
        """
        self.ensure_one()
        values = self._timesheet_create_project_prepare_values()
        if self.product_id.project_template_id:
            values['name'] = "%s - %s" % (values['name'], self.product_id.project_template_id.name)
            # The no_create_folder context key is used in documents_project
            project = self.product_id.project_template_id.with_context(no_create_folder=True).copy(values)
            project.tasks.write({
                'sale_line_id': self.id,
                'partner_id': self.order_id.partner_id.id,
            })
            # duplicating a project doesn't set the SO on sub-tasks
            project.tasks.filtered('parent_id').write({
                'sale_line_id': self.id,
                'sale_order_id': self.order_id.id,
            })
        else:
            project_only_sol_count = self.env['sale.order.line'].search_count([
                ('order_id', '=', self.order_id.id),
                ('product_id.service_tracking_quotation', 'in', ['project_only', 'task_in_project']),
            ])
            if project_only_sol_count == 1:
                values['name'] = "%s - [%s] %s" % (values['name'], self.product_id.default_code, self.product_id.name) if self.product_id.default_code else "%s - %s" % (values['name'], self.product_id.name)
            # The no_create_folder context key is used in documents_project
            project = self.env['project.project'].with_context(no_create_folder=True).create(values)

        # Avoid new tasks to go to 'Undefined Stage'
        if not project.type_ids:
            project.type_ids = self.env['project.task.type'].create([{
                'name': name,
                'fold': fold,
                'sequence': sequence,
            } for name, fold, sequence in [
                (_('To Do'), False, 5),
                (_('In Progress'), False, 10),
                (_('Done'), True, 15),
                (_('Canceled'), True, 20),
            ]])

        # link project as generated by current so line
        self.write({'project_id': project.id})
        return project
    
    def _timesheet_service_generation_quotation(self):
        """ For service lines, create the task or the project. If already exists, it simply links
            the existing one to the line.
            Note: If the SO was confirmed, cancelled, set to draft then confirmed, avoid creating a
            new project/task. This explains the searches on 'sale_line_id' on project/task. This also
            implied if so line of generated task has been modified, we may regenerate it.
        """
        so_line_task_global_project = self.filtered(lambda sol: sol.is_service and sol.product_id.service_tracking_quotation == 'task_global_project')
        map_sol_project = {}
        if so_line_task_global_project:
            map_sol_project = {sol.id: sol.product_id.with_company(sol.company_id).project_id_quotation for sol in so_line_task_global_project}


        # task_global_project: create task in global project
        for so_line in so_line_task_global_project:
            if not so_line.task_id:
                if map_sol_project.get(so_line.id) and so_line.product_uom_qty > 0:
                    so_line._timesheet_create_task(project=map_sol_project[so_line.id])
  
    def create(self, vals):
        

        solines = super().create(vals)
        for line in solines:
            self._new_attribute_wizard(line, line.product_id)
       
       
        # solines = solines.filtered(lambda sol: sol.is_service and sol.product_id.service_tracking_quotation == 'task_global_project')
       
        # if solines:
        #     map_sol_project = {sol.id: sol.product_id.with_company(sol.company_id).project_id for sol in solines}
        # for so_line in solines:
        #     if not so_line.task_id:
        #         if map_sol_project.get(so_line.id) and so_line.product_uom_qty > 0:
        #             so_line._timesheet_create_task(project=map_sol_project[so_line.id])

        solines.sudo()._timesheet_service_generation_quotation()
       
    def _new_attribute_wizard(self, line, product_id):
        line.attributes_wizard_id = self.env['technical.attributes.wizard'].sudo().create({ 
                        'sol_id': line.id,
                        'technical_attribute_ids' : [(0, 0, {
                        'name': attr.name,
                        'is_required': attr.is_required,
                        'is_technical': attr.is_technical,
                        'value': attr.value,
                        'type': attr.type,
                        'possible_values': attr.possible_values,
                        'model_id': attr.model_id.id
                    }) for attr in product_id.technical_attribute_ids]
                })
    def _edit_attribute_wizard(self, product_id):
        self.attributes_wizard_id.sudo().unlink()
        self._new_attribute_wizard(self, product_id)
      
    def write(self, vals):
        if 'product_id' in vals and vals['product_id'] != self.product_id.id:
            self._update_line_product(vals)
            product_id = self.env['product.product'].browse(vals['product_id'])
            self._edit_attribute_wizard(product_id)
        res = super().write(vals)
        if self.order_id:
            min_discount= min(self.order_id.order_line.mapped(lambda line: line.discount))
           
      
            discount_group_ids = [self.env.ref('icosnet.group_remise_5_pourcent').id, self.env.ref('icosnet.group_remise_15_pourcent').id, self.env.ref('icosnet.group_remise_50_pourcent').id]  
            if min_discount > 5 and min_discount < 15   and  self.env.user.has_group('icosnet.group_remise_5_pourcent') and not self.env.user.has_group('icosnet.group_remise_15_pourcent') :
                self.order_id.write({'validation_percent': min_discount}) 
          
                # if self.user_id.sale_team_id.user_id:
                #     self.env['bus.bus']._sendone(self.user_id.sale_team_id.user_id.partner_id, 'simple_notification', {
                #     'type': 'danger',
                #     'message': _("%s : Une tentative de remise superieure à 5%%,, veuillez valider!" % self.name),
                #     'sticky': True,
                #  })
                # else:
                #     partner_ids =  self.env.ref('icosnet.group_remise_15_pourcent').users.partner_id
            
                #     self.env['bus.bus']._sendmany([(partner, 'simple_notification', {
                #             'type': 'danger',
                #             'message':_("%s : Une tentative de remise superieure à 5%%,, veuillez valider!")% self.name,
                #             'sticky': True,}) for partner in partner_ids])

                # raise UserError(_("Vous n'êtes pas autorisé à appliquer des réductions supérieures à 5% sans validation."))
            elif min_discount > 15 and min_discount < 50 and self.env.user.has_group('icosnet.group_remise_15_pourcent') and not self.env.user.has_group('icosnet.group_remise_50_pourcent') :
                self.order_id.validation_percent = min_discount
                partner_ids = self.env.ref('icosnet.group_remise_50_pourcent').users.partner_id
                
                message = Markup("Une tentative de remise supérieure à 15 veuillez valider!: ") 
                self.env['bus.bus']._sendmany([(partner, 'simple_notification', {
                            'type': 'info',
                            'message':message,
                            'sticky': True,}) for partner in partner_ids])


            elif min_discount > 50 and  self.env.user.has_group('icosnet.group_remise_50_pourcent'):
                self.order_id.validation_percent = 50.0
                raise UserError(_("Le taux maximum de réduction est de 50%."))
            elif min_discount!=0 and all(group_id not in self.env.user.groups_id.ids for group_id in discount_group_ids) :
                raise UserError(_("Vous n'êtes pas autorisé à appliquer des réductions"))


        return res

    
    def unlink(self):
        for rec in self:
            rec.task_id.unlink()    
            if rec.product_id.service_tracking_quotation not in ['no', 'task_global_project']:
                rec.project_id.unlink()   
        return super().unlink()
    def _update_line_product(self, values):
        orders = self.mapped('order_id')
        for order in orders:
            msg = Markup("<br/>")
            order_lines = self.filtered(lambda x: x.order_id == order)
            for line in order_lines:
                
                msg = Markup("<b>%s</b><ul>") % _("Produit changé")
                msg += Markup("<li> %s: <br/>") % line.product_id.name
                msg += _(
                    "%(old_product)s -> %(new_product)s",
                    old_product=line.product_id.name,
                    new_product=self.env['product.product'].browse(values["product_id"]).name
                ) + Markup("<br/>")
               
            msg += Markup("</ul>")
            order.message_post(body=msg)

    @api.depends('product_id')
    def _compute_attributes_button_visible(self):
        for rec in self:
            if rec.product_id.technical_attribute_ids:
                rec.attributes_button_visible = True
            else:
                rec.attributes_button_visible = False
    
    def open_wizard_action(self):

        action = {
            'name': 'Fiche Technique: ' + self.attributes_wizard_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'technical.attributes.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('icosnet.view_attributes_wizard_form').id,
            'target': 'new',
            'res_id': self.attributes_wizard_id.id
            # 'context': {
            #         'default_technical_attribute_ids' : [(0, 0, {
            #         'name': attr.name,
            #         'is_required': attr.is_required,
            #         'value': attr.value,
        
            #     }) for attr in self.product_id.technical_attribute_ids]
            # }
        }

        # if self.attributes_wizard_id:
        #     action['res_id'] = self.attributes_wizard_id.id
         


        return action
    
    def upgrade_order(self):
        
        

        # previous_price = sum(self.mapped('order_line').filtered('product_id.recurring_invoice').mapped('price_unit'))
        previous_price = self.price_unit
        today = date.today()
        
        
        
        # if self.plan_id.billing_period_unit=='month':
        if self.order_id.plan_id.billing_period_unit=='month':
            if self.order_id.commitment_date:
               end_date =  self.order_id.commitment_date.date()+ relativedelta(months=1) 
            else:
                end_date =  self.order_id.end_date or   self.order_id.date_order.date()  + relativedelta(months=1) 
            remaining_days = (end_date - today).days
            discount = previous_price * remaining_days / 30 
        if self.order_id.plan_id.billing_period_unit=='year':
            if self.order_id.commitment_date:
                end_date = self.order_id.commitment_date.date()+ relativedelta(years=1) 
            else:
                end_date =  self.order_id.end_date or   self.order_id.date_order.date()  + relativedelta(years=1) 
           
            remaining_days = (end_date - today).days
            discount = previous_price * remaining_days / 365     
        new_order_values = {
            'partner_id': self.order_id.partner_id.id,
            'plan_id': self.order_id.plan_id.id
            
        }
        new_order = self.env['sale.order'].create(new_order_values)

        order_line_values = {
            'name': 'Prorata',
            'product_id': self.env.ref("icosnet.product_template_prorata").id,
            'product_uom_qty': 1,
            'product_uom': 1,
            'price_unit': -discount,
            'customer_lead': 1,
            'display_type': False,
            'order_id': new_order.id,
             'tax_id': [(6, 0, [])],
        }
        order_line = self.env['sale.order.line'].create(order_line_values)

        # self.locked = True
        action = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'target': 'current',
            'res_id': new_order.id,
        }

        return action

    
 
