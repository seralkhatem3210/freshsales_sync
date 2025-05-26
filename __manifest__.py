{
    "name": "Freshsale Sync",
    "version": "1.1",
    "category": "Tools",
    "summary": "Sync freshsale users and channels to Odoo",
    "author": "Sirelkhatim",
    "depends": ["base", "contacts"],
    "data": [
        "data/cron.xml",
        "views/freshsales_contact_views.xml",
        "security/ir.model.access.csv"
    ],
    'images': ['static/description/banner.png', 'static/description/icon.png'],
    'assets': {
        'web.assets_backend': [
            'freshsales_sync/static/src/**/*',
        ],
    },
    "installable": True,
    "application": True,
}