# Copyright 2020 Ecosoft Co., Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class EcoUtils(models.Model):
    """ Sample use of eco.utils create_data, addong more logics """
    _inherit = 'sale.order'

    @api.model
    def sample_create_sale_order(self, vals):
        _logger.info('sample_create_sale_order(), input: %s' % vals)
        try:
            Utils = self.env['eco.utils']
            res = Utils.friendly_create_data(self._name, vals)
            if res['is_success']:
                res_id = res['result']['id']
                sale = self.browse(res_id)
                # BUSINESS LOGIC, i.e., overwrite some sale order value
                sale.write({'client_order_ref': 'Test Test Test'})
                # return more data
                res['result']['order_number'] = sale.name
                res['result']['client_order_ref'] = sale.client_order_ref
        except Exception as e:
            res = {
                'is_success': False,
                'result': False,
                'messages': _(str(e)),
            }
            self._cr.rollback()
        _logger.info('sample_create_sale_order(), output: %s' % res)
        return res

    @api.model
    def sample_create_update_sale_order(self, vals):
        _logger.info('sample_create_update_sale_order(), input: %s' % vals)
        try:  # Update
            if not self.search([('name', '=', vals.get('name'))]):
                return self.sample_create_sale_order(vals)  # fall back to create
            Utils = self.env['eco.utils']
            res = Utils.friendly_update_data(self._name, vals, 'name')
            if res['is_success']:
                res_id = res['result']['id']
                p = self.browse(res_id)
                res['result']['name'] = p.name
        except Exception as e:
            res = {
                'is_success': False,
                'result': False,
                'messages': _(str(e)),
            }
            self._cr.rollback()
        _logger.info('sample_create_update_sale_order(), output: %s' % res)
        return res
