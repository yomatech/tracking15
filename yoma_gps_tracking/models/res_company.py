from odoo import api, models, fields

GOOGLEMAPS_LANG = [
    ('af', 'Afrikaans'),
    ('ja', 'Japanese'),
    ('sq', 'Albanian'),
    ('kn', 'Kannada'),
    ('am', 'Amharic'),
    ('kk', 'Kazakh'),
    ('ar', 'Arabic'),
    ('km', 'Khmer'),
    ('ar', 'Armenian'),
    ('ko', 'Korean'),
    ('az', 'Azerbaijani'),
    ('ky', 'Kyrgyz'),
    ('eu', 'Basque'),
    ('lo', 'Lao'),
    ('be', 'Belarusian'),
    ('lv', 'Latvian'),
    ('bn', 'Bengali'),
    ('lt', 'Lithuanian'),
    ('bs', 'Bosnian'),
    ('mk', 'Macedonian'),
    ('bg', 'Bulgarian'),
    ('ms', 'Malay'),
    ('my', 'Burmese'),
    ('ml', 'Malayalam'),
    ('ca', 'Catalan'),
    ('mr', 'Marathi'),
    ('zh', 'Chinese'),
    ('mn', 'Mongolian'),
    ('zh-CN', 'Chinese (Simplified)'),
    ('ne', 'Nepali'),
    ('zh-HK', 'Chinese (Hong Kong)'),
    ('no', 'Norwegian'),
    ('zh-TW', 'Chinese (Traditional)'),
    ('pl', 'Polish'),
    ('hr', 'Croatian'),
    ('pt', 'Portuguese'),
    ('cs', 'Czech'),
    ('pt-BR', 'Portuguese (Brazil)'),
    ('da', 'Danish'),
    ('pt-PT', 'Portuguese (Portugal)'),
    ('nl', 'Dutch'),
    ('pa', 'Punjabi'),
    ('en', 'English'),
    ('ro', 'Romanian'),
    ('en-AU', 'English (Australian)'),
    ('ru', 'Russian'),
    ('en-GB', 'English (Great Britain)'),
    ('sr', 'Serbian'),
    ('et', 'Estonian'),
    ('si', 'Sinhalese'),
    ('fa', 'Farsi'),
    ('sk', 'Slovak'),
    ('fi', 'Finnish'),
    ('sl', 'Slovenian'),
    ('fil', 'Filipino'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('es-419', 'Spanish (Latin America)'),
    ('fr-CA', 'French (Canada)'),
    ('sw', 'Swahili'),
    ('gl', 'Galician'),
    ('sv', 'Swedish'),
    ('ka', 'Georgian'),
    ('ta', 'Tamil'),
    ('de', 'German'),
    ('te', 'Telugu'),
    ('el', 'Greek'),
    ('th', 'Thai'),
    ('gu', 'Gujarati'),
    ('tr', 'Turkish'),
    ('iw', 'Hebrew'),
    ('uk', 'Ukrainian'),
    ('hi', 'Hindi'),
    ('ur', 'Urdu'),
    ('hu', 'Hungarian'),
    ('uz', 'Uzbek'),
    ('is', 'Icelandic'),
    ('vi', 'Vietnamese'),
    ('id', 'Indonesian'),
    ('zu', 'Zulu'),
    ('it', 'Italian'),
]
GOOGLEMAPS_THEMES = [('default', 'Default'),
                     ('aubergine', 'Aubergine'),
                     ('night', 'Night'),
                     ('dark', 'Dark'),
                     ('retro', 'Retro'),
                     ('silver', 'Silver'),
                     ('atlas', 'Atlas'),
                     ('muted_blue', 'Muted blue'),
                     ('pale_down', 'Pale down'),
                     ('subtle_gray', 'Subtle gray'),
                     ('shift_worker', 'Shift worker'),
                     ('even_lighter', 'Even lighter'),
                     ('unsaturated_brown', 'Unsaturated brown'),
                     ('uber', 'Uber')]


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def get_country(self):
        country_ids = self.env['res.country'].search([])
        values = [(country.code, country.name) for country in country_ids]
        return values

    google_maps_view_api_key = fields.Char(default="")
    google_maps_lang_localization = fields.Selection(selection=GOOGLEMAPS_LANG)
    google_maps_region_localization = fields.Selection(selection=get_country)
    google_maps_theme = fields.Selection(selection=GOOGLEMAPS_THEMES)
    google_maps_libraries = fields.Char()
    traccar_server_url = fields.Char(default="http://127.0.0.1:8082")
    traccar_username = fields.Char(default="admin")
    traccar_password = fields.Char(default="admin")
    contact_sequence_prefix = fields.Char(default="CUST")
    maximum_distance_allowed = fields.Float(default="40.0")
    add_to_odometer = fields.Boolean(default=False)
    inactivity_period_duration = fields.Char(default="30")
    do_reverse_geocoding = fields.Boolean(default=False)
