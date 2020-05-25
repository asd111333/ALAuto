import enum


class UtilConsts(object):

    def __new__(cls):
        return cls

    class ScreenCapMode(enum.Enum):
        SCREENCAP_PNG = enum.auto()
        SCREENCAP_RAW = enum.auto()
        ASCREENCAP = enum.auto()


class CombatConsts(object):

    def __new__(cls):
        return cls

    class Filters:
        # filter option name = filter function name
        SUPPLY_FIRST = 'supply_first_filter'
        SIREN_FIRST = 'siren_first_filter'
        ENEMY_ONLY = 'enemy_only_filter'
