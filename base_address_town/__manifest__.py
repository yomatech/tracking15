# -*- coding: utf-8 -*-

{
    'name': 'Township',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Selectable Township in Contact Address',
    'author': 'Yoma Technologies (Darshan)',
    'description': """
Selectable Township in Contact Address. Suitable for Odoo 13, 15. Not tested on 14. 
    """,
    'depends': ['base',
                'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/res_country_state.xml',
        'views/res_city.xml',
        'views/res_town.xml',
        'data/res.country.state.csv',
        'data/res.city.csv',
        'data/res.town.csv',
        'data/res_country_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
