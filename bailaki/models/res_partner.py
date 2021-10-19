# Copyright 2020 - TODAY, Marcel Savegnago
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from math import radians, cos, sin, asin, sqrt
from dateutil.relativedelta import relativedelta

# Formula de Haversine
def haversine(a, b):
    # Raio da Terra em Km
    r = 6371

    # Converte coordenadas de graus para radianos
    lon1, lat1, lon2, lat2 = map(radians, [
        a['partner_current_longitude'],
        a['partner_current_latitude'],
        b['partner_current_longitude'],
        b['partner_current_latitude']
    ])

    # Formula de Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    hav = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    d = 2 * r * asin(sqrt(hav))

    return d


class ResPartner(models.Model):

    _inherit = 'res.partner'

    profile_description = fields.Text(string="Profile Description", size=140)

    res_partner_image_ids = fields.One2many(
        'res.partner.image',
        'res_partner_id',
        string='Images')

    music_genre_ids = fields.Many2many(
        'res.partner.music.genre',
        string='Music Genres')

    music_skill_id = fields.Many2one(
        'res.partner.music.skill',
        string='Music Skill')

    referred_friend_ids = fields.Many2many(
        'res.partner',
        string="Referred Friends",
        compute='_compute_referred_friend_ids')

    referred_friend_count = fields.Integer(
        compute="_compute_referred_friend_count",
        string='# Referred Friends')

    referred_friend_max_distance = fields.Integer(
        string="Referred Friend Max Distance",
        default=25)

    referred_friend_min_age = fields.Integer(
        string="Referred Friend Min Age",
        default=18)

    referred_friend_max_age = fields.Integer(
        string="Referred Friend Max Age",
        default=99
    )

    interest_male_gender = fields.Boolean(
        string='Interest in the male gender',
        default=False)

    interest_female_gender = fields.Boolean(
        string='Interest in the female gender',
        default=False)

    interest_other_genres = fields.Boolean(
        string='Interest in other genres',
        default=False)

    partner_current_latitude = fields.Float(
        string='Geo Current Latitude',
        digits=(16, 5))

    partner_current_longitude = fields.Float(
        string='Geo Current Longitude',
        digits=(16, 5))

    enable_match_notification = fields.Boolean(
        string='Enable Match Notification',
        default=True
    )

    enable_message_notification = fields.Boolean(
        string='Enable Message Notification',
        default=True
    )

    age = fields.Integer(string="Age", readonly=True, compute="_compute_age", store=True)

    @api.depends("birthdate_date")
    def _compute_age(self):
        for record in self:
            age = 0
            if record.birthdate_date:
                age = relativedelta(fields.Date.today(), record.birthdate_date).years
            record.age = age

    @api.depends('referred_friend_ids')
    def _compute_referred_friend_count(self):
        for rec in self:
            rec.inspection_count = len(
                rec.referred_friend_ids)

    @api.depends('relation_all_ids')
    def _compute_match_relation(self):
        for rec in self:
            send_likes = rec.relation_all_ids.filtered(
                lambda x: x.this_partner_id == rec and
                          x.tab_id.code == 'send_likes'
            )
            for send in send_likes:
                if not rec.relation_all_ids.filtered(
                        lambda x: x.tab_id.code == 'matches' and
                                  x.other_partner_id == send.other_partner_id):

                    match = rec.relation_all_ids.filtered(
                        lambda x: x.this_partner_id == rec and
                                  x.tab_id.code == 'receive_likes' and
                                  x.other_partner_id == send.other_partner_id)

                    if match:
                        # Cria relação do tipo match
                        rec.env['res.partner.relation'].create({
                            'type_id': rec.env.ref('bailaki.relation_type_match').id,
                            'left_partner_id': rec.id,
                            'right_partner_id': match.other_partner_id.id})

                        # Envia notificação via OdooBot para os envolvidos no match
                        rec.env['mail.channel'].sudo().message_post(
                            body='<p>Match entre %s e %s</p>' % (
                            match.this_partner_id.name, match.other_partner_id.name),
                            subtype='mail.mt_comment',
                            model='mail.channel',
                            partner_ids=[
                                match.this_partner_id.id,
                                match.other_partner_id.id]
                        )
                        
                      
                        # Criar o Canal
                        mail_channel = self.env['mail.channel'].create({
                            'name': str(rec.id) + ',' + str(match.other_partner_id.id),
                            'alias_name': '(' + str(rec.id) + ' - ' + str(match.other_partner_id.id) + ')',
                            'channel_type': 'chat',
                            'public': 'private',
                            'channel_partner_ids': [(4, rec.id), (4, match.other_partner_id.id)],
                            # The user must join the group
                            # 'channel_partner_ids': [(4, self.env.user.partner_id.id), (4, rec.id)]
                        })

                        queryDeletarOutrosPartnersIds = 'delete from mail_channel_partner where channel_id = ' + str(mail_channel.id) + ' and partner_id not in (' + str(rec.id) + ',' + str(match.other_partner_id.id) + ')';

                        # Deletar partner que possam ter sido incluídos pelas heranças (a rotina mail.channel.create criar o relacionamento com self.env.user.partner_id.id automaticamente)
                        self.env.cr.execute(queryDeletarOutrosPartnersIds);

                        if mail_channel:
                            #Alterando "is_pinned" de mail.channel.partner (Que foi inserido automaticamente ao criar o mail.channel)
                            mail_channel_partner = rec.env['mail.channel.partner'].search(
                                [['channel_id', '=', mail_channel.id]]);
                            mail_channel_partner.write({'is_pinned': True});

                        #Criar notificação mobile

                        mobileNitification = [{
                            'author_id': rec.id,
                            'res_id': mail_channel.id,
                            'subject': 'Novo Parceiro',
                            'body': rec.name + ' também quer dançar com você'}
                        ]

                        self.env['mail.message'].sendModileNotification(mobileNitification, 0)

    @api.multi
    def _compute_referred_friend_ids(self):
        for rec in self:
            if rec.id and rec.is_company == False:

                block_partner_ids = []
                send_dislikes_ids = rec.relation_all_ids.filtered(
                    lambda x: x.this_partner_id == rec and
                              x.tab_id.code == 'send_dislikes'
                )

                for send_dislikes_id in send_dislikes_ids:
                    block_partner_ids.append(send_dislikes_id.other_partner_id.id)


                unmatches_ids = rec.relation_all_ids.filtered(
                    lambda x: x.this_partner_id == rec and
                              x.tab_id.code == 'unmatches'
                )

                for unmatches_id in unmatches_ids:
                    block_partner_ids.append(unmatches_id.other_partner_id.id)
                    
                matches_ids = rec.relation_all_ids.filtered(
                    lambda x: x.this_partner_id == rec and
                              x.tab_id.code == 'matches'
                )

                for matches_id in matches_ids:
                    block_partner_ids.append(matches_id.other_partner_id.id)
                    
                send_likes_ids = rec.relation_all_ids.filtered(
                    lambda x: x.this_partner_id == rec and
                              x.tab_id.code == 'send_likes'
                )

                for send_likes_id in send_likes_ids:
                    block_partner_ids.append(send_likes_id.other_partner_id.id)

                genres = []
                if rec.interest_male_gender:
                    genres.append('male')
                if rec.interest_female_gender:
                    genres.append('female')
                if rec.interest_other_genres:
                    genres.append('other')

                friend_ids = rec.env['res.partner'].sudo(). \
                    search([
                        '&', '&', '&', '&',
                        ('id', '!=', rec.id),
                        ('id', 'not in', block_partner_ids),
                        ('active', '=', True),
                        ('gender', 'in', genres),
                        ('is_company', '=', False),
                        ('age', '>=', rec.referred_friend_min_age),
                        ('age', '<=', rec.referred_friend_max_age),
                    ])

                if friend_ids:
                    friend_ids = friend_ids.filtered(
                        (lambda x: haversine(x, rec) <=
                                   rec.referred_friend_max_distance)
                    )

                if friend_ids:
                    friend_ids = friend_ids.filtered(
                        (lambda x: set(x.music_genre_ids).
                         intersection(rec.music_genre_ids))
                    )

                rec.referred_friend_ids = friend_ids
                # Todo: esta checagem deve ocorrer quando houver alguma
                #  ateração nas relações entre parceiros
                rec._compute_match_relation()

    @api.multi
    def action_view_referred_friend(self):
        action = self.env.ref(
            "contacts.action_contacts").read()[0]
        action["domain"] = [("id", "in", self.referred_friend_ids.ids)]
        return action

class ResPartnerImage(models.Model):
    _name = 'res.partner.image'
    _description = 'Partner Image'

    name = fields.Char('Name')
    image = fields.Binary('Image', attachment=True)
    res_partner_id = fields.Many2one('res.partner', 'Related partner', copy=True)
