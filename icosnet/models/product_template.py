# -*- coding: utf-8 -*-


from odoo import api, models, fields, _, exceptions
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit= 'product.template'

    piece_identite = fields.Boolean(string='Piece Identite')
    registre_commerce = fields.Boolean(string='Registre de Commerce')
    autorisation_arpce = fields.Boolean(string='Autorisation ARPCE')
    inapi = fields.Boolean(string='INAPI')
    formulaire_nd_dz = fields.Boolean(string='Formulaire ND.DZ')
    procuration_dz = fields.Boolean(string='Procuration .dz')
    formulaire_caracteristiques = fields.Boolean(string='Formulaire des Caracteristiques')
    lettre_consentement = fields.Boolean(string='Lettre de Consentement')
    procuration_sms = fields.Boolean(string='Procuration SMS')
    lettre_fixation_sender_id = fields.Boolean(string='Lettre de Fixation Sender ID')
    lettre_exploitation_fo_fms = fields.Boolean(string='Lettre d’Exploitation FO/FMS')
    capture_cnrc = fields.Boolean(string='Capture CNRC')
    carte_fiscale = fields.Boolean(string='Carte fiscale')
    conditions_vente = fields.Boolean(string='Conditions générales de vente + conditions particulières de vente')
    
    is_non_catalog = fields.Boolean(string='Produit hors catalogue?')

    service_tracking_quotation = fields.Selection(
        selection=[('no', 'Nothing'),
            ('task_global_project', 'Task'),],
        string="Create on Quotation", default="no",
        help="On Quotation creation, this product can generate a project and/or task. \
        From those, you can track the service you are selling.\n \
        'In sale order\'s project': Will use the sale order\'s configured project if defined or fallback to \
        creating a new project based on the selected template.", required=True)

    project_id_quotation =  fields.Many2one('project.project', string="Projet étude", copy=False)
    technical_attribute_ids = fields.One2many(
        comodel_name="product.technical.attribute", inverse_name="product_id", string="Fiche Technique"
    )



    pid_whmcs = fields.Char('identifiant WHMCS')
    

    

    engament_minimale = fields.Char('Engament Minimale')
    type_abonnement = fields.Selection(
    selection=[
        ('rechargement', 'Rechargement'),
        ('abonnement', 'Abonnement'),
        ('Abonnement_et_Rechargement', 'Abonnement et Rechargement'),
    ],
    string="Type Abonnement",
)

    reservation =  fields.Boolean(string='Réservation pour plusieurs années')
    nbr_annees = fields.Char("Nombre d'années") 

    @api.constrains('project_id', 'project_template_id')
    def _check_project_and_template(self):
        """ NOTE 'service_tracking' should be in decorator parameters but since ORM check constraints twice (one after setting
            stored fields, one after setting non stored field), the error is raised when company-dependent fields are not set.
            So, this constraints does cover all cases and inconsistent can still be recorded until the ORM change its behavior.
        """
        
        for product in self:
            is_task_global_project = product.service_tracking_quotation == 'task_global_project' and product.project_id
            if product.service_tracking == 'no' and (product.project_id or product.project_template_id) and not is_task_global_project:
                    raise ValidationError(_('The product %s should not have a project nor a project template since it will not generate project.', product.name))
            elif (product.service_tracking == 'task_global_project' or product.service_tracking_quotation == 'task_global_project')  and product.project_template_id:
                    raise ValidationError(_('The product %s should not have a project template since it will generate a task in a global project.', product.name))
            elif product.service_tracking in ['task_in_project', 'project_only'] and product.project_id and not is_task_global_project:
                    raise ValidationError(_('The product %s should not have a global project since it will generate a project.', product.name))


class ProductCategory(models.Model):
    _inherit = 'product.category'


    account_code = fields.Char(string="Code comptable")