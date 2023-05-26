# -*- coding: utf-8 -*-

{
    'name': 'Map GPS Tracking',
    'description': 'Tracking on Map',
    "version": "1.0",
    'summary': 'GPS Tracking for your fleet',
    'author': "Yoma Technologies",
    'category': 'Extra Tools',
    'description': """
Traccar GPS tracking integration with the Fleet Management module.

==========================

Track your vehicles with the free and open source Traccar solution.
""",
    'depends': [
        'web_google_maps',
        'account',
        'fleet',
        'base',
        'contacts',
        'base_address_town',
        'snailmail_account'
    ],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'report/customer_qr_report.xml',
        'report/template.xml',
        'data/ir_cron_data.xml',
        'data/ir_sequence_data.xml',
        'views/fleet_vehicle_view.xml',
        'views/res_partner_visit_logs_views.xml',
        'views/res_config_settings.xml',
        'views/res_partner_views.xml',
        'views/fleet_vehicle_location_history_views.xml',
        'views/fleet_vehicle_day_trip_views.xml',
        'views/fleet_trip_view.xml',
        'views/fleet_route_view.xml',
        'views/res_partner_visit_logs_views.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            '/yoma_gps_tracking/static/src/xml/web_map.xml'
        ],
        'web.assets_backend': [
            'yoma_gps_tracking/static/src/css/web_map.css',
            'yoma_gps_tracking/static/src/js/web_map.js',
            'yoma_gps_tracking/static/src/js/calendar_prevent_create.js'
        ]
    },

    'demo': [],
    'installable': True,
    'application': True,
    'price': 149,
    'currency': 'EUR',
    'images': ['static/description/banner.jpg'],
}
