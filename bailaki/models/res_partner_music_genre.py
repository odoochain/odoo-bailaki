# Copyright 2020 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartnerMusicGenre(models.Model):

    _name = 'res.partner.music.genre'
    _description = 'Res Partner Music Genre'  # TODO

    name = fields.Char()
