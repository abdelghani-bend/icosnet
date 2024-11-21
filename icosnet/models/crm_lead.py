from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = "crm.lead"

    lead_line_ids = fields.One2many(
        comodel_name="crm.lead.product.line", inverse_name="lead_id", string="Lead Product Lines", tracking=True
    )

    reference = fields.Char(string="Réference", compute='_compute_crm_lead_reference')
    stage = fields.Integer('Sequence', related='stage_id.sequence')
    @api.depends('partner_id')
    def _compute_crm_lead_reference(self):
       
       #temporary implementation 
       for rec in self:
            partner_id = rec.partner_id
            reference_prefix = "M" if partner_id.is_company else "P"

            if partner_id.account_category:
                reference_prefix += str(partner_id.account_category)[:2]

            rec.reference = f"{reference_prefix}{self.env['ir.sequence'].next_by_code('crm.lead.reference')}"


    def _prepare_opportunity_quotation_context(self, catalog=False, non_catalog=False, sanitize=False):

        quotation_context = super()._prepare_opportunity_quotation_context()

        if catalog:
            lines = self.lead_line_ids.filtered(lambda x : not  x.product_id.is_non_catalog)
        elif non_catalog :
            lines =  self.lead_line_ids.filtered(lambda x : x.product_id.is_non_catalog)
        else :
            lines = self.lead_line_ids
        if not lines:
              raise UserError(_('Vous devez definir au moins un produit pour cette opportunité'))
        quotation_context['default_order_line'] =  [(0, 0, {
        'name': line.name,
        'product_id': line.product_id.id,
        'product_uom_qty': line.product_qty,
        'product_uom': line.product_id.uom_id.id,
        'price_unit': line.price_unit,
        'customer_lead': 1,
        'display_type': False,
        'tax_id': [(6, 0, line.taxes_id.ids)],
                }) for line in lines]
        
        quotation_context['from_crm_lead'] = True

        technical_attribute_ids = lines.mapped('product_id.technical_attribute_ids').read(['is_required', 'name'])
        quotation_context['default_technical_attribute_ids'] =  [(0, 0, {
        'name': line['name'],
        'is_required': line['is_required']}) for line in technical_attribute_ids]
        

        if sanitize:
            quotation_context =  {key.replace('default_', ''): value for key, value in quotation_context.items() if key.startswith('default_')}


        return quotation_context

    def action_new_quotation(self):
        is_mixed = any(line.product_id.is_non_catalog for line in self.lead_line_ids) and any(not line.product_id.is_non_catalog for line in self.lead_line_ids)
        if is_mixed:
           
            contexts = [self._prepare_opportunity_quotation_context(non_catalog=True, sanitize=True),
                    self._prepare_opportunity_quotation_context(catalog=True, sanitize=True)]               

            sale_orders = self.env['sale.order'].create(contexts)
            action = {
            'type': 'ir.actions.act_window',
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            "name": _("Nouveaux devis"),
            'target': 'current',
            'domain': [('id', 'in', sale_orders.ids)]  
        }

            

            return action
            
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.sale_action_quotations_new")
            action['context'] = self._prepare_opportunity_quotation_context()
            action['context']['search_default_opportunity_id'] = self.id
            action['context']['active_test'] = True
            return action
        
    def write(self, vals):
        stage_id = self.env['crm.stage'].browse(vals.get('stage_id', False))
        if stage_id.sequence >= 2 and self.partner_id and  self.partner_id._is_crm_opportunity_convertible()!=True:
                 missing_fields = self.partner_id._is_crm_opportunity_convertible()
                 raise UserError(_("Les informations du client associé à cette opportunité ne sont pas entièrement renseignées. Veuillez compléter :  %s " % ', '.join(missing_fields)))
        super().write(vals)
    
    def action_sale_quotations_new(self):
        res = super().action_sale_quotations_new()
        
        offer_stage = self.env['crm.stage'].search([('is_offer','=',True)], limit=1)
        if offer_stage:
            self.stage_id = offer_stage
        return res
    
    @api.depends_context('uid')
    @api.depends('partner_id', 'type')
    def _compute_is_partner_visible(self):
        for lead in self:
            lead.is_partner_visible = True
class Stage(models.Model):
    _inherit = "crm.stage"


    is_offer = fields.Boolean('Est une proposition?')