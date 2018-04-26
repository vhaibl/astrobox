# -*- coding: utf-8 -*-
from __future__ import print_function

import math
import random

from robogame_engine import GameObject, Scene
from robogame_engine.constants import ROTATE_FLIP_BOTH, ROTATE_TURNING
from robogame_engine.geometry import Point
from robogame_engine.states import StateMoving
from robogame_engine.theme import theme

from .cargo_box import CargoBox


class Dron(GameObject):
    __MAX_ELERIUM = 100
    rotate_mode = ROTATE_TURNING
    radius = 44
    _part_of_team = True
    __my_mathership = None
    _dead = False

    def __init__(self):
        super(Dron, self).__init__(pos=self.my_mathership.coord)
        self.cargo = CargoBox(initial_cargo=0, maximum_cargo=self.__MAX_ELERIUM)
        self._objects_holder = self._scene
        self.__health = theme.MAX_HEALTH

    @property
    def sprite_filename(self):
        return 'dron_{}.png'.format(self.team)

    @property
    def my_mathership(self):
        if self.__my_mathership is None:
            try:
                self.__my_mathership = self._scene.get_beehive(team=self.team)
            except IndexError:
                raise Exception("No mathership for {} - check matherships_count!".format(self.__class__.__name__))
        return self.__my_mathership

    @property
    def meter_1(self):
        return self.cargo.meter

    @property
    def meter_2(self):
        return float(self.__health) / theme.MAX_HEALTH

    @property
    def is_alive(self):
        return self.__health > 0

    def game_step(self):
        super(Dron, self).game_step()
        if self.is_alive and self.__health < theme.MAX_HEALTH:
            self.__health += theme.HEALTH_TOP_UP_SPEED
        self._update(is_moving=isinstance(self.state, StateMoving))

    def on_stop_at_target(self, target):
        for flower in self.flowers:
            if flower.at_load_distance(target):
                self.on_stop_at_flower(flower)
                return
        else:
            for bh in self.beehives:
                if bh.at_load_distance(target):
                    self.on_stop_at_beehive(bh)
                    return
        self.on_stop_at_point(target)

    def on_stop_at_point(self, target):
        pass

    def on_stop_at_asteriod(self, asteriod):
        pass

    def on_stop_at_mathership(self, mathership):
        pass

    # def sting(self, other):
    #     """
    #     Укусить другую пчелу
    #     """
    #     if self._dead:
    #         return
    #     if isinstance(other, Bee):
    #         other.stung(self, self.__reduce_health)
    #
    # def stung(self, other, kickback):
    #     """
    #     Принять укус, если кусающий близко.
    #     Здоровье кусающего тоже уменьшается через kickback
    #     """
    #     if self.distance_to(other) <= self.radius:
    #         try:
    #             kickback()
    #             self.__reduce_health()
    #         except TypeError:
    #             # flashback не может быть вызвана
    #             pass

    # def __reduce_health(self):
    #     if self.distance_to(self.my_beehive) > theme.BEEHIVE_SAFE_DISTANCE:
    #         self._health -= theme.STING_POWER
    #         if self._health < 0:
    #             self.__die()
    #
    # def __die(self):
    #     self.rotate_mode = ROTATE_FLIP_BOTH
    #     self.move_at(Point(x=self.x + random.randint(-20, 20), y=40 + random.randint(-10, 20)))
    #     self._dead = True

    def move_at(self, target, speed=None):
        if not self.is_alive:
            return
        super(Dron, self).move_at(target, speed)

    def turn_to(self, target):
        if not self.is_alive:
            return
        super(Dron, self).turn_to(target)

    def load_elerium_from(self, source):
        if hasattr(source, 'cargo_box'):
            self.cargo.load_from(source=source.cargo_box)
        else:
            raise Exception("Source object {} hasn't cargo_box!".format(source))

    def unload_elerium_to(self, target):
        if hasattr(target, 'cargo_box'):
            self.cargo.load_from(source=target.cargo_box)
        else:
            raise Exception("Target object {} hasn't cargo_box!".format(target))



class Asteriod(GameObject):
    radius = 50
    selectable = False
    _MIN_HONEY = 100
    _MAX_HONEY = 200
    counter_attrs = dict(size=16, position=(43, 45), color=(128, 128, 128))

    def __init__(self, pos, max_honey=None):
        super(Asteriod, self).__init__(pos=pos)
        if max_honey is None:
            max_honey = random.randint(self._MIN_HONEY, self._MAX_HONEY)
        self.set_inital_honey(loaded=max_honey, maximum=max_honey)

    def update(self):
        pass

    @property
    def counter(self):
        return self.honey


