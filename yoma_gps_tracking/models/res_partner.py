# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from geopy.distance import geodesic

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    unique_sequence = fields.Char("Customer Code", readonly=True)
    qr_code = fields.Binary("QR Code")
    fleet_route_id = fields.Many2one(comodel_name='fleet.route', string='Vehicle Route', ondelete='restrict')
    driver = fields.Boolean(string='Is a Driver', default=False,
                            help="Check this box if this contact is a driver. It can be selected in Vehicle and Trip.")
    visit_log_ids = fields.One2many('partner.visit.logs', 'partner_id', string='Visit Logs')

    @api.model
    def create(self, vals):
        prefix = self.env.company.contact_sequence_prefix
        vals['unique_sequence'] = "%s%s" % (prefix, self.env['ir.sequence'].next_by_code(self._name))
        return super(ResPartner, self).create(vals)

    @api.depends("unique_sequence")
    def get_customer_qr_code(self):
        if qrcode and base64:
            unique_sequence = self.unique_sequence
            if not unique_sequence:
                prefix = self.env.company.contact_sequence_prefix
                unique_sequence = "%s%s" % (prefix, self.env['ir.sequence'].next_by_code(self._name))
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=40, border=4)

            qr_data = {
                'id': self.id,
                'c': unique_sequence,
                'n': self.name
            }
            if self.street:
                qr_data['s'] = self.street
            if self.street2:
                qr_data['s2'] = self.street2
            if self.city:
                qr_data['ct'] = self.city.name
            if self.town:
                qr_data['t'] = self.town.name
            if self.state_id:
                qr_data['st'] = self.state_id.name
            if self.zip:
                qr_data['zip'] = self.zip
            if self.country_id:
                qr_data['cn'] = self.country_id.name
            qr.add_data(base64.b64encode(json.dumps(qr_data).encode('ascii')))
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            self.write({
                'unique_sequence': unique_sequence,
                'qr_code': base64.b64encode(temp.getvalue())
            })
            return self.env.ref('yoma_gps_tracking.report_customer_qrcode').report_action(self)
        else:
            raise UserError(_('Dependancies not satisfied. Please contact your administrator'))

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Customer %s' % (self.unique_sequence)

class PartnerVisitLog(models.Model):
    _name = 'partner.visit.logs'
    _order = 'visit_date_time DESC'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string='Visited Partner', readonly=True)
    visit_date_time = fields.Datetime('Visited On', readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', readonly=True)
    visit_latitude = fields.Char('Latitude', readonly=True)
    visit_longitude = fields.Char('Longitude', readonly=True)
    visit_distance = fields.Float('Distance (Meter)', groups="base.group_no_one", readonly=True)
    state = fields.Selection([('ok', "OK"), ('invalid', 'Invalid')], string='State', readonly=True, default='invalid')
    map = fields.Text(string="Map", default=lambda self: self.calculate_map(),compute='calculate_map')

    @api.model
    def verify_and_insert(self, values):
        visit_latitude = float(values['visit_latitude'])
        visit_longitude = float(values['visit_longitude'])
        partner = self.env["res.partner"].sudo().search([('id', '=', int(values['partner_id']))])
        visit_log = False
        if partner.partner_latitude and partner.partner_longitude:
            visit_location = (visit_latitude, visit_longitude)
            partner_location = (partner.partner_latitude, partner.partner_longitude)
            distance = geodesic(visit_location, partner_location)
            _logger.info("VISIT LOG: DISTANCE => %f METER", distance.m)
            values["visit_distance"] = distance.m
            if distance.m <= self.env['res.config.settings'].sudo()._get_allowed_meter():
                values["state"] = 'ok'
            visit_log = self.create(values)
        else:
            partner.write({
                'partner_latitude': visit_latitude,
                'partner_longitude': visit_longitude,
                'date_localization': fields.Datetime.now()
            })
            values['state'] = 'ok'
            visit_log = self.create(values)
        return visit_log.id if visit_log else False

    @api.onchange('map','visit_latitude','visit_longitude')
    def calculate_map(self):

        for visit in self:

            if(visit.visit_latitude and visit.visit_longitude):

                makers = []

                json_str_customer = json.dumps({
                    u'lat': float(visit.visit_latitude or 0),
                    u'lng': float(visit.visit_longitude or 0),
                    u'color': 'red'
                })

                makers.append(json_str_customer)

                data = json.dumps({
                    u'makers': makers,
                    u'zoom': 17
                })

                visit.map = data

