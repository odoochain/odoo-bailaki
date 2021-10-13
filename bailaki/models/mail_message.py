# Copyright 2021 Pop Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import requests
import json

class MailMessage(models.Model):

    _inherit = 'mail.message'
    
    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def bailaki_message_post(self, values):
        value = values[0]
        channel_id = self.env['mail.channel'].search([('id', '=', value['res_id'])])

        if not channel_id:
            raise Exception('Channel "' + value['res_id'] + '" not found')

        return channel_id.message_post(
            subject="Timesheet reminder",
            body=value['body'],
            message_type='comment',
            subtype='mail.mt_comment')

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        idLastMessage = 0

        for arg in args:
            if ((arg[0] == 'id') and (arg[1] == '>') and (str(arg[2]).isdigit())): #  sample: ["id", ">","400"]
                idLastMessage = int(arg[2]);

            if (arg[0] == 'res_id'):
                channel_id = arg[2];

        res = super(MailMessage, self)._search(
            args, offset=offset, limit=limit, order=order,
            count=count, access_rights_uid=access_rights_uid)

        if idLastMessage > 0:
            self.env['hermes.monitor'].create(
                    {'partner_id': self.env.user.partner_id.id,
                     'idlastmessage': idLastMessage,
                     'channel_id': channel_id}
                );

        return res
