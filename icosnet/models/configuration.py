from odoo import api, models, fields, _, exceptions


class Pop(models.Model):
    _name = 'icosnet.pop'

    
    name = fields.Char(string='Code')
    designation = fields.Char(string='Désignation')
    pop_de_rattachement = fields.Char(string='POP de rattachement')
    origine = fields.Char(string='Origine')
    type = fields.Char(string='Type')
    capacite = fields.Char(string='Capacité')
    adresse = fields.Char(string='Adresse')
    position_gps = fields.Char(string='Position GPS')
    region = fields.Char(string='Région')
    pays = fields.Char(string='Pays')
    latitude = fields.Char(string='Latitude')
    longitude = fields.Char(string='Longitude')
    elevation = fields.Char(string='Élévation')
    extremite_at_icosnet_pop_source = fields.Char(string='Extrémité AT icosnet POP source')
    extremite_at_icosnet_pop_final = fields.Char(string='Extrémité AT icosnet POP final')
    ipv4_prive = fields.Char(string='IPv4 privé')
    ipv6 = fields.Char(string='IPv6')
    ipv4_publique = fields.Char(string='IPv4 publique')
    equipement = fields.Char(string='Équipement')
    architecture = fields.Char(string='Architecture')
    fiche_de_mise_en_service = fields.Char(string='Fiche de mise en service')
    fiche_de_resiliation = fields.Char(string='Fiche de résiliation')

    @api.model
    def create(self, vals):
        res = super(Pop, self).create(vals)
        model_id = self.env['ir.model'].search([('model', '=', 'icosnet.pop')])
        common_value = self.env['icosnet.common.config'].create({'name': res.name,
                                                                 'model_id': model_id.id,
                                                                 'res_id': res.id})
        return res

    def unlink(self):
        self.ensure_one()
        model_id = self.env['ir.model'].search([('model', '=', 'icosnet.pop')])
        common_value = self.env['icosnet.common.config'].search([('model_id', '=', model_id.id),
                                                                 ('res_id', '=', self.id)])
        common_value.unlink()
        res = super(Pop, self).unlink()
        return res


class PopEquipment(models.Model):
    _name = 'icosnet.pop.equipement'

    name = fields.Char(string='Code')
    designation = fields.Char(string='Désignation')
    type = fields.Char(string='Type')
    pop = fields.Char(string='POP')
    adresse_ip = fields.Char(string='Adresse IP')

    @api.model
    def create(self, vals):
        res = super(PopEquipment, self).create(vals)
        model_id = self.env['ir.model'].search([('model', '=', 'icosnet.pop.equipement')])
        common_value = self.env['icosnet.common.config'].create({'name': res.name,
                                                                 'model_id': model_id.id,
                                                                 'res_id': res.id})
        return res

    def unlink(self):
        self.ensure_one()
        model_id = self.env['ir.model'].search([('model', '=', 'icosnet.pop.equipement')])
        common_value = self.env['icosnet.common.config'].search([('model_id', '=', model_id.id),
                                                                 ('res_id', '=', self.id)])
        common_value.unlink()
        res = super(PopEquipment, self).unlink()
        return res

