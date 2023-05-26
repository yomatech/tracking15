# -*- coding: utf-8 -*-

from odoo import api, models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    town = fields.Many2one('res.town', string='Town', ondelete='restrict')
    city_id = fields.Many2one('res.city', string='City', ondelete='restrict')

    @api.model
    def _get_default_address_format(self):
        return "%(street)s\n%(street2)s\n%(town_name)s\n%(city_name)s\n%(state_name)s %(zip)s\n%(country_name)s"

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            return {'domain': {'city_id': [('state_id', '=', self.state_id.id)]}}
        else:
            return {'domain': {'city_id': []}}

    @api.onchange('city_id')
    def _onchange_city(self):
        if self.city_id:
            self.city = self.city_id.name
            return {'domain': {'town': [('city_id', '=', self.city_id.id)]}}
        else:
            self.city = False
            return {'domain': {'town': []}}

    @api.model
    def _address_fields(self):

        res = super(Partner, self)._address_fields()

        res.append("town")

        return res

    def _display_address_depends(self):

        res = super(Partner, self)._address_fields()

        res.append("city_id.name")
        res.append("town.name")

        return res

    def _get_address_args(self):

        args = {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self._get_country_name(),
            'company_name': self.commercial_company_name or '',
            'city_name': self._get_city_name(),
            'town_name': self._get_town_name(),
        }

        return args

    def _display_address(self, without_company=False):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_address_format()

        args = self._get_address_args()

        for field in self._address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

    def _get_city_name(self):
        return self.city_id.name or ''

    def _get_town_name(self):
        return self.town.name or ''

    @api.depends('street', 'zip', 'city', 'town', 'country_id')
    def _compute_complete_address(self):
        for record in self:
            record.contact_address_complete = ''
            if record.street:
                record.contact_address_complete += record.street + ','
            if record.zip:
                record.contact_address_complete += record.zip + ' '
            if record.city_id:
                record.contact_address_complete += record.city_id.name + ','
            if record.town:
                record.contact_address_complete += record.town.name + ','
            if record.country_id:
                record.contact_address_complete += record.country_id.name
