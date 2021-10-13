# Copyright 2021 Pop Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, http
from odoo.http import request, Response
import json


class odooController(http.Controller):
  @http.route('/bailaki/channels_amounts/', auth='public', type="http")
  def index(self, **kw):
    try:
      partner_id = int(kw['partner_id'])
    except:
      return Response(json.dumps({'data': {'status': 400, 'response': 'Invalid Params'}}), status=400,
                      content_type="application/json")

    query = '''
select t.channelId,
       t.name,
       t.idlastreadmessage,
       t.leftPartnerId,
       rp_left.name leftPartnerName,
       t.rightPartnerId,
       rp_rigth.name rigthPartnerName,
       t.lastMessage
  from res_partner rp_left,
       res_partner rp_rigth,
       (
        select mcn.id channelId,
               mcn.name,
               mcp.idlastreadmessage,
               (
               select count(0)
                 from mail_message mmg
                where mmg.res_id = mcn.id 
                  and mmg.id > coalesce(mcp.idlastreadmessage, 0)
                  and mmg.author_id <> mcp.partner_id
                      and mmg.message_type = 'comment'
               ) amount_newmessages,
               (select mcp2.partner_id 
                  from mail_channel_partner mcp2
                 where mcp2.channel_id = mcp.channel_id
                 limit 1 
               ) leftPartnerId,
               (select mcp2.partner_id 
                  from mail_channel_partner mcp2
                 where mcp2.channel_id = mcp.channel_id
                 limit 1 offset 1
               ) rightPartnerId,
               (
               select mm.body 
                 from mail_message mm 
                where mm.res_id = mcn.id
                order by mm.id desc
                limit 1
               ) lastMessage
          from mail_channel_partner mcp,
               mail_channel mcn
         where partner_id = ''' + str(partner_id) + '''
           and mcn.id = mcp.channel_id 
           and mcn.channel_type = 'chat'    
     ) t
 where rp_left.id = t.leftPartnerId
   and rp_rigth.id = t.rightPartnerId  
        '''

    channelsJson = []

    request.env.cr.execute(query)
    channels = request.env.cr.fetchall()

    for channel in channels:
      item = {
        'channelId': channel[0],
        'name': channel[1],
        'idlastreadmessage': channel[2],
        'leftPartnerId': channel[3],
        'leftPartnerName': channel[4],
        'rightPartnerId': channel[5],
        'rigthPartnerName': channel[6],
        'lastMessage': channel[7]
      }

      channelsJson.append(item)

    data = {'status': 200, 'response': channelsJson}
    # return data;
    return Response(json.dumps({'data': data}), status=200, content_type="application/json")


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
    channel_id = 0
    processLastMessage = False

    for arg in args:
      if arg[0].upper() == 'processLastMessage'.upper():
        processLastMessage = arg[2].upper() == 'TRUE'
        args.remove(arg)

    for arg in args:
      if ((arg[0] == 'id') and (arg[1] == '>') and (str(arg[2]).isdigit())):  # sample: ["id", ">","400"]
        idLastMessage = int(arg[2])

      if (arg[0] == 'res_id'):
        channel_id = arg[2]

    res = super(MailMessage, self)._search(
      args, offset=offset, limit=limit, order=order,
      count=count, access_rights_uid=access_rights_uid)

    if processLastMessage:
      # todo - Improvement: run hermes_monitor_only 1 time validation when starting odoo
      self.env.cr.execute("select id from ir_module_module where name = 'hermes-message' limit 1")
      hermes_message_model = self.env.cr.fetchall()

      hermes_monitor_installed = not (len(hermes_message_model) == 0)

      if hermes_monitor_installed:
        if idLastMessage > 0:
          self.env['hermes.monitor'].create(
            {'partner_id': self.env.user.partner_id.id,
             'idlastmessage': idLastMessage,
             'channel_id': channel_id}
          )

      if (len(res) > 0 and channel_id > 0):
        query = '''
                    update mail_channel_partner 
                       set idlastreadmessage = ''' + str(res[0]) + '''
                     where channel_id = ''' + str(channel_id) + '''
                       and partner_id = ''' + str(self.env.user.partner_id.id)

        self.env.cr.execute(query)

    return res