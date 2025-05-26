# models/freshsales_config.py
import requests
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import dateutil.parser


_logger = logging.getLogger(__name__)

class FreshsalesConfig(models.Model):
    _name = 'freshsales.config'
    _description = 'Freshsales API Config'

    name = fields.Char()
    api_key = fields.Char(required=True)
    bundle_alias = fields.Char(required=True)  # e.g. wesalit.myfreshworks.com/crm/sales

    def action_sync_contacts(self):
        self.ensure_one()

        headers = {
            "Authorization": f"Token token={self.api_key}",
            "Content-Type": "application/json"
        }

        # 1. Get view ID for 'All Contacts'
        filters_url = f"https://{self.bundle_alias}/api/contacts/filters"
        filters_resp = requests.get(filters_url, headers=headers)
        if filters_resp.status_code != 200:
            raise UserError(_("❌ Failed to retrieve views: %s") % filters_resp.text)
        filters = filters_resp.json().get("filters", [])
        view_id = next((f["id"] for f in filters if f["name"] == "All Contacts"), None)
        if not view_id:
            raise UserError(_("❌ 'All Contacts' view not found."))

        # 2. Fetch contacts
        total_synced = 0
        page = 1
        while True:
            url = f"https://{self.bundle_alias}/api/contacts/view/{view_id}?page={page}&per_page=25"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise UserError(_("❌ Failed to fetch contacts: %s") % response.text)

            data = response.json()
            contacts = data.get("contacts", [])
            if not contacts:
                break

            for c in contacts:
                # raw_time = c.get('last_contacted')
                
                raw_time = c.get('last_contacted')
                try:
                    parsed_time = dateutil.parser.parse(raw_time).astimezone().replace(tzinfo=None) if raw_time else False
                except Exception:
                    parsed_time = False

                existing = self.env['freshsales.contact'].search([('contact_id', '=', str(c['id']))], limit=1)
                freshsale_id = str(c['id'])

                # Step 1: Use customer_type as a tag
                custom_fields = c.get('custom_field', {})
                customer_type = custom_fields.get('cf_customer_type')

                # customer_type = c.get('cf_customer_type')  # or c.get('customer_type') if not custom
                category_ids = []

                if customer_type:
                    customer_type = customer_type.strip()
                    category = self.env['res.partner.category'].search([('name', '=', customer_type)], limit=1)

                    if not category:
                        category = self.env['res.partner.category'].create({'name': customer_type})
                        _logger.info("✅ Created new tag: %s", customer_type)

                    category_ids = [category.id]

                # Step 3: Include tag in partner_vals
                partner_vals = {
                    'name': f"{c.get('first_name', '')} {c.get('last_name', '')}".strip(),
                    'email': c.get('email'),
                    'phone': c.get('mobile_number'),
                    'city': c.get('city'),
                    'country_id': self.env['res.country'].search([('name', '=', c.get('country'))], limit=1).id if c.get('country') else False,
                    'freshsale_id': freshsale_id,
                    'type': 'contact',
                    'category_id': [(6, 0, category_ids)] if category_ids else False,  # Assign the tag only if it exists
                }

  
                # Find or create res.partner
                partner = self.env['res.partner'].search([('freshsale_id', '=', freshsale_id)], limit=1)
                if partner:
                    partner.write(partner_vals)
                else:
                    partner = self.env['res.partner'].create(partner_vals)

                values = {
                    'first_name': c.get('first_name'),
                    'last_name': c.get('last_name'),
                    'email': c.get('email'),
                    'mobile_number': c.get('mobile_number'),
                    'city': c.get('city'),
                    'country': c.get('country'),
                    'last_contacted': parsed_time,
                    'customer_type': customer_type, #cf_customer_type
                    # 'last_contacted': Datetime.from_string(raw_time) if raw_time else False,
                    # 'last_contacted': c.get('last_contacted'),
                }
                if existing:
                    existing.write(values)
                else:
                    values['contact_id'] = str(c['id'])
                    self.env['freshsales.contact'].create(values)
                total_synced += 1

            page += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Freshsales'),
                'message': _('✅ %d contact(s) synced.') % total_synced,
                'type': 'success',
            }
        }

    @api.model
    def cron_sync_freshsales_contacts(self):
        configs = self.search([])
        for config in configs:
            try:
                config.action_sync_contacts()
            except Exception as e:
                _logger.error("❌ Cron Sync Error (Freshsales): %s", e)
