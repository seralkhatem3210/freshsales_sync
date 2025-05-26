import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError


# models/freshsales_contact.py
from odoo import models, fields

class FreshsalesContact(models.Model):
    _name = 'freshsales.contact'
    _description = 'Freshsales Contact'

    contact_id = fields.Char(string="Freshsales ID", readonly=True, index=True)
    first_name = fields.Char()
    last_name = fields.Char()
    email = fields.Char()
    mobile_number = fields.Char()
    city = fields.Char()
    country = fields.Char()
    customer_type = fields.Char()
    last_contacted = fields.Datetime()
