# -*- coding: utf-8 -*-

from robogame_engine.utils import CanLogging


class CargoBox(CanLogging):
    """Класс кузова для перевозки и хранения элериума"""
    __load_speed = 1
    __payload = 0
    __max_payload = 0
    # TODO подумать держать __cargo_source и __cargo_target, без стейта,
    # TODO тогда можно трансферить елериум - сразу и загружать и разгружать
    __cargo_jack = None
    __cargo_state = 'hold'

    def __init__(self, initial_cargo, maximum_cargo):
        self.__payload = initial_cargo
        if maximum_cargo <= 0:
            raise Exception("max_payload must be positive!")
        self.__max_payload = maximum_cargo

    @property
    def payload(self):
        return self.__payload

    @property
    def fullness(self):
        return self.__payload / float(self.__max_payload)

    @property
    def is_empty(self):
        return self.__payload <= 0

    @property
    def is_full(self):
        return self.__payload >= self.__max_payload

    @property
    def free_space(self):
        return self.__max_payload - self.__payload

    def load_from(self, source):
        if isinstance(source, CargoBox):
            self.__cargo_jack = source
            self.__cargo_state = 'loading'
        else:
            raise Exception('Source for CargoBox can be only CargoBox!')

    def unload_to(self, target):
        if isinstance(target, CargoBox):
            self.__cargo_jack = target
            self.__cargo_state = 'unloading'
        else:
            raise Exception('Target for CargoBox can be only CargoBox!')

    def at_load_distance(self, target):
        # TODO можно переопределить - дыра?
        raise NotImplementedError()

    def on_load_complete(self):
        pass

    def on_unload_complete(self):
        pass

    def _update(self):
        if self.__cargo_jack is None or self.__cargo_state == 'hold':
            return
        if not self.at_load_distance(self.__cargo_jack):
            self.__stop_transfer()
        elif self.__cargo_state == 'unloading':
            if min(self.__payload, self.__cargo_jack.free_space) == 0:
                self.__end_exchange(event=self.on_unload_complete)
            else:
                batch = self.__get_cargo()
                if batch:
                    self.__cargo_jack.__put_cagro(batch)
                else:
                    self.__end_exchange(event=self.on_unload_complete)
        elif self.__cargo_state == 'loading':
            if min(self.free_space, self.__cargo_jack.__payload) == 0:
                self.__end_exchange(event=self.on_load_complete)
            else:
                batch = self.__cargo_jack.__get_cargo()
                if batch:
                    self.__put_cagro(batch)
                else:
                    self.__end_exchange(event=self.on_load_complete)

    def __end_exchange(self, event):
        self.__cargo_jack = None
        self.__cargo_state = 'hold'
        try:
            event()
        except Exception as exc:
            self.error("Exception at {} event {} handle: {}".format(self, event, exc))

    def __stop_transfer(self):
        self.__cargo_jack = None
        self.__cargo_state = 'hold'

    def __get_cargo(self):
        batch = min(self.__payload, self.__cargo_jack.free_space, self.__load_speed)
        self.__payload -= batch
        return batch

    def __put_cagro(self, value):
        part = min(value, self.__max_payload - self.__payload)
        self.__payload += part



