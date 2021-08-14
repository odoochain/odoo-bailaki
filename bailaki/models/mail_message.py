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
        channel_id = self.env['mail.channel']
        channel_ids = ', '.join(str(x) for x in value['channel_ids'][0]);

        # Query to find channel already existing in database
        query = '''
            select id
              from mail_channel
             where id in (
                   select channel_id
                     from mail_channel_partner
                    where partner_id in (''' + channel_ids + ''')
                    group by channel_id 
                   having count(0) = ''' + str(len(value['channel_ids'][0])) + '''
                   )
               and channel_type = 'chat'
               and public = 'private'
             order by id desc
             limit 1  
            '''

        self.env.cr.execute(query)
        channel = self.env.cr.fetchall()

        if channel:
            channel_id = self.env['mail.channel'].search([('id', '=', channel[0])])

        if not channel_id:
            channel_id = channel_obj.create({
                'name': channel_odoo_bot_users,
                'email_send': False,
                'channel_type': 'chat',
                'public': 'private',
                'channel_partner_ids': [(4, channel_odoo_bot_users[0]), channel_odoo_bot_users[1]]
            })

        if channel_id:
                return channel_id.message_post(
                    subject="Timesheet reminder",
                    body=value['body'],
                    message_type='comment',
                    subtype='mail.mt_comment',
            )
        else:
            raise Exception('Failed to create channel')
