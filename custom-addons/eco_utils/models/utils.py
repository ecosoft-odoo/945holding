# Copyright 2020 Ecosoft Co., Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class EcoUtils(models.AbstractModel):
    _name = 'eco.utils'
    _description = 'Utils Class'

    @api.model
    def friendly_create_data(self, model, data_dict, auto_create={}):
        """ Accept friendly data_dict in following format to create data
            data_dict:
            {'field1': value1,
             'field2_id': value2,  # can be ID or name search string
             'line_ids': [{
                'field2': value2,
             }]
            }
           auto_create:
            {'field2_id': {'name': 'Test'}, ...}
            Auto create master data, if not found.
            Only for many2one on header, not for lines
        """
        res = {}
        rec = self.env[model].new()  # Dummy reccord
        rec_fields = []
        line_fields = []
        for field, model_field in rec._fields.items():
            if field in data_dict and model_field.type != 'one2many':
                rec_fields.append(field)
            elif field in data_dict:
                line_fields.append(field)
        rec_dict = {k: v for k, v in data_dict.items() if k in rec_fields}
        rec_dict = self._finalize_data_to_write(rec, rec_dict,
                                                auto_create=auto_create)
        # Prepare Line Dict (o2m)
        for line_field in line_fields:
            final_line_dict = []
            # Loop all o2m lines, and recreate it
            for line_data_dict in data_dict[line_field]:
                rec_fields = []
                line_fields = []
                for field, model_field in rec[line_field]._fields.items():
                    if field in line_data_dict and \
                            model_field.type != 'one2many':
                        rec_fields.append(field)
                    elif field in line_data_dict:
                        line_fields.append(field)
                line_dict = {k: v for k, v in line_data_dict.items()
                             if k in rec_fields}
                if line_fields:
                    raise ValidationError(_('friendly_create_data() support '
                                            'only 1 level of one2many lines'))
                line_dict = self._finalize_data_to_write(rec[line_field],
                                                         line_dict)
                final_line_dict.append((0, 0, line_dict))
            rec_dict[line_field] = final_line_dict
        obj = rec.create(rec_dict)
        res = {
            'is_success': True,
            'result': {
                'id': obj.id,
            },
            'messages': _('Record created successfully'),
        }
        return res

    @api.model
    def friendly_update_data(self, model, data_dict, key_field, auto_create={}):
        """ Accept friendly data_dict in following format to update existing rec
        This method, will always delete o2m lines and recreate it.
            data_dict:
            {'field1': value1,
             'line_ids': [{
                'field2': value2,
             }]
            }
            key_field: search field, i.e., number
           auto_create:
            {'field2_id': {'name': 'Test'}, ...}
            Auto create master data, if not found.
            Only for many2one on header, not for lines
        """
        res = {}
        # Prepare Header Dict (non o2m)
        if not key_field or key_field not in data_dict:
            raise ValidationError(
                _('Method update_data() key_field is not valid!'))
        rec = self.env[model].search([(key_field, '=', data_dict[key_field])])
        if not rec:
            raise ValidationError(_('Search key "%s" not found!') %
                                  data_dict[key_field])
        elif len(rec) > 1:
            raise ValidationError(_('Search key "%s" found mutiple matches!') %
                                  data_dict[key_field])
        rec_fields = []
        line_fields = []
        for field, model_field in rec._fields.items():
            if field in data_dict and model_field.type != 'one2many':
                rec_fields.append(field)
            elif field in data_dict:
                line_fields.append(field)
        rec_dict = {k: v for k, v in data_dict.items() if k in rec_fields}
        rec_dict = self._finalize_data_to_write(rec, rec_dict,
                                                auto_create=auto_create)
        # Prepare Line Dict (o2m)
        for line_field in line_fields:
            lines = rec[line_field]
            # First, delete all lines o2m
            lines.unlink()
            final_line_dict = []
            final_line_append = final_line_dict.append
            # Loop all o2m lines, and recreate it
            for line_data_dict in data_dict[line_field]:
                rec_fields = []
                rec_fields_append = rec_fields.append
                line_fields = []
                for field, model_field in rec[line_field]._fields.items():
                    if field in line_data_dict and \
                            model_field.type != 'one2many':
                        rec_fields_append(field)
                    elif field in line_data_dict:
                        line_fields.append(field)
                line_dict = {k: v for k, v in line_data_dict.items()
                             if k in rec_fields}
                if line_fields:
                    raise ValidationError(_('friendly_update_data() support '
                                            'only 1 level of one2many lines'))
                line_dict = self._finalize_data_to_write(lines, line_dict)
                final_line_append((0, 0, line_dict))
            rec_dict[line_field] = final_line_dict
        rec.write(rec_dict)
        res = {
            'is_success': True,
            'result': {
                'id': rec.id,
            },
            'messages': _('Record updated successfully'),
        }
        return res

    @api.model
    def _finalize_data_to_write(self, rec, rec_dict, auto_create={}):
        """ For many2one, many2many, use name search to get id """
        final_dict = {}
        for key, value in rec_dict.items():
            ftype = rec._fields[key].type
            if key in rec_dict.keys() and ftype in ('many2one', 'many2many'):
                model = rec._fields[key].comodel_name
                Model = self.env[model]
                if rec_dict[key] and isinstance(rec_dict[key], str):
                    search_vals = []
                    if ftype == 'many2one':
                        search_vals = [rec_dict[key]]
                    elif ftype == 'many2many':
                        search_vals = rec_dict[key].split(',')
                        value = []  # for many2many, result will be tuple
                    for val in search_vals:
                        values = Model.name_search(val, operator='=')
                        # If failed, try again by ID
                        if len(values) != 1:
                            if val and isinstance(val, int):
                                rec = Model.search([('id', '=', val)])
                                if len(rec) == 1:
                                    values = [(rec.id, )]
                        # If not found, but auto_create it
                        if len(values) != 1 and auto_create.get(key):
                            res = self.friendly_create_data(model, auto_create[key])
                            values = [(res['result']['id'], )]
                        # --
                        if len(values) > 1:
                            raise ValidationError(
                                _('"%s" matched more than 1 record') % val)
                        elif not values:
                            raise ValidationError(
                                _('"%s" found no match.') % val)
                        if ftype == 'many2one':
                            value = values[0][0]
                        elif ftype == 'many2many':
                            value.append((4, values[0][0]))
            final_dict.update({key: value})
        return final_dict
