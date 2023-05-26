# -*- coding: utf-8 -*-

from odoo import fields, models


class City(models.Model):
    _name = 'res.city'
    _description = 'City'
    _order = 'name'

    name = fields.Char("Name", required=True, translate=True)
    state_id = fields.Many2one('res.country.state', string='State', required=True)
    town_ids = fields.One2many('res.town', 'city', string='Towns')