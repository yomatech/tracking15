# -*- coding: utf-8 -*-

import json
import requests
import logging
import pytz

import datetime
from datetime import datetime as dt_origin
from pytz import timezone
from . import traccar

from odoo import api, fields, models, exceptions, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)


def get_last_position(cookie, device_id):
    params = {'uniqueID': device_id, 'from': '2000-01-01T00:00:00.000Z', 'to': '2050-01-01T00:00:00.000Z'}
    headers = {'Cookie': cookie[0], 'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.get(cookie[1] + '/api/positions', headers=headers, params=params)
    result = 0, 0, None, None
    for position in response.json():
        if position['deviceId'] == device_id:
            totalDistance = 0
            if 'attributes' in position and position['attributes'].get('totalDistance', False): totalDistance = \
                position['attributes'].get('totalDistance', 0)
            result = float(position['latitude']), float(position['longitude']), datetime.datetime.strptime(
                position['fixTime'], '%Y-%m-%dT%H:%M:%S.000+00:00'), totalDistance
    return result


class FleetVehicleLocationHistory(models.Model):
    _name = "fleet.vehicle.location.history"
    _order = 'date_localization desc'
    _description = 'Vehicle Location History'

    def _compute_inactive(self):
        for rec in self:
            rec.inactive_period = False
            if not rec.vehicle_id or (
                    rec.vehicle_latitude == 0 and rec.vehicle_longitude == 0) or not rec.date_localization:
                continue
            inactivity_period_duration = self.env.company.inactivity_period_duration
            on_date = rec.date_localization
            date_localization_from = on_date - datetime.timedelta(minutes=int(inactivity_period_duration))

            all_history_records = self.search(
                [('vehicle_id', '=', rec.vehicle_id.id), ('date_localization', '>=', date_localization_from),
                 ('date_localization', '<=', rec.date_localization)])
            if all_history_records:
                inactive = False
                for h in all_history_records:
                    if round(h.vehicle_latitude, 4) != round(rec.vehicle_latitude, 4) or round(h.vehicle_longitude,
                                                                                               4) != round(
                        rec.vehicle_longitude, 4):  # if locations are close enough
                        inactive = False
                        break
                    else:
                        inactive = True
                if inactive: rec.inactive_period = True

    @api.depends('date_localization')
    def _compute_bokeh_chart(self):
        superuser = self.env['res.users'].sudo().browse(SUPERUSER_ID)
        if self.env.user.partner_id.tz:
            tz = timezone(self.env.user.partner_id.tz) or timezone('UTC')
        elif superuser.partner_id.tz:
            tz = timezone(superuser.partner_id.tz) or timezone('UTC')
        else:
            tz = timezone('UTC')
        for rec in self:
            on_date = self.date_localization
            day_after = on_date + datetime.timedelta(days=1)

            day_points = self.env['fleet.vehicle.location.history'].search([('vehicle_id', '=', self.vehicle_id.id),
                                                                            ('date_localization', '<', day_after),
                                                                            ('date_localization', '>=', on_date)])

            localdate = on_date - datetime.timedelta(days=1)
            from_input_date = dt_origin.strftime(localdate, "%Y-%m-%d %H:%M:%S")
            to_input_date = dt_origin.strftime(localdate, "%Y-%m-%d 23:59:59")

            match_trip = self.env['fleet.trip'].search([
                ('vehicle', '=', self.vehicle_id.id),
                ('start_date', '>=', from_input_date),
                ('start_date', '<=', to_input_date)
            ], limit=1)

            if match_trip.exists():

                route = match_trip.fleet_route

                customers = route.partner_ids

            else:
                customers = []

            if not day_points:
                # no data
                return

            waypoints = []
            makers = []

            lst_lat = day_points.mapped('vehicle_latitude')
            lst_lng = day_points.mapped('vehicle_longitude')

            for point in day_points:
                fixTime = tz.localize(point.date_localization)
                # fixTime = fixTime.astimezone(pytz.utc)

                json_str_point = json.dumps({
                    u'lat': float(point.vehicle_latitude),
                    u'lng': float(point.vehicle_longitude),
                    u'info': point.driver_name
                })

                waypoints.append(json_str_point)

            for customer in customers:

                if customer.partner_latitude in lst_lat and customer.partner_longitude in lst_lng:

                    json_str_customer = json.dumps({
                        u'lat': float(customer.partner_latitude),
                        u'lng': float(customer.partner_longitude),
                        u'info': customer.name,
                        u'color': 'green'
                    })

                else:

                    json_str_customer = json.dumps({
                        u'lat': float(customer.partner_latitude),
                        u'lng': float(customer.partner_longitude),
                        u'info': customer.name,
                        u'color': 'red'
                    })

                makers.append(json_str_customer)

            data = json.dumps({
                u'makers': makers,
                u'waypoints': waypoints,
                u'zoom': 17
            })

            rec.trip = data
            rec.on_date = on_date.date()

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    name = fields.Char(string='Name', required=True)
    driver_name = fields.Char(string='Driver Name')
    image_128 = fields.Binary(related='vehicle_id.image_128', string="Logo (small)")
    vehicle_latitude = fields.Float(string='Geo Latitude', digits=(16, 5))
    vehicle_longitude = fields.Float(string='Geo Longitude', digits=(16, 5))
    date_localization = fields.Datetime(string='Located on')
    inactive_period = fields.Boolean(string='Inactive Period', compute='_compute_inactive', store=False)

    on_date = fields.Date(string='On Date', compute=_compute_bokeh_chart)
    all_day = fields.Boolean(string='All Day', default=True)
    trip = fields.Text(
        string='Trip',
        compute=_compute_bokeh_chart)


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    def _compute_bokeh_chart(self):
        for rec in self:
            makers = []

            json_str_customer = json.dumps({
                u'lat': float(rec.vehicle_latitude or 0),
                u'lng': float(rec.vehicle_longitude or 0),
                u'color': 'red'
            })

            makers.append(json_str_customer)

            data = json.dumps({
                u'makers': makers,
                u'zoom': 17
            })

            rec.bokeh_last_location = data

    fleet_route = fields.Many2one(comodel_name='fleet.route',
                                  string='Default Route')

    driver_id = fields.Many2one('res.partner',
                                'Driver',
                                track_visibility="onchange",
                                help='Driver of the vehicle',
                                copy=False,
                                domain="[('driver', '=', True)]")

    trips = fields.One2many(comodel_name='fleet.trip',
                            inverse_name='vehicle',
                            string='Trip Log',
                            copy=False,
                            readonly=True)

    vehicle_latitude = fields.Float(string='Geo Latitude', digits=(16, 5))
    vehicle_longitude = fields.Float(string='Geo Longitude', digits=(16, 5))
    current_address = fields.Char(string='Current Address', compute='_reverse_geocode', store=False)
    date_localization = fields.Datetime(string='Last Time Geolocated')
    traccar_uniqueID = fields.Char(string='Traccar unique ID')
    traccar_device_id = fields.Integer(string='Traccar device ID')
    gps_tracking = fields.Boolean(string='Tracking')
    location_history_ids = fields.One2many('fleet.vehicle.location.history', 'vehicle_id', string='Location History',
                                           copy=False, readonly=True)

    working_hours_from = fields.Float(string='Shift Starting Hour')
    working_hours_to = fields.Float(string='Shift Ending Hour')
    date_inactive_filter = fields.Date(string='On Date', store=False)

    bokeh_last_location = fields.Text(
        string='Last Location',
        compute=_compute_bokeh_chart)
    visit_log_ids = fields.One2many('partner.visit.logs', 'vehicle_id', string='Visit Log')

    def toggle_gps_tracking(self):
        if not self.traccar_uniqueID:
            self.gps_tracking = False
            raise exceptions.UserError(
                _('You have not provided a Traccar device unique ID, '
                  'please click Edit and enter it before '
                  'adding/removing a device!'))

        self.gps_tracking = not self.gps_tracking

        try:
            url = self.env.company.traccar_server_url
            traccar_username = self.env.company.traccar_username
            traccar_password = self.env.company.traccar_password
            traccar_api = traccar.TraccarAPI(base_url=url)
            traccar_api.login_with_credentials(username=traccar_username, password=traccar_password)
            existed_device = traccar_api.get_devices(query='uniqueId', params=self.traccar_uniqueID)

            if self.gps_tracking and not existed_device:

                new_device = traccar_api.create_device(
                    name=self.name or False,
                    unique_id=self.traccar_uniqueID,
                )
                new_device_id = new_device['id']
                self.write({'traccar_device_id': new_device_id})

            elif not self.gps_tracking and existed_device:

                traccar_api.delete_device(existed_device[0]['id'])

        except IndexError:
            raise exceptions.UserError(_(IndexError))

    def geo_localize(self):
        # for next day. convert timezone and save to server
        superuser = self.env['res.users'].sudo().browse(SUPERUSER_ID)
        if self.env.user.partner_id.tz:
            tz = timezone(self.env.user.partner_id.tz) or timezone('UTC')
        elif superuser.partner_id.tz:
            tz = timezone(superuser.partner_id.tz) or timezone('UTC')
        else:
            tz = timezone('UTC')

        for vehicle in self:

            try:

                url = self.env.company.traccar_server_url
                traccar_username = self.env.company.traccar_username
                traccar_password = self.env.company.traccar_password
                traccar_api = traccar.TraccarAPI(base_url=url)
                traccar_api.login_with_credentials(username=traccar_username, password=traccar_password)
                existed_device = traccar_api.get_devices(query='uniqueId', params=self.traccar_uniqueID)
                if existed_device and vehicle.traccar_uniqueID:

                    from_datetime = vehicle.date_localization.astimezone(pytz.utc).isoformat() \
                        if vehicle.date_localization else '2023-01-01T00:00:00Z'

                    positions = traccar_api.get_positions(
                        deviceId=existed_device[0]['id'],
                        from_datetime=from_datetime,
                        to_datetime=dt_origin.now(pytz.utc).isoformat(),
                    )

                    for position in positions:

                        gps_time = dt_origin.strptime(
                            position['fixTime'], '%Y-%m-%dT%H:%M:%S.000+00:00')

                        if not vehicle.date_localization or gps_time > vehicle.date_localization:
                            vehicle.write({'location_history_ids': [(0, 0, {
                                'vehicle_id': vehicle.id,
                                'name': vehicle.name,
                                'driver_name': vehicle.driver_id.name,
                                'vehicle_latitude': position['latitude'],
                                'vehicle_longitude': position['longitude'],
                                'date_localization': gps_time
                            })
                                                                    ],
                                           'date_localization': gps_time,
                                           'vehicle_latitude': position['latitude'],
                                           'vehicle_longitude': position['longitude']
                                           })
            except IndexError:
                raise exceptions.UserError(_(IndexError))
        return True

    @api.model
    def schedule_traccar(self):
        """Schedules fleet tracking using Traccar platform.
        """

        records_to_schedule = self.env['fleet.vehicle'].search(
            [('gps_tracking', '=', True), ('traccar_uniqueID', '!=', False)])

        if not records_to_schedule:
            return

        res = None
        try:
            records_to_schedule.geo_localize()
            res = True
        except Exception:
            raise exceptions.UserError(_(Exception))
        return res

    def action_show_day_trip(self):
        self.ensure_one()
        context = self.env.context.copy()
        context['default_vehicle_id'] = self.id
        new_ids = []
        all_dates = []
        all_location_records = self.env['fleet.vehicle.location.history'].search(
            [('vehicle_id', '=', self.id), ('date_localization', '!=', False), ('vehicle_latitude', '!=', 0),
             ('vehicle_longitude', '!=', 0)], order='date_localization desc')
        if all_location_records:
            for day in all_location_records:
                last_date = day.date_localization.date()
                if last_date not in all_dates:
                    all_dates.append(last_date)
                    new_id = self.env['fleet.vehicle.day.trip'].create({'vehicle_id': self.id, 'on_date': last_date})
                    if new_id:
                        new_ids.append(new_id.id)
        view_id = self.env.ref('yoma_gps_tracking.view_vehicle_day_trip_calendar')
        return {
            'name': _('Daily Trip Data'),
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.day.trip',
            'view_mode': 'calendar',
            'view_type': 'calendar',
            'target': 'current',
            'views': [(view_id.id, 'calendar')],
            'context': context,
            'domain': [('id', 'in', new_ids)]
        }


class FleetVehicleDayTrip(models.TransientModel):
    _name = "fleet.vehicle.day.trip"
    _description = 'Daily Vehicle Trip Data'
    _rec_name = 'on_date'

    @api.depends('on_date')
    def _compute_bokeh_chart(self):
        superuser = self.env['res.users'].sudo().browse(SUPERUSER_ID)
        if self.env.user.partner_id.tz:
            tz = timezone(self.env.user.partner_id.tz) or timezone('UTC')
        elif superuser.partner_id.tz:
            tz = timezone(superuser.partner_id.tz) or timezone('UTC')
        else:
            tz = timezone('UTC')
        for rec in self:
            on_date = self.on_date
            day_after = on_date + datetime.timedelta(days=1)

            day_points = self.env['fleet.vehicle.location.history'].search([('vehicle_id', '=', self.vehicle_id.id),
                                                                            ('date_localization', '<', day_after),
                                                                            ('date_localization', '>=', on_date)])

            from_input_date_str = dt_origin.strftime(on_date, "%Y-%m-%d %H:%M:%S")
            to_input_date_str = dt_origin.strftime(on_date, "%Y-%m-%d 23:59:59")
            from_input_date_utc = datetime.datetime.strptime(from_input_date_str,
                                                             "%Y-%m-%d %H:%M:%S") - datetime.timedelta(hours=6,
                                                                                                       minutes=30)
            to_input_date_utc = datetime.datetime.strptime(to_input_date_str, "%Y-%m-%d %H:%M:%S") - datetime.timedelta(
                hours=6, minutes=30)

            match_trip = self.env['fleet.trip'].search([
                ('vehicle', '=', self.vehicle_id.id),
                ('start_date', '>=', from_input_date_utc),
                ('start_date', '<=', to_input_date_utc),
                ('state', 'not in', ['draft', 'cancelled'])
            ], limit=1)

            visited_logs = self.env['partner.visit.logs'].search([
                ('vehicle_id', '=', self.vehicle_id.id),
                ('visit_date_time', '>=', from_input_date_utc),
                ('visit_date_time', '<=', to_input_date_utc),
                ('state', '=', 'ok')
            ])

            waypoints = []
            makers = []

            if match_trip.exists():

                route = match_trip.fleet_route

                customers = route.partner_ids

                visited_customers = visited_logs.mapped('partner_id')

                for customer in customers:

                    if customer.id in visited_customers.ids:

                        json_str_customer = json.dumps({
                            u'lat': float(customer.partner_latitude),
                            u'lng': float(customer.partner_longitude),
                            u'info': customer.name,
                            u'color': 'green'
                        })

                    else:

                        json_str_customer = json.dumps({
                            u'lat': float(customer.partner_latitude),
                            u'lng': float(customer.partner_longitude),
                            u'info': customer.name,
                            u'color': 'red'
                        })

                    makers.append(json_str_customer)

            if day_points.exists():

                for point in day_points:
                    fixTime = point.date_localization + datetime.timedelta(hours=6, minutes=30)

                    json_str_point = json.dumps({
                        u'lat': float(point.vehicle_latitude),
                        u'lng': float(point.vehicle_longitude),
                        u'info': point.driver_name
                    })

                    waypoints.append(json_str_point)

            main_company = self.env.ref("base.main_partner")

            default_value = json.dumps({
                u'lat': float(main_company.partner_latitude),
                u'lng': float(main_company.partner_longitude)
            })

            data = json.dumps({
                u'makers': makers,
                u'waypoints': waypoints,
                u'zoom': 17,
                u'default_value': default_value
            })

            rec.trip = data

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    on_date = fields.Date(string='On Date', default=fields.Date.today(), required=True, track_visibility='always')
    trip = fields.Text(
        string='Trip',
        compute=_compute_bokeh_chart, track_visibility='always')


class FleetVehicleRoute(models.Model):
    _name = "fleet.route"
    _description = 'Vehicle Route'
    _order = 'name'

    name = fields.Char(string='Route Name',
                       required=True)

    starting_point = fields.Many2one(comodel_name='res.partner',
                                     compute='onchange_partner_ids',
                                     string='Starting Point',
                                     readonly=True)
    ending_point = fields.Many2one(comodel_name='res.partner',
                                   compute='onchange_partner_ids',
                                   string='Ending Point',
                                   readonly=True)
    partner_count = fields.Integer(string="Way Points",
                                   compute='onchange_partner_ids',
                                   readonly=True,
                                   default=0)

    partner_ids = fields.Many2many(comodel_name='res.partner', string='Customers')

    map = fields.Text(string="Map", default=lambda self: self.calculate_map(), compute='calculate_map', readonly=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Vehicle route name already exists !"),
    ]

    @api.onchange('partner_ids')
    def onchange_partner_ids(self):

        for trip_route in self:

            customers = trip_route.partner_ids

            if customers.exists():
                trip_route.starting_point = trip_route.partner_ids[0]
                trip_route.ending_point = trip_route.partner_ids[-1]
                trip_route.partner_count = len(trip_route.partner_ids)

    @api.depends('partner_ids')
    def calculate_map(self):

        for trip_route in self:

            main_company = self.env.ref("base.main_partner")

            default_value = json.dumps({
                u'lat': float(main_company.partner_latitude),
                u'lng': float(main_company.partner_longitude)
            })

            markers = []

            customers = trip_route.partner_ids

            if customers.exists():

                for customer in customers:
                    json_str_customer = json.dumps({
                        u'lat': float(customer.partner_latitude),
                        u'lng': float(customer.partner_longitude),
                        u'info': customer.display_name,
                        u'city': customer.city,
                        u'country_id': customer.country_id.name,
                        u'email': customer.email,
                        u'color': 'red'
                    })

                    markers.append(json_str_customer)

            trip_route.map = json.dumps({
                u'makers': markers,
                u'zoom': 17,
                u'default_value': default_value
            })

    def count_waypoints(self):
        pass
