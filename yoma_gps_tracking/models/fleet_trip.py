# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions, _
from odoo.tools import format_datetime
import json
import datetime
from datetime import datetime as dt_origin


class FleetTrip(models.Model):
    _name = "fleet.trip"
    _description = 'Trip Planner'
    _order = 'name'

    name = fields.Char(
        string='Trip',
        readonly=True)

    fleet_route = fields.Many2one(
        comodel_name='fleet.route',
        string='Route')

    start_date = fields.Datetime(string='Start Date')

    end_date = fields.Datetime(string='End Date')

    vehicle = fields.Many2one('fleet.vehicle', string='Vehicle')

    driver = fields.Many2one('res.partner', string='Driver')

    partner_ids = fields.Many2many(
        related='fleet_route.partner_ids',
        string="Way Points")

    state = fields.Selection([
        ('draft', 'DRAFT'),
        ('running', 'RUNNING'),
        ('done', 'DONE'),
        ('cancelled', 'CANCELLED')],
        string='Status',
        default='draft')

    @api.depends('fleet_route', 'start_date', 'end_date')
    def calculate_map(self):

        main_company = self.env.ref("base.main_partner")

        default_value = json.dumps({
            u'lat': float(main_company.partner_latitude),
            u'lng': float(main_company.partner_longitude)
        })

        for trip in self:

            markers = []
            waypoints = []
            dateStart = False
            dateEnd = fields.Datetime.now()
            customers = trip.fleet_route.partner_ids

            if customers.exists():

                if trip.start_date:

                    dateStart = trip.start_date

                    if trip.end_date:
                        dateEnd = trip.end_date

                    from_input_date_str = dt_origin.strftime(dateStart, "%Y-%m-%d %H:%M:%S")
                    to_input_date_str = dt_origin.strftime(dateEnd, "%Y-%m-%d %H:%M:%S")
                    from_input_date_utc = datetime.datetime.strptime(from_input_date_str,
                                                                     "%Y-%m-%d %H:%M:%S") - datetime.timedelta(hours=6,
                                                                                                               minutes=30)
                    to_input_date_utc = datetime.datetime.strptime(to_input_date_str,
                                                                   "%Y-%m-%d %H:%M:%S") - datetime.timedelta(hours=6,
                                                                                                             minutes=30)

                    visited_logs = self.env['partner.visit.logs'].search([
                        ('vehicle_id', '=', trip.vehicle.id),
                        ('visit_date_time', '>=', from_input_date_utc),
                        ('visit_date_time', '<=', to_input_date_utc),
                        ('state', '=', 'ok')
                    ])

                    visited_customers = visited_logs.mapped('partner_id')

                    for customer in customers:

                        if customer.id in visited_customers.ids:

                            json_str_customer = json.dumps({
                                u'lat': float(customer.partner_latitude),
                                u'lng': float(customer.partner_longitude),
                                u'info': customer.display_name,
                                u'city': customer.city,
                                u'country_id': customer.country_id.name,
                                u'email': customer.email,
                                u'color': 'green'
                            })

                        else:

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

                    day_points = self.env['fleet.vehicle.location.history'].search([
                        ('vehicle_id', '=', trip.vehicle.id),
                        ('date_localization', '<', dateEnd),
                        ('date_localization', '>=', dateStart)
                    ])

                    if day_points.exists():

                        for point in day_points:
                            fixTime = point.date_localization + datetime.timedelta(hours=6, minutes=30)

                            json_str_point = json.dumps({
                                u'lat': float(point.vehicle_latitude),
                                u'lng': float(point.vehicle_longitude),
                                u'info': point.driver_name + ' - ' + fixTime.strftime("%Y-%m-%d %H:%M:%S") or ''
                            })

                            waypoints.append(json_str_point)

                else:

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

            trip.map = json.dumps({
                u'makers': markers,
                u'waypoints': waypoints,
                u'zoom': 17,
                u'default_value': default_value
            })

    map = fields.Text(
        string="Map",
        default=lambda self: self.calculate_map(),
        compute='calculate_map', readonly=True)

    def split_datetime2date(self, datetime_entry):
        input_date = datetime_entry.date()
        from_input_date = dt_origin.strftime(input_date, "%Y-%m-%d %H:%M:%S")
        to_input_date = dt_origin.strftime(input_date, "%Y-%m-%d 23:59:59")
        return from_input_date, to_input_date

    def get_2datetimefromdate(self, date_entry):
        from_input_date = dt_origin.strftime(date_entry, "%Y-%m-%d %H:%M:%S")
        to_input_date = dt_origin.strftime(date_entry, "%Y-%m-%d 23:59:59")
        return from_input_date, to_input_date

    def trips_filter(self, vehicle=None, driver=None, route=None, matching_date=None):

        trips_filter = []

        if matching_date:

            if type(matching_date) is datetime.date:
                from_date, to_date = self.get_2datetimefromdate(matching_date)

            if type(matching_date) is datetime:
                from_date, to_date = self.split_datetime2date(matching_date)

            trips_filter.append(('start_date', '>=', from_date),
                                ('start_date', '<=', to_date))

        if vehicle:
            trips_filter.append(('vehicle', '=', vehicle.id))

        if driver:
            trips_filter.append(('driver', '=', driver.id))

        if route:
            trips_filter.append(('fleet_route', '=', route.id))

        match_trips = self.env['fleet.trip'].search(trips_filter)

        return match_trips

    def get_match_trip(self, vehicle, driver, route, matching_date):

        if vehicle and driver and route and matching_date:

            from_date, to_date = self.split_datetime2date(matching_date)

            match_trips = self.env['fleet.trip'].search([
                ('vehicle', '=', vehicle.id),
                ('driver', '=', driver.id),
                ('fleet_route', '=', route.id),
                ('start_date', '>=', from_date),
                ('start_date', '<=', to_date)
            ])

            return match_trips

        else:

            raise exceptions.UserError(_('Please fill all data!'))

    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for item in self:
            if item.start_date and item.end_date and item.start_date >= item.end_date:
                raise exceptions.ValidationError(_(
                    '%s : end date (%s) should be greater than start date (%s)', item.name,
                    format_datetime(self.env, item.start_date),
                    format_datetime(self.env, item.end_date)))
        return True

    @api.onchange("state")
    def state_on_change(self):
        for trip in self:
            if trip.state == "cancelled":
                trip.start_date = False
                trip.end_date = False

            if trip.state == "running":
                if not trip.start_date:
                    raise exceptions.UserError(_('To start trip, please fill start date!'))

                match_trips = trip.get_match_trip(
                    vehicle=trip.vehicle,
                    driver=trip.driver,
                    route=trip.fleet_route,
                    matching_date=trip.start_date
                )

                if not match_trips.exists():
                    raise exceptions.UserError(_('System could not find any matching record!'))
                for match_trip in match_trips:
                    if match_trip.state == 'running':
                        raise exceptions.UserError(
                            _('Trip with selected vehicle, driver, and route is already running on selected date!'))
            if trip.state == "done":
                if not trip.end_date:
                    raise exceptions.UserError(_('To end trip, please fill end date!'))
                if trip.start_date > trip.end_date:
                    raise exceptions.UserError(_('End Date should be larger than start date!'))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'fleet.trip') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('fleet.trip') or _('New')

        vals['state'] = "draft"
        result = super(FleetTrip, self).create(vals)
        return result
