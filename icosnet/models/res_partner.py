# -*- coding: utf-8 -*-


from odoo import api, models, fields, _, exceptions
import random
import string
import requests
import base64
from odoo.exceptions import UserError
from phpserialize import *
import logging
import json


_logger = logging.getLogger(__name__)
class ResPartner(models.Model):
    _inherit = "res.partner"

   
    document_ids = fields.One2many(
        comodel_name="partner.documents", inverse_name="partner_id", string="Partner Documents"
    )


    region = fields.Selection(string="Région", selection=[('Centre', 'Centre'),
                                                         ('Est', 'Est'),
                                                         ('Ouest', 'Ouest'),
                                                         ('Sud', 'Sud'),
                                                         ])
    account_category = fields.Selection(string="Catégorie de compte", selection=[('Grand Compte', 'Grand Compte'),
                                         ('PME', 'PME'),
                                         ('SOHO', 'SOHO'),
                                         ('Partenaire', 'Partenaire'),
                                         ('Partenaire National', 'Partenaire National'),('Particulier', 'Particulier'),
                                         ('Revendeur', 'Revendeur')
                                         ])
    
    # account_category_individual = fields.Selection(string="Catégorie de compte", selection=[('Particulier', 'Particulier'),
    #                                      ('Revendeur', 'Revendeur'),
    #                                      ])
    
    activity_sector = fields.Many2one('activity.sector', string="Sécteur d\'activité")
    need_authorization = fields.Boolean(string="Nécessite autorisation?")
    # legal_status = fields.Selection(string="Statut juridique", selection=[('SARL', 'SARL'),
    #                                      ('EURL', 'EURL'),
    #                                      ('SPA', 'SPA')])
    legal_status = fields.Char(string="Statut juridique")
    nature_account = fields.Selection(string="Nature du compte", selection=[('Local', 'Local'),
                                         ('Etranger', 'Etranger')])
    
    number_registre = fields.Char(string="N° Registre de commerce")
    number_article = fields.Char(string="N° Article d\'imposition")
    number_carte_fiscale = fields.Char(string="N° Carte fiscale")
    number_nif = fields.Char(string="N° identification fiscale")
    number_nis = fields.Char(string="N° identification social")
    tva_applicable = fields.Boolean(string="Assujetti à la TVA?", default=True)
    identity_document_type = fields.Selection(string="Type piece d\'identité", selection=[('Carte d\'identité nationale', 'Carte d\'identité nationale'),
                                         ('Passeport', 'Passeport')])
    number_identity_document = fields.Char(string="N° Piece d\'identité")
    identity_document_expiration = fields.Date(string="Date d\'éxpiration")

    technical_attribute_ids = fields.One2many(
        comodel_name="product.technical.attribute", inverse_name="partner_id", string="Fiche Technique"
    )


    technical_attribute_count = fields.Integer(compute='_compute_technical_attribute_count')

    firstname = fields.Char(string="Nom" )
    lastname = fields.Char(string="Prénom")
    nom_commercial = fields.Char(string="Nom Commercial")
    id_commercial = fields.Char(string="ID Commercial")
    whmcs_clientid = fields.Char(string="Identifiant WHMCS")
    password2 = fields.Char(string="Mot de passe whmcs")
    code_crm = fields.Char(string="Code CRM")
    crm_id = fields.Char(string="ID CRM")
    code_nav = fields.Char(string="Code navision")
    code_tva = fields.Char(string="Code TVA")
    compte_parent_name = fields.Char(string="Nom du compte parent")

    city_id = fields.Many2one('res.country.city', string='City')
    entity_type = fields.Selection([('Client', 'Client'),
                                   ('Partenaire', 'Partenaire'),
                                   ('Contact', 'Contact')], required=True, string="Type d'entité")
    fax = fields.Char(string="Fax")
    second_email = fields.Char(string="Email secondaire")
    second_contact = fields.Char(string="Contact secondaire")
    contact_role = fields.Selection([('Directeur Général', 'Directeur Général'),
                                     ('Contact Technique', 'Contact Technique'),
                                     ('Contact Commercial', 'Contact Commercial'),
                                     ('Contact Financier', 'Contact Financier'),
                                     ('Contact Achat/MG', 'Contact Achat/MG'),
                                     ], required=False, string="Role")
    need_email_authorization = fields.Boolean(string="Autorisé Email ?")
    need_tel_authorization = fields.Boolean(string="Autorisé Tel ?")
    need_letter_authorization = fields.Boolean(string="Autorisé Courrier ?")
    partnership_type = fields.Selection([('Commercial', 'Commercial'),
                                         ('Commercial & Technique', 'Commercial & Technique'),
                                         ('Technique', 'Technique'),
                                         ], required=False, string="Type de partenariat")
    partner_type = fields.Selection([('Vente', 'Vente'),
                                     ('Installateur et vente', 'Installateur et vente'),
                                     ('Hébergeur', 'Hébergeur'),
                                     ('Installateur', 'Installateur'),
                                     ], required=False, string="Type de partenaire")
    sex = fields.Selection([('Homme', 'Homme'),
                            ('Femme', 'Femme')], required=False, string="Sexe")

    currency = fields.Many2one('res.currency', string="Currency")

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(ResPartner, self).fields_get(allfields, attributes)
        if 'account_category' in fields:
            fields['account_category']['selection'] = [('Grand Compte', 'Grand Compte'),
                                         ('PME', 'PME'),
                                         ('SOHO', 'SOHO'),
                                         ('Partenaire', 'Partenaire'),
                                         ('Partenaire National', 'Partenaire National'),('Particulier', 'Particulier'),
                                         ('Revendeur', 'Revendeur')
                                         ]
        return fields


    def _get_missing_fields(self, field_names):
        data = self.read(field_names.keys())
        if len(data)>0 and not all(value for value in data[0].values()):
            missing_fields = [field_names.get(key) for key, value in data[0].items() if not value]
            return missing_fields
        return []
    
    @api.model
    def _is_crm_opportunity_convertible(self):
       
        company_field_names =  {
               'account_category': "Catégorie de compte",
               'legal_status': "Statut juridique",
               'nature_account': "Nature du Compte",}

        individual_field_names ={
               'account_category': "Catégorie de compte",
               'nature_account': "Nature du Compte",
              }
        
        field_names = company_field_names if self.is_company else individual_field_names
        missing_fields = self._get_missing_fields(field_names)
        if missing_fields:
            return missing_fields
        return True
    
    
    

    def _is_sale_convertible(self):
        missing_fields = [] if self._is_crm_opportunity_convertible() else self._is_crm_opportunity_convertible()
        company_field_names =  {
               'number_registre': "N° Registre de commerce",
               'number_article': "N° Article d\'imposition",
               'number_carte_fiscale': "N° Carte fiscale",
               'number_nif': "N° identification fiscale",
               'tva_applicable': "Assujetti à la TVA?",
               'nom_commercial': "Nom du Commercial",
               }
        

        individual_field_names ={
               'identity_document_type': "Type piece d\'identité",
               'nature_account': "N° Piece d\'identité",
               'identity_document_expiration': "Date d\'éxpiration",
               'nom_commercial': "Nom du Commercial",
              
              }
        
        field_names = company_field_names if self.is_company else individual_field_names
        missing_fields += self._get_missing_fields(field_names)
        if missing_fields:
            return missing_fields
        return True

    
    def _generate_random_password(self, length=12):
            
            characters = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(random.choice(characters) for _ in range(length))
            self.password2 = password
            return password
    
    @api.model_create_multi
    def create(self,vals):
        
        
       
        
        for val in vals:
            if 'password2' not in val or not val['password2']:
                val['password2'] = self._generate_random_password(12)
            if self._context.get('active_model',False) == 'crm.lead' or 'is_company' not in val:
                val['is_company'] = True
    
   
        res = super().create(vals)
        if not res._check_client_exists_whmcs():
            res._add_client_whmcs()
        return res


    def action_see_fiches_techniques(self):
        action = self.env.ref('icosnet.action_fiches_techniques').read()[0]
        action['domain'] = [('partner_id', '=', self.id)] 
        return action
    
    def _compute_technical_attribute_count(self):
        for rec in self:
            rec.technical_attribute_count = self.env['technical.attributes.wizard'].search_count([('partner_id','=',self.id),('state','!=','cancelled')])



    def _check_client_exists_whmcs(self):
        url = 'https://espace-client.icosnet.com.dz/includes/api.php'
        username = '5aIRfD2bqyKVjQglUR25ejtoALfdCa4u'
        password = 'Bkw8nvL72cVXW2rp6GolcLZEkoFnUC79'
        payload = {
            'action': 'GetClientsDetails',
            'username': username,
            'password': password,
            'email': self.email,
            'clientid': self.whmcs_clientid,
            'responsetype': 'json'
        }
        response = requests.post(url, data=payload)
      
        client_data = response.json()
        if client_data['result'] == 'success':
            return True
        else:
            return False


    def _add_client_whmcs(self):
        partner = self
        
       
        custom_fields = {
            'Registre Commerce': partner.number_registre,
            'NIS': partner.number_carte_fiscale,
            'NIF': partner.number_nif,
            # 'Code Client': "c123456789",
            'Commercial':   partner.nom_commercial,
            'un client existant': "Oui",
            'wilaya' : partner.state_id.name,
            'ICRM':  partner.id,
            
            # 'Commercial': 'Aucun Commerciale',
            'crm_integration': "true",
        }
        serialized_fields = dumps(custom_fields)


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
            'firstname': partner.name.split()[0],
            'lastname': ' '.join(partner.name.split()[1:]) if len(partner.name.split()) > 1 else '',
            'email': partner.email,
            'address1': partner.street,
            'address2': partner.street2,
            'city': partner.city_id.name,
            'companyname': partner.name,
            'state': partner.state_id.name,
            'postcode': partner.zip,
            'country': partner.country_id.code,
            'phonenumber': partner.phone,
            'password2': partner.password2,
            'currency': partner.currency.name,
            'customfields': encoded_fields,
            'noemail': True,
            'skipvalidation' : 'true',
            'responsetype': 'json'

           
        }

       
        response = requests.post(url, data=new_client)

      
        if response.status_code == 200:
            response_data = response.json()
            if response_data['result'] == 'success':
                self.whmcs_clientid = response_data['clientid']
                print("Client added successfully:")
                _logger.info(" ||||||||| Client added successfully:")
                _logger.info(response_data)
                _logger.info(partner.state_id.name)
                
            else:
                
                raise UserError(_("Failed to add client :  %s " %  response_data['message'] ))
                # print("Failed to add client:", response_data['message'])
        else:
            raise UserError(_("Failed to connect to WHMCS API: :  %s " %  response.status_code ))
            # print("Failed to connect to WHMCS API:", response.status_code)
    def _update_client_whmcs(self):
        partner = self

        custom_fields = {
            'Registre Commerce': partner.number_registre,
            'NIS': partner.number_carte_fiscale,
            'NIF': partner.number_nif,
            # 'Code Client': "c123456789",
            'Commercial':   partner.nom_commercial,
            'un client existant': "Oui",
            'ICRM':  partner.id,
            'wilaya' : partner.state_id.name,
            'crm_integration': "true",
        }
        serialized_fields = dumps(custom_fields)


        encoded_fields = base64.b64encode(serialized_fields).decode('utf-8')

        url = 'https://espace-client.icosnet.com.dz/includes/api.php'
        username = '5aIRfD2bqyKVjQglUR25ejtoALfdCa4u'
        password = 'Bkw8nvL72cVXW2rp6GolcLZEkoFnUC79' #todo sortir le mot de passe

        update_client_payload = {
            'action': 'UpdateClient',
            'username': username,
            'password': password,
            'clientid': partner.whmcs_clientid, 
            'firstname': partner.name.split()[0],
            'lastname': partner.name.split()[1] if len(partner.name.split())>1 else '',
            'email': partner.email,
            'address1': partner.street,
            'address2': partner.street2,
            'city': partner.city_id.name,
            'companyname': partner.name,
            'state': partner.state_id.name,
            'postcode': partner.zip,
            'country': partner.country_id.code,
            'phonenumber': partner.phone,
            'customfields': encoded_fields,
            'responsetype': 'json'
        }

        response = requests.post(url, data=update_client_payload)

        if response.status_code == 200:
            response_data = response.json()
            if response_data['result'] == 'success':
                _logger.info(" ||||||||| Client updated successfully:")
                _logger.info(update_client_payload)
                _logger.info(partner.state_id.name)
            else:
                _logger.info(update_client_payload)
                raise UserError(_("Failed to update client :  %s " % response_data['message']))
        else:
            raise UserError(_("Failed to connect to WHMCS API: : %s " % response.status_code))


    def write(self, vals):
        
        needs_whmcs_update = [record for record in self if record._check_client_exists_whmcs()]
        
       
        res = super().write(vals)

        for record in needs_whmcs_update:
            record._update_client_whmcs()
        
        return res
    
