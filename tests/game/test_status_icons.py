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

from horizons.command.building import Build
from horizons.command.production import ToggleActive
from horizons.world.production.producer import Producer
from horizons.world.component.storagecomponent import StorageComponent
from horizons.constants import BUILDINGS, RES
from horizons.world.status import SettlerUnhappyStatus, DecommissionedStatus, ProductivityLowStatus, InventoryFullStatus
from mock import Mock

from tests.game import settle, game_test

@game_test
def test_productivity_low(session, player):
	settlement, island = settle(session)

	lj = Build(BUILDINGS.LUMBERJACK_CLASS, 30, 30, island, settlement=settlement)(player)

	# precondition
	assert abs(lj.get_component(Producer).capacity_utilisation) < 0.0001

	# must be low
	icons = lj.get_status_icons()
	assert len(icons) == 1
	assert isinstance(icons[0], ProductivityLowStatus)

	# set capac util to 100, can't change the property directly
	get_comp_orig = lj.get_component
	# change get_component to give our fake obj, whose dict is copied from the original producer
	def _get_comp(x):
		if x == Producer:
			orig_comp = get_comp_orig(Producer)
			comp = Mock()
			comp.__dict__ = orig_comp.__dict__
			comp.capacity_utilisation = 1.0
			return comp
		else:
			return get_comp_orig(x)

	lj.get_component = _get_comp

	assert abs(lj.get_component(Producer).capacity_utilisation) > 0.9999
	icons = lj.get_status_icons()
	assert len(icons) == 0

@game_test
def test_settler_unhappy(session, player):
	settlement, island = settle(session)

	settler = Build(BUILDINGS.RESIDENTIAL_CLASS, 30, 30, island, settlement=settlement)(player)

	# certainly not unhappy
	assert settler.happiness > 0.45
	icons = settler.get_status_icons()
	assert len(icons) == 0

	# make it unhappy
	settler.get_component(StorageComponent).inventory.alter(RES.HAPPINESS_ID, -settler.happiness)
	assert settler.happiness < 0.1
	icons = settler.get_status_icons()
	assert len(icons) == 1
	assert isinstance(icons[0], SettlerUnhappyStatus)



@game_test
def test_decommissioned(session, player):
	settlement, island = settle(session)

	lj = Build(BUILDINGS.LUMBERJACK_CLASS, 30, 30, island, settlement=settlement)(player)

	icons = lj.get_status_icons()
	assert not any( isinstance(icon, DecommissionedStatus) for icon in icons )

	ToggleActive(lj)(player)

	icons = lj.get_status_icons()
	assert any( isinstance(icon, DecommissionedStatus) for icon in icons )



@game_test
def test_inventory_full(session, player):
	settlement, island = settle(session)

	lj = Build(BUILDINGS.LUMBERJACK_CLASS, 30, 30, island, settlement=settlement)(player)

	icons = lj.get_status_icons()
	assert not any( isinstance(icon, InventoryFullStatus) for icon in icons )

	inv = lj.get_component(StorageComponent).inventory
	res = RES.BOARDS_ID
	inv.alter(res, inv.get_free_space_for( res ) )

	icons = lj.get_status_icons()
	assert any( isinstance(icon, InventoryFullStatus) for icon in icons )




