# -*- coding: utf-8 -*-

from odoo import fields, models


class Town(models.Model):
    _name = 'res.town'
    _description = 'Township'
    _order = 'name'

    name = fields.Char("Name", required=True, translate=True)
    city = fields.Many2one('res.city', string='City', required=True)