class Mathership(GameObject):
    radius = 75
    selectable = False
    counter_attrs = dict(size=22, position=(60, 92), color=(255, 255, 0))

    def __init__(self, pos, max_honey):
        super(Mathership, self).__init__(pos=pos)
        self.set_inital_honey(loaded=0, maximum=max_honey)

    @property
    def counter(self):
        return self.honey


class Rect(object):

    def __init__(self, x=0, y=0, w=10, h=10):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def reduce(self, dw=0, dh=0):
        self.w -= dw
        self.h -= dh

    def shift(self, dx=0, dy=0):
        self.x += dx
        self.y += dy

    def __str__(self):
        return "{}x{} ({}, {})".format(self.w, self.h, self.x, self.y)


class StarField(Scene):
    check_collisions = False
    _FLOWER_JITTER = 0.7
    _HONEY_SPEED_FACTOR = 0.02
    __beehives = []

    def prepare(self, flowers_count=5, beehives_count=1):
        self._place_flowers_and_beehives(
            flowers_count=flowers_count,
            beehives_count=beehives_count,
        )
        self._objects_holder = self
        honey_speed = int(theme.MAX_SPEED * self._HONEY_SPEED_FACTOR)
        if honey_speed < 1:
            honey_speed = 1

    def _place_flowers_and_beehives(self, flowers_count, beehives_count):
        if beehives_count > theme.TEAMS_COUNT:
            raise Exception('Only {} beehives!'.format(theme.TEAMS_COUNT))

        field = Rect(w=theme.FIELD_WIDTH, h=theme.FIELD_HEIGHT)
        field.reduce(dw=BeeHive.radius * 2, dh=BeeHive.radius * 2)
        if beehives_count >= 2:
            field.reduce(dw=BeeHive.radius * 2)
        if beehives_count >= 3:
            field.reduce(dh=BeeHive.radius * 2)
        if field.w < Flower.radius or field.h < Flower.radius:
            raise Exception("Too little field...")
        if theme.DEBUG:
            print("Initial field", field)

        cells_in_width = int(math.ceil(math.sqrt(float(field.w) / field.h * flowers_count)))
        cells_in_height = int(math.ceil(float(flowers_count) / cells_in_width))
        cells_count = cells_in_height * cells_in_width
        if theme.DEBUG:
            print("Cells count", cells_count, cells_in_width, cells_in_height)
        if cells_count < flowers_count:
            print(u"Ну я не знаю...")

        cell = Rect(w=field.w / cells_in_width, h=field.h / cells_in_height)

        if theme.DEBUG:
            print("Adjusted cell", cell)

        cell_numbers = [i for i in range(cells_count)]

        jit_box = Rect(w=int(cell.w * self._FLOWER_JITTER), h=int(cell.h * self._FLOWER_JITTER))
        jit_box.shift(dx=(cell.w - jit_box.w) // 2, dy=(cell.h - jit_box.h) // 2)
        if theme.DEBUG:
            print("Jit box", jit_box)

        field.w = cells_in_width * cell.w + jit_box.w
        field.h = cells_in_height * cell.h + jit_box.h
        if theme.DEBUG:
            print("Adjusted field", field)

        field.x = BeeHive.radius * 2
        field.y = BeeHive.radius * 2
        if theme.DEBUG:
            print("Shifted field", field)

        max_honey = 0
        i = 0
        while i < flowers_count:
            cell_number = random.choice(cell_numbers)
            cell_numbers.remove(cell_number)
            cell.x = (cell_number % cells_in_width) * cell.w
            cell.y = (cell_number // cells_in_width) * cell.h
            dx = random.randint(0, jit_box.w)
            dy = random.randint(0, jit_box.h)
            pos = Point(field.x + cell.x + dx, field.y + cell.y + dy)
            flower = Flower(pos)
            max_honey += flower.honey
            i += 1
        max_honey /= float(beehives_count)
        max_honey = int(round((max_honey / 1000.0) * 1.3)) * 1000
        if max_honey < 1000:
            max_honey = 1000
        for team in range(beehives_count):
            if team == 0:
                pos = Point(90, 75)
            elif team == 1:
                pos = Point(theme.FIELD_WIDTH - 90, 75)
            elif team == 2:
                pos = Point(90, theme.FIELD_HEIGHT - 75)
            else:
                pos = Point(theme.FIELD_WIDTH - 90, theme.FIELD_HEIGHT - 75)
            beehive = BeeHive(pos=pos, max_honey=max_honey)
            self.__beehives.append(beehive)

    def get_beehive(self, team):
        return self.__beehives[team - 1]



