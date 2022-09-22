# Copyright 2021 Pop Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, http, tools
from odoo.http import request, Response
import json


class odooController(http.Controller):
  @http.route('/bailaki/events/', auth='public', type="http")
  def get_events(self, **kw):
    query = """
select ee.id,
       ee.state,
       ee.name,
       ee.date_begin,
       ee.date_end,
       ee.organizer_id,
       rp.name organizer_name, 
       rp.street,
       rp.zip,
       rp.city,
       st.name statename,
       coalesce(rp.partner_current_latitude, 0) partner_current_latitude,
       coalesce(rp.partner_current_longitude, 0) partner_current_longitude,
       event_type_id
  from event_event ee,
       res_partner rp left join res_country_state st on (st.id = rp.state_id)
 where rp.id = ee.address_id
   and ee.state = 'confirm'  
    """

    eventsJson = []

    request.env.cr.execute(query)
    events = request.env.cr.fetchall()

    for event in events:
      event_event = request.env['event.event'].search([('id', '=', event[0])])

      eventsJson.append({
        'id': event[0],
        'state': event[1],
        'name': event[2],
        'date_begin': str(event[3]),
        'date_end': str(event[4]),
        'organizer_id': event[5],
        'organizer_name': event[6],
        'street': event[7],
        'zip': event[8],
        'city': event[9],
        'statename': event[10],
        'partner_current_latitude': event[11],
        'partner_current_longitude': event[12],
        'website_url': event_event.website_url,
        'event_type_id': event[13]
      })

    data = {'status': 200, 'response': eventsJson}
    return Response(json.dumps({'data': data}), status=200, content_type="application/json")

  @http.route('/bailaki/printlog/', auth='public', type="http")
  def printlog(self, **kw):
    print('** Mobile Bailaki Log: ' + kw['msg'])
    return Response(json.dumps({'data': {'status': 200}}), status=200, content_type="application/json")

  @http.route('/bailaki/ir_config_parameters/', auth='public', type="http")
  def ir_config_parameters(self, **kw):
    ir_config_parameters = request.env['ir.config_parameter'].sudo().search([('key', 'like', 'MobileBailakiParams.%')])
    ir_config_parametersReturn = []

    for ir_config_parameter in ir_config_parameters:
      ir_config_parametersReturn.append({
        'id': ir_config_parameter['id'],
        'key': ir_config_parameter['key'],
        'value': ir_config_parameter['value']
      })

    data = {'status': 200, 'response': ir_config_parametersReturn}
    return Response(json.dumps({'data': data}), status=200, content_type="application/json")


  @http.route('/bailaki/channels_amounts/', auth='public', type="http")
  def channels_amounts(self, **kw):
    channel_idSql = ''
    partner_idSql = ''
    partner_id = 0
    try:
      if 'channel_id' in kw:
        channel_idSql = kw['channel_id']
        int(channel_idSql) #only validation int tyoe
        channel_idSql = ' and mcp.channel_id = ' + channel_idSql

      if 'partner_id' in kw:
        partner_id = int(kw['partner_id'])
        partner_idSql = ' and partner_id = ' + str(partner_id)

      getImages = str(kw['getImages']).upper() == 'TRUE'
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
       t.lastMessage,
       t.amount_newmessages
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
         where 0 = 0 ''' + partner_idSql + channel_idSql + '''
           and mcn.id = mcp.channel_id 
           and mcn.channel_type = 'chat'    
     ) t
 where rp_left.id = t.leftPartnerId
   and rp_rigth.id = t.rightPartnerId
   and not exists 
       (--disregarding Unmatch
       select rpr.id 
         from res_partner_relation rpr
        where type_id = (select id from res_partner_relation_type rprt where name = 'Unmatch')
          and (   (rpr.left_partner_id = t.leftPartnerId and rpr.right_partner_id = t.rightPartnerId)
               or (rpr.left_partner_id = t.rightPartnerId and rpr.right_partner_id = t.leftPartnerId)
              )
         limit 1
       )        
        '''

    channelsJson = []

    request.env.cr.execute(query)
    channels = request.env.cr.fetchall()

    for channel in channels:

      photoLeft = None
      photoRight = None

      if getImages:
        def getPhoto(res_partner_id):
          if res_partner_id == partner_id:
            return None

          photo = None

          res_partner_image = request.env['res.partner.image'].sudo().search([('res_partner_id', '=', res_partner_id)], limit=1)

          if res_partner_image:
            # images = tools.image_get_resized_images(res_partner_image[0].image, return_medium=False)
            # images = tools.image_resize_image_small(res_partner_image[0].image, avoid_if_small = True)
            # photo = images.decode("utf-8")
            photo = res_partner_image[0].image.decode("utf-8")

          return photo

          # res_partner = request.env['res.partner'].sudo().search([('id', '=', res_partner_id)], limit=1).read(['image_small'])
          #
          # if res_partner:
          #   photo = res_partner[0]['image_small'].decode("utf-8")
          #
          # return photo

        photoLeft = getPhoto(channel[3])
        photoRight = getPhoto(channel[5])

      partnerLeft = {
        'id': channel[3],
        'name': channel[4],
        'photo': photoLeft
      }

      partnerRight = {
        'id': channel[5],
        'name': channel[6],
        'photo': photoRight
      }

      item = {
        'channelId': channel[0],
        'name': channel[1],
        'idlastreadmessage': channel[2],
        'leftPartnerId': channel[3],
        'rightPartnerId': channel[5],
        'lastMessage': channel[7],
        'amount_newmessages': channel[8],
        'partners': [partnerLeft, partnerRight]
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
