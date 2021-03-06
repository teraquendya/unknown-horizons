# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

__all__ = ['animal','nature','ship','unit']

import logging

from fife import fife

import horizons.main
from horizons.util import ActionSetLoader, Callback
from horizons.world.ingametype import IngameType

class UnitClass(IngameType):

	log = logging.getLogger('world.units')
	basepackage = 'horizons.world.units.'
	classstring = 'Unit['

	_action_load_callbacks = {}

	def __init__(self, id, yaml_data):
		"""
		@param id: unit id.
		"""
		super(UnitClass, self).__init__(id, yaml_data)

	@classmethod
	def ensure_action_loaded(cls, action_set_id, action):
		"""Called when an action is actually needed, makes sure it is loaded then"""
		try:
			# load for all instances, don't care for separating again per object
			for i in cls._action_load_callbacks[action_set_id][action]:
				i()
			del cls._action_load_callbacks[action_set_id][action]
		except KeyError:
			pass

	def _loadObject(cls):
		"""Loads the object with all animations.
		"""
		cls.log.debug('Loading unit %s', cls.id)
		try:
			cls._real_object = horizons.main.fife.engine.getModel().createObject(str(cls.id), 'unit')
		except RuntimeError:
			cls.log.debug('Already loaded unit %s', cls.id)
			cls._real_object = horizons.main.fife.engine.getModel().getObject(str(cls.id), 'unit')
			return
		cls._real_object.setPather(horizons.main.fife.engine.getModel().getPather('RoutePather'))
		cls._real_object.setBlocking(False)
		cls._real_object.setStatic(False)
		action_sets = ActionSetLoader.get_sets()
		# create load callbacks to be called when the actions are needed

		def do_load(action_set_id, action_id):
			action = cls._real_object.createAction(action_id+"_"+str(action_set_id))
			fife.ActionVisual.create(action)
			for rotation in action_sets[action_set_id][action_id].iterkeys():
				anim = horizons.main.fife.animationloader.loadResource( \
					str(action_set_id)+"+"+str(action_id)+"+"+ \
					str(rotation) + ':shift:center+0,bottom+8')
				action.get2dGfxVisual().addAnimation(int(rotation), anim)
				action.setDuration(anim.getDuration())

		#{ action_set : { action_id : [ load0, load1, ..., loadn ]}}
		# (loadi are load functions of objects, there can be many per as_id and action)
		for action_set_id in cls.action_sets:
			if not action_set_id in cls._action_load_callbacks:
				cls._action_load_callbacks[action_set_id] = {}
			for action_id in action_sets[action_set_id].iterkeys():
				if not action_id in cls._action_load_callbacks[action_set_id]:
					cls._action_load_callbacks[action_set_id][action_id] = []
				cls._action_load_callbacks[action_set_id][action_id].append(
				  Callback(do_load, action_set_id, action_id))
