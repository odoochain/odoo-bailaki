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
