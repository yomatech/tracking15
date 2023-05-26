# -*- coding: utf-8 -*-

from odoo import fields, models


class CountryState(models.Model):
    _inherit = 'res.country.state'

    city_ids = fields.One2many('res.city', 'state_id', string='Cities')
