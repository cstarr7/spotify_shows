# -*- coding: utf-8 -*-
# @Author: Charles Starr
# @Date:   2016-07-10 12:49:18
# @Last Modified by:   Charles Starr
# @Last Modified time: 2016-08-14 13:06:12

import user_classes
import helpers
from text_menu import Text_Menu


def main():
	db_filename = 'no_shows.sqlite'
	menu = Text_Menu(db_filename)
	menu.database_options()
	user = menu.user_options()
	calendar = user_classes.Event_Calendar(db_filename)
	common_artists = user.dp_common_artists(calendar.artist_set())
	events = calendar.events_by_artist(common_artists)
	user.send_email(events)

main()