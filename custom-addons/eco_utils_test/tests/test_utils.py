# Copyright 2019 Ecosoft Co., Ltd., Kitti U. <kittiu@ecosoft.co.th>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPurchaseDeposit(TransactionCase):
    def setUp(self):
        super(TestPurchaseDeposit, self).setUp()
        self.partner_model = self.env['res.partner']
        self.product_model = self.env['product.product']
        self.utils_model = self.env['eco.utils']
        self.sale_model = self.env['sale.order']

        self.partner1 = self.partner_model.create({'name': 'Test Cust 1'})
        self.partner2 = self.partner_model.create({'name': 'Test Cust 2'})
        self.partner_dup = self.partner_model.create({'name': 'Test Cust Duplicated'})
        self.partner_dup2 = self.partner_model.create({'name': 'Test Cust Duplicated'})
        self.product1 = self.product_model.create(
            {
                'name': 'Test Product 1',
                'type': 'service',
                'default_code': 'PROD1',
            }
        )
        self.product2 = self.product_model.create(
            {
                'name': 'Test Product 2',
                'type': 'service',
                'default_code': 'PROD2',
            }
        )
        self.test_sale_vals = {
            'partner_id': 'Test Cust 1',
            'order_line': [
                {
                    'product_id': 'PROD1',
                    'product_uom_qty': 1,
                    'price_unit': 100,
                },
                {
                    'product_id': 'PROD2',
                    'product_uom_qty': 2,
                    'price_unit': 100,
                }
            ]
        }

    def test_friendly_create_data(self):
        # If partner and product one matching, create OK
        res = self.utils_model.friendly_create_data(
            'sale.order', self.test_sale_vals
        )
        self.assertTrue(res['is_success'])
        sale = self.sale_model.browse(res['result']['id'])
        self.assertEqual(len(sale.order_line), 2)

        # If partner find > 1 matched, can't create order
        with self.assertRaises(ValidationError):
            res = self.utils_model.friendly_create_data(
                'sale.order', {'partner_id': 'Test Cust Duplicated'}
            )

        # If partner Cust X not found, can't create order
        with self.assertRaises(ValidationError):
            res = self.utils_model.friendly_create_data(
                'sale.order', {'partner_id': 'Test Cust X'}
            )

        # If partner Cust X not found, but auto_create it, order can create
        res = self.utils_model.friendly_create_data(
            'sale.order', {'partner_id': 'Test Cust X'},
            auto_create={'partner_id': {'name': 'Test Cust X'}}
        )
        sale = self.sale_model.browse(res['result']['id'])
        self.assertEqual(sale.partner_id.name, 'Test Cust X')

    def test_friendly_update_data(self):
        # If partner and product one matching, create OK
        res = self.utils_model.friendly_create_data(
            'sale.order', self.test_sale_vals
        )
        self.assertTrue(res['is_success'])
        sale = self.sale_model.browse(res['result']['id'])
        self.assertEqual(len(sale.order_line), 2)

        # Update same sale order's date using name is search_key
        self.utils_model.friendly_update_data(
            'sale.order',
            {'name': sale.name, 'client_order_ref': 'Cust Ref', 'partner_id': 'Test Cust 2'},
            'name'  # search_key
        )
        self.assertEqual(sale.client_order_ref, 'Cust Ref')
        self.assertEqual(sale.partner_id.name, 'Test Cust 2')

        # Update partner to Cust X, not found
        with self.assertRaises(ValidationError):
            self.utils_model.friendly_update_data(
                'sale.order',
                {'name': sale.name, 'partner_id': 'Cust X'},
                'name'  # search_key
            )

        # Update partner to Cust X, not found but auto_create
        self.utils_model.friendly_update_data(
            'sale.order',
            {'name': sale.name, 'partner_id': 'Cust X'},
            'name',  # search_key
            auto_create={'partner_id': {'name': 'Cust X'}}
        )

        # Update lines, is equal to delete and create again
        self.utils_model.friendly_update_data(
            'sale.order',
            {'name': sale.name,
             'order_line': [
                {
                     'product_id': 'PROD1',
                     'product_uom_qty': 2,
                     'price_unit': 100,
                     'tax_id': False,
                 },
                 {
                     'product_id': 'PROD2',
                     'product_uom_qty': 3,
                     'price_unit': 100,
                     'tax_id': False,
                 }
             ]},
            'name',
        )
        self.assertEqual(sale.amount_total, 500)  # equal to the new lines


    def test_sample_sale_create_data(self):
        # sample_sale_create_data will have more info in the result
        res = self.sale_model.sample_create_sale_order(self.test_sale_vals)
        self.assertTrue('order_number' in res['result'] and
                        'client_order_ref' in res['result'])

    def test_sample_sale_create_update_data(self):
        # If not exists, create. If exists update it
        test_number = 'SOXXX'
        self.test_sale_vals.update({'name': test_number})
        s1 = self.sale_model.search_count([])
        # Do create / update first time, a new sale order created
        res = self.sale_model.sample_create_update_sale_order(self.test_sale_vals)
        s2 = self.sale_model.search_count([])
        self.assertEqual(s2-s1, 1)
        # Do create / update again
        res = self.sale_model.sample_create_update_sale_order(self.test_sale_vals)
        s3 = self.sale_model.search_count([])
        self.assertEqual(s3-s2, 0)

        # sale = self.sale_model.browse(res['result']['id'])
        # self.assertNotEqual(test_number, sale.name)
