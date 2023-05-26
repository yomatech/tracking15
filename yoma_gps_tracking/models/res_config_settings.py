# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_maps_view_api_key = fields.Char(
        string="Google Maps View Api Key",
        related="company_id.google_maps_view_api_key",
        readonly=False,
        config_parameter='web_google_maps.api_key')
    google_maps_lang_localization = fields.Selection(
        string='Google Maps Language Localization',
        related="company_id.google_maps_lang_localization",
        readonly=False,
        config_parameter='web_google_maps.lang_localization')
    google_maps_region_localization = fields.Selection(
        string='Google Maps Region Localization',
        related="company_id.google_maps_region_localization",
        readonly=False,
        config_parameter='web_google_maps.region_localization')
    google_maps_theme = fields.Selection(
        string='Google Maps theme',
        related="company_id.google_maps_theme",
        readonly=False,
        config_parameter='web_google_maps.theme')
    google_maps_libraries = fields.Char(
        string='Libraries',
        related="company_id.google_maps_libraries",
        readonly=False,
        config_parameter='web_google_maps.libraries')
    traccar_server_url = fields.Char(
        string='Traccar server URL',
        related="company_id.traccar_server_url",
        readonly=False,
        help='Enter the URL of a Traccar server, this must be a valid http address.')
    traccar_username = fields.Char(
        string='Traccar username',
        related="company_id.traccar_username",
        readonly=False,
        help='Enter the username used to connect to Traccar.')
    traccar_password = fields.Char(
        string='Traccar password',
        related="company_id.traccar_password",
        readonly=False,
        help='Enter the password of a user used to connect to Traccar.')
    contact_sequence_prefix = fields.Char(
        string="Customer Sequence Prefix",
        related="company_id.contact_sequence_prefix",
        readonly=False,)
    maximum_distance_allowed = fields.Float(
        string="Maximum Distance Allowed",
        related="company_id.maximum_distance_allowed",
        readonly=False,)
    add_to_odometer = fields.Boolean(
        string='Automatically increase vehicle odometer from GPS data',
        related="company_id.add_to_odometer",
        readonly=False,)
    inactivity_period_duration = fields.Char(
        string='Inactivity Period Duration (min)',
        help='Enter a time interval which will be a threshold for the inactivity of a vehicle (in minutes).',
        related="company_id.inactivity_period_duration",
        readonly=False)
    do_reverse_geocoding = fields.Boolean(
        string='Retrieve an address after every location change \n(reverse geocoding - beware that this consumes a lot '
               'of GMaps API calls)',
        related="company_id.do_reverse_geocoding",
        readonly=False,)
