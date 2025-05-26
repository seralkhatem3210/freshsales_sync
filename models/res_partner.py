from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    freshsale_id = fields.Char(string="Freshsale ID", index=True)