class PartnerDocuments(models.Model):
    _name = "activity.sector"

    name = fields.Char(string="Nom")


class PartnerDocuments(models.Model):
    _name = "partner.documents"

    name = fields.Char("name", compute='_compute_name')
    partner_id = fields.Many2one("res.partner")
    document_type_individual = fields.Selection([('Piece Identite', 'Piece Identite'),
                                       ('Registre de Commerce', 'Registre de Commerce'),
                                       ('Autorisation ARPCE', 'Autorisation ARPCE'),
                                       ('INAPI', 'INAPI'),
                                       ('Formulaire ND.DZ', 'Formulaire ND.DZ'),
                                       ('Procuration .dz', 'Procuration .dz'),
                                       ('Formulaire des Caractéristiques', 'Formulaire des Caractéristiques'),
                                       ('Lettre de Consentement', 'Lettre de Consentement'),
                                       ('Procuration SMS', 'Procuration SMS'),
                                       ('Lettre de fixation Sender ID', 'Lettre de fixation Sender ID'),
                                       ('Lettre d’Exploitation FO/FMS', 'Lettre d’Exploitation FO/FMS'),
                                       ('Capture CNRC', 'Capture CNRC')])
    document_type_company = fields.Selection([
                                        ('Piece Identite', 'Piece Identite'),
                                       ('Registre de Commerce', 'Registre de Commerce'),
                                       ('Autorisation ARPCE', 'Autorisation ARPCE'),
                                       ('INAPI', 'INAPI'),
                                       ('Formulaire ND.DZ', 'Formulaire ND.DZ'),
                                       ('Procuration .dz', 'Procuration .dz'),
                                       ('Formulaire des Caractéristiques', 'Formulaire des Caractéristiques'),
                                       ('Lettre de Consentement', 'Lettre de Consentement'),
                                       ('Procuration SMS', 'Procuration SMS'),
                                       ('Lettre de fixation Sender ID', 'Lettre de fixation Sender ID'),
                                       ('Lettre d’Exploitation FO/FMS', 'Lettre d’Exploitation FO/FMS'),
                                       ('Capture CNRC', 'Capture CNRC'),
                                       ('Carte fiscale', 'Carte fiscale'),
                                       ('Conditions générales de vente + conditions particulières de vente', 'Conditions générales de vente + conditions particulières de vente'),
                                       ])
    
    file_data = fields.Binary(string="Fichier")
    related_documents_document =  fields.Many2one("documents.document")



    @api.constrains('partner_id', 'document_type')
    def _check_unique_document_type(self):
        for record in self:
            existing_records = self.search([
                ('partner_id', '=', record.partner_id.id),
                ('document_type_company', '=', record.document_type_company),
                ('document_type_individual', '=', record.document_type_individual),
                ('id', '!=', record.id),  
            ])
            if existing_records:
                raise exceptions.ValidationError("One document type allowed per partner. Please choose a different document type.")

    @api.depends('document_type_individual', 'document_type_company' )
    def _compute_name(self):
        for rec in self:
            rec.name = rec.document_type_individual if rec.document_type_individual else rec.document_type_company


    def create(self, vals):
        for record in vals:
                document_values ={
                        'name':vals[vals.index(record)].get('document_type_individual') or vals[vals.index(record)].get('document_type_company'),
                        'datas': record['file_data'],
                        'folder_id': self.env.ref("documents.documents_internal_folder").id,
                        'partner_id': record['partner_id']
                    }

                document_record = self.env['documents.document'].create(document_values)
                vals[vals.index(record)]['related_documents_document'] = document_record.id
                self.env.cr.commit()
        return  super().create(vals)
        
    

    
    
    
    
    
    def write(self, vals):
        document_values = {}
        if 'document_type_individual' in vals:
            document_values['name'] = vals['document_type_individual']
        if 'document_type_company' in vals:
            document_values['name'] = vals['document_type_company']
        if 'file_data' in vals:
            document_values['datas'] = vals['file_data']
        self.related_documents_document.write
