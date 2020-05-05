import math
import string
import random
from datetime import datetime, timedelta
from util.logger import Logger
from util.utils import Region, Utils
import numpy as np
from util.homg_trans import HomographyTransform as Homg
import util.homg_trans_consts as HomgConsts 

class CombatModule(object):

    def __init__(self, config, stats, retirement_module, enhancement_module):
        """Initializes the Combat module.

        Args:
            config (Config): ALAuto Config instance.
            stats (Stats): ALAuto Stats instance.
            retirement_module (RetirementModule): ALAuto RetirementModule instance.
            enhancement_module (EnhancementModule): ALAuto EnhancementModule instance.
        """
        self.enabled = True
        self.config = config
        self.stats = stats
        self.retirement_module = retirement_module
        self.enhancement_module = enhancement_module
        self.chapter_map = self.config.combat['map']
        Utils.small_boss_icon = config.combat['small_boss_icon']
        if config.combat['small_boss_icon']:
            self.use_small_boss_icon = True
        else:
            self.use_small_boss_icon = False
        self.exit = 0
        self.combats_done = 0
        self.swipe_dir_idx = 0
        self.boss_fleet_found = False
        self.sea_map = None
        self.boss_defeated = False

        self.mob_fleet_no = None
        self.boss_fleet_no = None
        self.switch_fleet_after_combats = None

        self.force_fleet_no = None
        self.last_visited_idx = None
        self.homg = None

        self.kills_count = 0
        self.kills_before_boss = {
            '1-1': 1, '1-2': 2, '1-3': 2, '1-4': 3,
            '2-1': 2, '2-2': 3, '2-3': 3, '2-4': 3,
            '3-1': 3, '3-2': 3, '3-3': 3, '3-4': 3,
            '4-1': 3, '4-2': 3, '4-3': 3, '4-4': 4,
            '5-1': 4, '5-2': 4, '5-3': 4, '5-4': 4,
            '6-1': 4, '6-2': 4, '6-3': 4, '6-4': 5,
            '7-1': 5, '7-2': 5, '7-3': 5, '7-4': 5,
            '8-1': 4, '8-2': 4, '8-3': 4, '8-4': 4,
            '9-1': 5, '9-2': 5, '9-3': 5, '9-4': 5,
            '10-1': 6, '10-2': 6, '10-3': 6, '10-4': 6,
            '11-1': 6, '11-2': 6, '11-3': 6, '11-4': 6,
            '12-1': 6, '12-2': 6, '12-3': 6, '12-4': 6,
            '13-1': 6, '13-2': 6, '13-3': 6, '13-4': 7
        }
        if self.chapter_map not in self.kills_before_boss:
            # check if current map is present in the dictionary and if it isn't,
            # a new entry is added with kills_before_boss value
            self.kills_before_boss[self.chapter_map] = self.config.combat['kills_before_boss']
        elif self.config.combat['kills_before_boss'] != 0:
            # updates default value with the one provided by the user
            self.kills_before_boss[self.chapter_map] = self.config.combat['kills_before_boss']

        self.region = {
            'fleet_lock': Region(1790, 750, 130, 30),
            'open_strategy_menu': Region(1797, 617, 105, 90),
            'disable_subs_hunting_radius': Region(1655, 615, 108, 108),
            'close_strategy_menu': Region(1590, 615, 40, 105),
            'menu_button_battle': Region(1517, 442, 209, 206),
            'map_summary_go': Region(1289, 743, 280, 79),
            'fleet_menu_go': Region(1485, 872, 270, 74),
            'combat_ambush_evade': Region(1493, 682, 208, 56),
            'combat_com_confirm': Region(848, 740, 224, 56),
            'combat_end_confirm': Region(1520, 963, 216, 58),
            'combat_dismiss_surface_fleet_summary': Region(790, 950, 250, 65),
            'menu_combat_start': Region(1578, 921, 270, 70),
            'tap_to_continue': Region(661, 840, 598, 203),
            'close_info_dialog': Region(1326, 274, 35, 35),
            'dismiss_ship_drop': Region(1228, 103, 692, 735),
            'retreat_button': Region(1130, 985, 243, 60),
            'dismiss_commission_dialog': Region(1065, 732, 235, 68),
            'normal_mode_button': Region(88, 990, 80, 40),
            'map_nav_right': Region(1831, 547, 26, 26),
            'map_nav_left': Region(65, 547, 26, 26),
            'event_button': Region(1770, 250, 75, 75),
            'lock_ship_button': Region(1086, 739, 200, 55),
            'clear_second_fleet': Region(1690, 473, 40, 40),
            'button_switch_fleet': Region(1430, 985, 240, 60),
            'menu_nav_back': Region(54, 57, 67, 67),
            'fleet_no': Region(220, 110, 125, 45)
        }

        self.swipe_dir_idx = 0
        self.swipe_coord = [
            (960, 240, 960, 940, 600),
            (1560, 540, 260, 540, 600),
            (960, 940, 960, 240, 600),
            (260, 540, 1560, 540, 600)
        ]

    def combat_logic_wrapper(self):
        """Method that fires off the necessary child methods that encapsulates
        the entire action of sortieing combat fleets and resolving combat.

        Returns:
            int: 1 if boss was defeated, 2 if successfully retreated after the specified
                number of fights, 3 if morale is too low, 4 if dock is full and unable to
                free it and 5 if fleet was defeated.
        """
        self.exit = 0
        self.start_time = datetime.now()
        self.combats_done = 0
        self.kills_count = 0
        self.swipe_dir_idx = 0
        self.boss_fleet_found = False
        self.sea_map = None
        self.boss_defeated = False
        self.mob_fleet_no = 1
        self.boss_fleet_no = 2
        self.switch_fleet_after_combats = 5
        self.force_fleet_no = None
        self.last_visited_idx = None
        self.homg = Homg()
        self.homg.init_homg_vars()
        
        # enhancecement and retirement flags
        enhancement_failed = False
        retirement_failed = False

        # get to map

        map_region = self.reach_map()


        while True:
            Utils.update_screen()
            self.store_screen_to_homg()

            if self.exit == 1 or self.exit == 2:
                self.stats.increment_combat_done()
                time_passed = datetime.now() - self.start_time
                if self.stats.combat_done % self.config.combat['retire_cycle'] == 0 or ((self.config.commissions['enabled'] or \
                    self.config.dorm['enabled'] or self.config.academy['enabled']) and time_passed.total_seconds() > 3600) or \
                        not Utils.check_oil(self.config.combat['oil_limit']):
                        break
                else:
                    self.exit = 0
                    break
            if self.exit > 2:
                self.stats.increment_combat_attempted()
                break
            if Utils.find("combat/button_go"):
                Logger.log_debug("Found map summary go button.")
                Utils.touch_randomly(self.region["map_summary_go"])
                Utils.wait_update_screen()
                self.store_screen_to_homg()
            if Utils.find("combat/menu_fleet") and (lambda x:x > 414 and x < 584)(Utils.find("combat/menu_fleet").y) and not self.config.combat['boss_fleet']:
                if not self.chapter_map[0].isdigit() and string.ascii_uppercase.index(self.chapter_map[2:3]) < 1 or self.chapter_map[0].isdigit():
                    Logger.log_msg("Removing second fleet from fleet selection.")
                    Utils.touch_randomly(self.region["clear_second_fleet"])
            if Utils.find("combat/menu_select_fleet"):
                Logger.log_debug("Found fleet select go button.")
                Utils.touch_randomly(self.region["fleet_menu_go"])
                Utils.wait_update_screen(2)
                self.store_screen_to_homg()
            if Utils.find("combat/button_retreat"):
                Logger.log_debug("Found retreat button, starting clear function.")
                if not self.clear_map():
                    self.stats.increment_combat_attempted()
                    break
                Utils.wait_update_screen()
                self.store_screen_to_homg()
            if Utils.find("menu/button_sort"):
                if self.config.enhancement['enabled'] and not enhancement_failed:
                    if not self.enhancement_module.enhancement_logic_wrapper(forced=True):
                        enhancement_failed = True
                    Utils.script_sleep(1)
                    Utils.touch_randomly(map_region)
                    continue
                elif self.config.retirement['enabled'] and not retirement_failed:
                    if not self.retirement_module.retirement_logic_wrapper(forced=True):
                        retirement_failed = True
                    else:
                        # reset enhancement flag
                        enhancement_failed = False
                    Utils.script_sleep(1)
                    Utils.touch_randomly(map_region)
                    continue
                else:
                    Utils.touch_randomly(self.region['close_info_dialog'])
                    self.exit = 4
                    break
            if Utils.find("combat/alert_morale_low"):
                if self.config.combat['ignore_morale']:
                    Utils.find_and_touch("menu/button_confirm")
                else:
                    Utils.touch_randomly(self.region['close_info_dialog'])
                    self.exit = 3
                    break
            if Utils.find("menu/button_confirm"):
                Logger.log_msg("Found commission info message.")
                Utils.touch_randomly(self.region["combat_com_confirm"])
            
        Utils.script_sleep(1)
        Utils.menu_navigate("menu/button_battle")

        return self.exit

    def reach_map(self):
        """
        Method which returns the map region for the stage set in the configuration file.
        If the map isn't found, it navigates the map selection menu to get to the world where the specified map is located.
        Only works with standard maps up to worlds 13 and some event maps.
        Also checks if hard mode is enabled, and if it's legit to keep it so (event maps C and D).
        If nothing is found even after menu navigation, it stops the bot workflow until the user moves to the right 
        screen or the map asset is substituted with the right one.

        Returns:
            (Region): the map region of the selected stage.
        """
        Utils.wait_update_screen()
        # get to map selection menu
        if Utils.find("menu/button_battle"):
            Logger.log_debug("Found menu battle button.")
            Utils.touch_randomly(self.region["menu_button_battle"])
            Utils.wait_update_screen(4)

        if Utils.find('combat/button_retreat'):
            return

        # correct map mode 
        if not self.chapter_map[0].isdigit():
            letter = self.chapter_map[2]
            event_maps = ['A', 'B', 'S', 'C', 'D']

            Utils.touch_randomly(self.region['event_button'])
            Utils.wait_update_screen(1)

            if event_maps.index(letter) < 3 and Utils.find("menu/button_normal_mode", 0.8) or \
               event_maps.index(letter) > 2 and not Utils.find("menu/button_normal_mode", 0.8):
                Utils.touch_randomly(self.region['normal_mode_button'])
                Utils.wait_update_screen(1)
        else:
            if Utils.find("menu/button_normal_mode"):
                Logger.log_debug("Disabling hard mode.")
                Utils.touch_randomly(self.region['normal_mode_button'])
                Utils.wait_update_screen(1)
        
        map_region = Utils.find('maps/map_{}'.format(self.chapter_map), 0.99)
        if map_region != None:
            Logger.log_msg("Found specified map.")
            Utils.touch_randomly(map_region)
            return map_region
        else:
            # navigate map selection menu
            if not self.chapter_map[0].isdigit():
                if (self.chapter_map[2] == 'A' or self.chapter_map[2] == 'C') and \
                    (Utils.find('maps/map_E-B1', 0.99) or Utils.find('maps/map_E-D1', 0.99)):
                    Utils.touch_randomly(self.region['map_nav_left'])
                    Logger.log_debug("Swiping to the left")
                elif (self.chapter_map[2] == 'B' or self.chapter_map[2] == 'D') and \
                    (Utils.find('maps/map_E-A1', 0.99) or Utils.find('maps/map_E-C1', 0.99)):
                    Utils.touch_randomly(self.region['map_nav_right'])
                    Logger.log_debug("Swiping to the right")
            else:
                _map = 0
                for x in range(1, 14):
                    if Utils.find("maps/map_{}-1".format(x), 0.99):
                        _map = x
                        break
                if _map != 0:
                    taps = int(self.chapter_map.split("-")[0]) - _map
                    for x in range(0, abs(taps)):
                        if taps >= 1:
                            Utils.touch_randomly(self.region['map_nav_right'])
                            Logger.log_debug("Swiping to the right")
                            Utils.script_sleep()
                        else:
                            Utils.touch_randomly(self.region['map_nav_left'])
                            Logger.log_debug("Swiping to the left")
                            Utils.script_sleep()
        
        Utils.wait_update_screen()
        map_region = Utils.find('maps/map_{}'.format(self.chapter_map), 0.99)
        if map_region == None:
            Logger.log_error("Cannot find the specified map, please move to the world where it's located.")
        while map_region == None:
            map_region = Utils.find('maps/map_{}'.format(self.chapter_map), 0.99)
            Utils.wait_update_screen(1)

        Logger.log_msg("Found specified map.")
        Utils.touch_randomly(map_region)

    def battle_handler(self, boss=False):
        Logger.log_msg("Starting combat.")

        # enhancecement and retirement flags
        enhancement_failed = False
        retirement_failed = False
        while not (Utils.find("combat/menu_loading", 0.8)):
            Utils.update_screen()
            self.store_screen_to_homg()
            if Utils.find("menu/button_sort"):
                if self.config.enhancement['enabled'] and not enhancement_failed:
                    if not self.enhancement_module.enhancement_logic_wrapper(forced=True):
                        enhancement_failed = True
                elif self.config.retirement['enabled'] and not retirement_failed:
                    if not self.retirement_module.retirement_logic_wrapper(forced=True):
                        retirement_failed = True
                else:
                    self.retreat_handler()
                    return False
            elif Utils.find("combat/alert_morale_low"):
                if self.config.combat['ignore_morale']:
                    Utils.find_and_touch("menu/button_confirm")
                else:
                    self.retreat_handler()
                    return False
            elif Utils.find("combat/combat_pause", 0.7):
                Logger.log_warning("Loading screen was not found but combat pause is present, assuming combat is initiated normally.")
                break
            else:
                Utils.touch_randomly(self.region["menu_combat_start"])
                Utils.script_sleep(1)

        Utils.script_sleep(4)

        # flags
        in_battle = True
        items_received = False
        locked_ship = False
        confirmed_fight = False
        defeat = False
        confirmed_fleet_switch = False
        while True:
            Utils.update_screen()
            self.store_screen_to_homg()

            if in_battle and Utils.find("combat/combat_pause", 0.7):
                Logger.log_debug("In battle.")
                Utils.wait_till_stable(max_time=2)
                continue
            if not items_received:
                if Utils.find("combat/menu_touch2continue"):
                    Logger.log_debug("Combat ended: tap to continue")
                    Utils.touch_randomly(self.region['tap_to_continue'])
                    in_battle = False
                    continue
                if Utils.find("menu/item_found"):
                    Logger.log_debug("Combat ended: items received screen")
                    Utils.touch_randomly(self.region['tap_to_continue'])
                    Utils.wait_till_stable(max_time=1)
                    continue
                if (not locked_ship) and Utils.find("combat/alert_lock"):
                    Logger.log_msg("Locking received ship.")
                    Utils.touch_randomly(self.region['lock_ship_button'])
                    locked_ship = True
                    continue
                if Utils.find("menu/drop_elite"):
                    Logger.log_msg("Received ELITE ship as drop.")
                    Utils.touch_randomly(self.region['dismiss_ship_drop'])
                    Utils.wait_till_stable(max_time=2)
                    continue
                elif Utils.find("menu/drop_rare"):
                    Logger.log_msg("Received new RARE ship as drop.")
                    Utils.touch_randomly(self.region['dismiss_ship_drop'])
                    Utils.wait_till_stable(max_time=2)
                    continue                
                elif Utils.find("menu/drop_ssr"):
                    Logger.log_msg("Received SSR ship as drop.")
                    Utils.touch_randomly(self.region['dismiss_ship_drop'])
                    Utils.wait_till_stable(max_time=2)
                    continue
                elif Utils.find("menu/drop_common"):
                    Logger.log_msg("Received new COMMON ship as drop.")
                    Utils.touch_randomly(self.region['dismiss_ship_drop'])
                    Utils.wait_till_stable(max_time=2)
                    continue
            if not in_battle:
                if (not confirmed_fight) and Utils.find("combat/button_confirm"):
                    Logger.log_msg("Combat ended.")
                    items_received = True
                    confirmed_fight = True
                    Utils.touch_randomly(self.region["combat_end_confirm"])
                    if boss:
                        return True
                    Utils.wait_till_stable(max_time=3.0)
                    #Utils.wait_update_screen(3)
                    self.store_screen_to_homg()
                if (not confirmed_fight) and Utils.find("combat/commander"):
                    items_received = True
                    # prevents fleet with submarines from getting stuck at combat end screen
                    Utils.touch_randomly(self.region["combat_dismiss_surface_fleet_summary"])
                    continue
                if defeat and not confirmed_fleet_switch:
                    if Utils.find("combat/alert_unable_battle"):
                        Utils.touch_randomly(self.region['close_info_dialog'])
                        Utils.wait_till_stable(max_time=3.0)
                        #Utils.script_sleep(3)
                        self.exit = 5
                        return False
                    if Utils.find("combat/alert_fleet_cannot_be_formed"):
                        # fleet will be automatically switched
                        Utils.touch_randomly(self.region['close_info_dialog'])
                        confirmed_fleet_switch = True
                        Utils.wait_till_stable(max_time=3.0)
                        #Utils.script_sleep(3)
                        continue
                    else:
                        # flagship sunk, but part of backline still remains
                        # proceed to retreat
                        Utils.wait_till_stable(max_time=3.0)
                        #Utils.script_sleep(3)
                        self.exit = 5
                        return False
                if confirmed_fight and Utils.find("menu/button_confirm"):
                    Logger.log_msg("Found commission info message.")
                    Utils.touch_randomly(self.region["combat_com_confirm"])
                    continue
                if confirmed_fight and Utils.find("combat/button_retreat"):
                    #Utils.touch_randomly(self.region["hide_strat_menu"])
                    if confirmed_fleet_switch:
                        # if fleet was defeated and it has now been switched
                        return False
                    else:
                        # fleet won the fight
                        self.combats_done += 1
                        self.kills_count += 1
                        """
                        if self.kills_count >= self.kills_before_boss[self.chapter_map]:
                            Utils.script_sleep(2.5)
                        """
                        return True
                if confirmed_fight and Utils.find_and_touch("combat/defeat_close_button"):
                    Logger.log_debug("Fleet was defeated.")
                    defeat = True
                    Utils.wait_till_stable(max_time=3.0)
                    #Utils.script_sleep(3)

    def movement_handler(self, target_info):
        """
        Method that handles the fleet movement until it reach its target (mystery node or enemy node).
        If the coordinates are wrong, they will be blacklisted and another set of coordinates to work on is obtained.
        If the target is a mystery node and what is found is ammo, then the method will fall in the blacklist case
        and search for another enemy: this is inefficient and should be improved, but it works.

        Args:
            target_info (list): coordinate_x, coordinate_y, type. Describes the selected target.
        Returns:
            (int): 1 if a fight is needed, -1 if unreachable, -2 if timeouts  otherwise 0.
        """
        if target_info[0] < 175:
            Logger.log_msg("Skip touching fleet info zone. Move to next enemy")
            return -1

        if target_info[0] > 990 and target_info[1] >= 940:
            Logger.log_msg("Skip touching command zone. Move to next enemy")
            return -1

        if 1920 > target_info[0] > 1765 and 805 > target_info[1] > 605:
            Logger.log_msg("Skip touching strategy zone. Move to next enemy")
            return -1

        Logger.log_msg("Moving towards objective.")
        count = 0
        location = (target_info[0], target_info[1])

        Utils.touch(location)
        while count < 16:
            Utils.update_screen()
            self.store_screen_to_homg()
            if Utils.find("combat/alert_unable_reach", 0.8):
                Logger.log_warning("Unable to reach the target.")
                return -1
            elif Utils.find("combat/button_evade"):
                Logger.log_msg("Ambush was found, trying to evade.")
                Utils.touch_randomly(self.region["combat_ambush_evade"])
                Utils.wait_till_stable(max_time=0.5)
                continue
            elif Utils.find("combat/alert_failed_evade"):
                Logger.log_warning("Failed to evade ambush.")
                self.kills_count -= 1
                Utils.touch_randomly(self.region["menu_combat_start"])
                self.battle_handler()
            elif Utils.find("menu/alert_info"):
                Logger.log_debug("Found alert.")
                Utils.find_and_touch("menu/alert_close")
            elif Utils.find("combat/alert_ammo_supplies"):
                Logger.log_msg("Ammo supplies found on node.")
                return 0
            elif Utils.find("menu/item_found"):
                Logger.log_msg("Item found on node.")
                Utils.touch_randomly(self.region['tap_to_continue'])
                if Utils.find("combat/menu_emergency"):
                    Utils.wait_till_stable(max_time=1)
                    self.store_screen_to_homg()
                    if not Utils.find("combat/strategy"):
                        Utils.touch_randomly(self.region["close_strategy_menu"])
                        Utils.wait_till_stable(max_time=2)
                return 0
            if Utils.find("combat/menu_loading"):
                return 1
            elif Utils.find("combat/menu_formation"):
                Utils.find_and_touch("combat/auto_combat_off")
                return 1
            else:
                if count != 0 and count % 3 == 0:
                    Utils.touch(location)
                count += 1
        return -2


    def retreat_handler(self):
        """ Retreats if necessary.
        """
        while True:
            Utils.wait_update_screen(2)
            self.store_screen_to_homg()

            if Utils.find("combat/alert_morale_low"):
                Utils.touch_randomly(self.region['close_info_dialog'])
                self.exit = 3
                continue
            if Utils.find("menu/button_sort"):
                Utils.touch_randomly(self.region['close_info_dialog'])
                self.exit = 4
                continue
            if Utils.find("combat/menu_formation"):
                Utils.touch_randomly(self.region["menu_nav_back"])
                continue
            if Utils.find("combat/button_retreat"):
                Utils.touch_randomly(self.region['retreat_button'])
                continue
            if Utils.find("menu/button_confirm"):
                Utils.touch_randomly(self.region['combat_com_confirm'])
                continue
            if Utils.find("menu/attack"):
                if self.exit != 1 and self.exit != 2 and self.exit != 5:
                    Logger.log_msg("Retreating...")
                return

    def clear_map(self):
        """ Clears map.
        """
        Logger.log_msg("Started map clear.")
        Utils.wait_till_stable(max_time=2.5)

        while Utils.find("combat/fleet_lock", 0.99):
            Utils.touch_randomly(self.region["fleet_lock"])
            Logger.log_warning("Fleet lock is not supported, disabling it.")
            Utils.wait_update_screen(1)
            self.store_screen_to_homg()

        # swipe map to fit everything on screen
        swipes = {
            'E-SP1': lambda: Utils.swipe(960, 540, 1400, 640, 300),
            'E-SP2': lambda: Utils.swipe(960, 540, 1500, 540, 300),
            'E-SP3': lambda: Utils.swipe(960, 840, 1300, 540, 300),
            '7-2': lambda: Utils.swipe(960, 540, 1300, 600, 300),
            '10-2': lambda: Utils.swipe(960, 440, 960, 640, 300),
            '12-2': lambda: Utils.swipe(1000, 570, 1300, 540, 300),
            '12-3': lambda: Utils.swipe(1250, 530, 1300, 540, 300),
            '12-4': lambda: Utils.swipe(960, 300, 960, 540, 300),
            '13-1': lambda: Utils.swipe(1020, 500, 1300, 540, 300),
            '13-2': lambda: Utils.swipe(1125, 550, 1300, 540, 300),
            '13-3': lambda: Utils.swipe(1150, 510, 1300, 540, 300),
            '13-4': lambda: Utils.swipe(1200, 450, 1300, 540, 300)
        }
        # disable subs' hunting range
        if self.config.combat["hide_subs_hunting_range"]:
            Utils.script_sleep(0.5)
            Utils.touch_randomly(self.region["open_strategy_menu"])
            Utils.script_sleep()
            Utils.touch_randomly(self.region["disable_subs_hunting_radius"])
            Utils.script_sleep()
            Utils.touch_randomly(self.region["close_strategy_menu"])

        if self.boss_fleet_no != self.mob_fleet_no:
            self.switch_fleet(self.boss_fleet_no)
            self.switch_fleet(self.mob_fleet_no)

        while True:
            Utils.update_screen()
            self.store_screen_to_homg()

            if self.boss_defeated:
                self.exit = 1
                break

            if Utils.find("combat/alert_unable_battle"):
                Utils.touch_randomly(self.region['close_info_dialog'])
                self.exit = 4
                break

            if self.config.combat['retreat_after'] != 0 and self.combats_done >= self.config.combat['retreat_after']:
                Logger.log_msg("Retreating after defeating {} enemies".format(self.config.combat['retreat_after']))
                self.exit = 5
                break

            if not Utils.find("combat/strategy"):
                Utils.touch_randomly(self.region["close_strategy_menu"])
                Utils.wait_till_stable(max_time=2)

            if Utils.find("combat/menu_loading"):
                self.battle_handler()
                continue
            elif Utils.find("combat/menu_formation"):
                Utils.find_and_touch("combat/auto_combat_off")
                self.battle_handler()
                continue

            boss_region = Utils.find_in_scaling_range("enemy/fleet_boss")
            if self.boss_fleet_found or boss_region:
                Logger.log_msg("Boss fleet was found.")
                self.boss_fleet_found = True

                if self.auto_switch_fleet():
                    boss_region = self.find_boss_fleet()
                elif boss_region is None:
                    boss_region = self.find_boss_fleet()

                if boss_region is not None:
                    ret = self.attack_boss(boss_region)
                    if ret == 1:
                        self.exit = 1
                        break
                    else:
                        while ret != 1:
                            if self.attack_boss_resolver():
                                boss_region = self.find_boss_fleet()
                                if boss_region:
                                    ret = self.attack_boss(boss_region)
                                    continue

                            self.exit = 1
                            break
                        if ret == 1:
                            self.exit = 1
                            break
                        else:
                            self.exit = 4
                            break

            self.auto_switch_fleet()

            ret = self.attack_fleet(1, skip_if_boss=True)
            if ret == 0:
                self.exit = 4
                break

        self.retreat_handler()
        return True

    def auto_switch_fleet(self):
        fleet_switched = False

        if self.force_fleet_no is None:
            if self.combats_done >= self.switch_fleet_after_combats or self.boss_fleet_found:
                if self.switch_fleet(self.boss_fleet_no):
                    fleet_switched = True
            else:
                if self.switch_fleet(self.mob_fleet_no):
                    fleet_switched = True
        else:
            if self.switch_fleet(self.force_fleet_no):
                fleet_switched = True

        return fleet_switched

    def attack_fleet(self, num, skip_if_boss):
        """
        :param num: number of fleets to attack
        :param skip_if_boss: return immediately if boss is detected
        :return: -1 find boss fleet, 0 error, defeated_enemies otherwise
        """
        defeated_enemies = 0
        while defeated_enemies < num:
            ret, boss_list, supply_list, enemy_list = self.find_enemy_fleet(not skip_if_boss)
            if ret is False:
                return 0
            elif len(boss_list) > 0:
                return -1

            succeed, self.last_visited_idx = self.attack_mob(supply_list, enemy_list)
            if succeed:
                defeated_enemies += 1
            else:
                self.swipe_map()

        return defeated_enemies

    def find_enemy_fleet(self, ignore_boss):
        give_up = False
        boss_fleet_found = False
        mob_fleet_found = False
        boss_list = list()
        supply_list = list()
        enemy_list = list()
        curr_fleet_no = self.get_fleet_number()
        fleet_mov_ord = [curr_fleet_no]
        if self.mob_fleet_no not in fleet_mov_ord:
            fleet_mov_ord.append(self.mob_fleet_no)
        if self.boss_fleet_no not in fleet_mov_ord:
            fleet_mov_ord.append(self.boss_fleet_no)

        if self.last_visited_idx is not None:
            node_coord = self.tile_idx_to_map_coord(self.last_visited_idx)
            Utils.swipe(node_coord[0], node_coord[1], 960, 600, 600)
            self.store_screen_to_homg()
            self.last_visited_idx = None

        while give_up is False:
            for i in range(12):
                sea_map, supply_list, enemy_list = self.update_map()
                if sea_map is None:
                    for j in range(4):
                        self.swipe_map()
                        sea_map, supply_list, enemy_list = self.update_map()
                        if sea_map is not None:
                            break

                if sea_map is None:
                    # cannot read sea map after several tries
                    return False, list(), list(), list()
                else:
                    boss_list = self.find_objs_on_map(HomgConsts.MAP_BOSS, sea_map)
                    if len(boss_list) > 0 and not ignore_boss:
                        boss_fleet_found = True
                        break
                    elif len(enemy_list) + len(supply_list) > 0:
                        mob_fleet_found = True
                        break
                    else:
                        # no object to attack or get, swipe the map
                        self.swipe_map(int(i / 4) + 1)

            if boss_fleet_found or mob_fleet_found:
                break
            else:
                # enemy_fleets or supplies may be blocked by our fleet
                while len(fleet_mov_ord) > 0:
                    fleet_no = fleet_mov_ord.pop(0)
                    if self.switch_fleet(fleet_no):
                        self.store_screen_to_homg()
                        self.homg.init_map_coordinate()
                        sea_map = self.merge_map()
                    free_list = self.find_objs_on_map(HomgConsts.MAP_FREE, sea_map)
                    if self.move_fleet_to_free_tile(free_list):
                        break
                else:
                    give_up = True
                    break

        if give_up:
            return False, list(), list(), list()
        elif ignore_boss:
            return True, list(), supply_list, enemy_list
        else:
            if boss_fleet_found:
                self.boss_fleet_found = True
            return True, boss_list, supply_list, enemy_list

    def attack_mob(self, supply_list, enemy_list):
        target_list = supply_list + enemy_list
        while len(target_list) > 0:
            target_index = target_list.pop(0)
            target_coord = self.tile_idx_to_map_coord(target_index)

            if target_coord is not None:
                ret = self.movement_handler(target_coord)
                if ret == 0:
                    Utils.wait_till_stable(max_time=4.0)
                    return True, target_index
                elif ret > 0:
                    if self.battle_handler():
                        Utils.wait_till_stable(min_time=1.0, max_time=4.0)
                        return True, target_index
        return False, None

    def update_map(self):
        sea_map = self.merge_map()
        if sea_map is None:
            return None, list(), list()
        # Find character
        character_loc = np.where(sea_map == HomgConsts.MAP_CHARACTER)
        enemy_list = []
        supply_list = []
        if len(character_loc[0]) > 0:
            character_idx = (character_loc[0][0], character_loc[1][0])
            enemy_list, supply_list = self.homg.bfs_search(sea_map, character_idx)
        # If above failed, find all enemy and mysterious nodes
        if len(enemy_list) + len(supply_list) == 0:
            # Shuffle the list. Hope this can decrease average retry time.
            enemy_list = self.find_objs_on_map(HomgConsts.MAP_ENEMY, sea_map)
            if len(enemy_list) > 0:
                random.shuffle(enemy_list)
            supply_list = self.find_objs_on_map(HomgConsts.MAP_SUPPLY, sea_map)
            if len(supply_list) > 0:
                random.shuffle(supply_list)

        return sea_map, supply_list, enemy_list

    def tile_idx_to_map_coord(self, index):
        return self.homg.inv_transform_coord(self.homg.map_index_to_coord(index))

    def get_free_tile_list(self, sea_map):
        ret = self.find_objs_on_map(HomgConsts.MAP_FREE, sea_map)
        if len(ret) > 0:
            random.shuffle(ret)
        return ret

    def move_fleet_to_free_tile(self, free_list):
        while len(free_list) > 0:
            target_index = free_list.pop()
            target_info = self.homg.inv_transform_coord(
                self.homg.map_index_to_coord(target_index))
            if self.movement_handler(target_info) == -2:
                return True
            Utils.wait_till_stable(max_time=1.0)
        return False

    def switch_fleet(self, fleet_number):
        if self.get_fleet_number() == fleet_number:
            return False
        while self.get_fleet_number() != fleet_number:
            self.last_visited_idx = None
            Utils.touch_randomly(self.region['button_switch_fleet'])
            Utils.wait_till_stable(max_time=2.0)
            self.store_screen_to_homg()
        return True

    def get_fleet_number(self):
        if Utils.find_in_region("combat/fleet_1", self.region['fleet_no'], 0.9):
            return 1
        else:
            return 2

    def merge_map(self, num=3):
        # try to resolve the blinking yellow boundary by combining multiple maps
        # Create map
        Utils.update_screen()
        self.store_screen_to_homg()
        # Cannot find pivot tile, swipe the map and try again
        prev_shape = (0, 0)

        if not self.homg.init_map_coordinate():
            return None

        while self.homg.get_map_shape() != prev_shape:
            prev_shape = self.homg.get_map_shape()
            Utils.update_screen()
            self.store_screen_to_homg()
            self.homg.init_map_coordinate()


        sea_map = np.zeros(shape=self.homg.get_map_shape())
        # should remove the magic number 6
        types_of_node = 6
        vote = np.zeros(shape=(*self.homg.get_map_shape(), types_of_node))
        counter = 0
        while counter < num:
            Utils.update_screen()
            tmp_map = self.homg.create_map()
            if tmp_map.shape != sea_map.shape:
                continue
            if tmp_map is None:
                continue
            else:
                counter += 1
            for node_type in range(types_of_node):
                vote[tmp_map == node_type, node_type] += 1
        for node_type in range(types_of_node):
            sea_map[vote[::, ::, node_type] > num / 2] = node_type
        sea_map[vote[::, ::, HomgConsts.MAP_CHARACTER] > 0] = HomgConsts.MAP_CHARACTER
        sea_map[vote[::, ::, HomgConsts.MAP_SUPPLY] > 0] = HomgConsts.MAP_SUPPLY
        print(sea_map)
        return sea_map

    def swipe_map(self, times=1):
        Utils.update_screen()
        old_fleet_num = self.get_fleet_number()
        while True:
            for i in range(times):
                self.last_visited_idx = None
                Utils.swipe(*self.swipe_coord[self.swipe_dir_idx])
            if old_fleet_num == self.get_fleet_number():
                break
            else:
                self.switch_fleet(old_fleet_num)
        self.swipe_dir_idx = (self.swipe_dir_idx + 1) % 4
        self.store_screen_to_homg()

    def map_swiping_resolver(self):
        """
        first boss fleet resolving method
        try swiping the map
        """
        boss_swipe_counter = 0
        boss_swipe_counter_max = 4 * 3
        boss_region = Utils.find_in_scaling_range("enemy/fleet_boss")
        while boss_region is None and boss_swipe_counter < boss_swipe_counter_max:
            self.swipe_map(1 + int(boss_swipe_counter / 4))
            boss_region = Utils.find_in_scaling_range("enemy/fleet_boss")
            boss_swipe_counter += 1
        return boss_region

    def fleet_moving_resolver(self, fleet_no):
        """
         second boss fleet resolving method
         try moving the fleet of fleet_no to a free tile to show the boss fleet
         """
        if self.boss_fleet_no != fleet_no and self.mob_fleet_no != fleet_no:
            return None

        if self.boss_fleet_no != self.mob_fleet_no:
            if self.get_fleet_number() == 1:
                self.switch_fleet(2)
                self.switch_fleet(1)
            else:
                self.switch_fleet(1)
                self.switch_fleet(2)

        self.switch_fleet(fleet_no)

        if not self.homg.init_map_coordinate():
            return None
        tmp_map = self.homg.create_map()
        free_list = self.get_free_tile_list(tmp_map)
        boss_region = Utils.find_in_scaling_range("enemy/fleet_boss")
        while boss_region is None:
            if not self.move_fleet_to_free_tile(free_list):
                # no free tile to move to, resolving failed
                return None
            else:
                boss_region = Utils.find_in_scaling_range("enemy/fleet_boss")
        return boss_region

    def find_boss_fleet(self):
        Logger.log_debug("boss fleet resolver.")
        boss_fleet_resolve = True
        boss_region = None

        if self.get_fleet_number() != self.boss_fleet_no:
            self.switch_fleet(self.boss_fleet_no)
            boss_region = Utils.find_in_scaling_range("enemy/fleet_boss")

        if boss_region is None:
            boss_region = Utils.find_in_scaling_range("enemy/fleet_boss")

        if boss_region is None:
            boss_region = self.map_swiping_resolver()

        if boss_region is None:
            boss_region = self.fleet_moving_resolver(self.boss_fleet_no)

        if boss_region is None and self.boss_fleet_no != self.mob_fleet_no:
            boss_region = self.fleet_moving_resolver(self.mob_fleet_no)
            self.switch_fleet(self.boss_fleet_no)

        if boss_region is None:
            return None
        else:
            return boss_region

    def attack_boss(self, boss_region):
        """
        attack boss located at the boss_region coordinate
        :param boss_region:
        :return: 1 if boss is defeated; 0 if boss is unreachable; -1 if boss is not on the map
        """
        Logger.log_debug("Started boss function.")

        if self.movement_handler([boss_region.x, boss_region.y]) > 0:
            if self.battle_handler(boss=True):
                Utils.wait_till_stable(max_time=2.0)
                return 1

        Utils.swipe(boss_region.x, boss_region.y, 960, 640, 300)
        self.store_screen_to_homg()
        sea_map = self.merge_map()
        boss_index = self.find_objs_on_map(HomgConsts.MAP_BOSS, sea_map)
        if len(boss_index) > 0:
            boss_index = boss_index[0]
        else:
            Logger.log_warning("Unable to find boos fleet on the map.")
            return -1

        # BFS from the boss node
        enemy_list, _ = self.homg.bfs_search(sea_map, boss_index)
        # sort enemy from the enemy with the farthest shortest path from boss to shortest shortest path from boss
        enemy_list.reverse()
        unreachable_enemy_list = self.find_objs_on_map(HomgConsts.MAP_ENEMY, sea_map)
        for enemy in unreachable_enemy_list:
            if enemy not in enemy_list:
                enemy_list.append(enemy)

        boss_coord = self.homg.inv_transform_coord(self.homg.map_index_to_coord(boss_index))
        while True:
            # moved to boos
            ret = self.movement_handler(boss_coord)

            if ret > 0:
                if self.battle_handler(boss=True):
                    Utils.wait_till_stable(max_time=2.0)
                    self.exit = 1
                    return 1
            elif ret == 0:
                continue
            else:
                Logger.log_msg("Unable to reach boss.")
                Utils.script_sleep(2)
                # handle boss' coordinates
                battle_end = False
                while len(enemy_list) > 0:
                    enemy = enemy_list.pop(0)
                    if self.movement_handler(self.homg.inv_transform_coord(self.homg.map_index_to_coord(enemy))) == 1:
                        if self.battle_handler():
                            battle_end = True
                            Utils.wait_till_stable(max_time=1.0)
                            break
                    else:
                        Utils.wait_update_screen(1)
                if not battle_end:
                    break
        return 0

    def attack_boss_resolver(self):

        if self.switch_fleet(
                self.mob_fleet_no) and self.switch_fleet(
                self.boss_fleet_no) and self.attack_fleet(1, skip_if_boss=False) == 1:
            return True
        elif self.fleet_moving_resolver_mobs(self.boss_fleet_no) and self.attack_fleet(1, skip_if_boss=False) == 1:
            return True

        elif self.fleet_moving_resolver_mobs(self.mob_fleet_no) and self.switch_fleet(
                self.boss_fleet_no) and self.attack_fleet(1, skip_if_boss=False) == 1:
            return True
        else:
            return False

    def fleet_moving_resolver_mobs(self, fleet_no):
        """
         second boss fleet resolving method
         try moving the fleet of fleet_no to a free tile to show a enemy
         """
        if self.boss_fleet_no != fleet_no and self.mob_fleet_no != fleet_no:
            return False

        if self.boss_fleet_no != self.mob_fleet_no:
            if self.get_fleet_number() == 1:
                self.switch_fleet(2)
                self.switch_fleet(1)
            else:
                self.switch_fleet(1)
                self.switch_fleet(2)

        self.switch_fleet(fleet_no)

        if not self.homg.init_map_coordinate():
            return False
        tmp_map = self.merge_map()
        if tmp_map is None:
            return False
        free_list = self.get_free_tile_list(tmp_map)
        """
        prev_enemy_list = self.find_objs_on_map(HomgConsts.MAP_ENEMY, tmp_map)
        while self.move_fleet_to_free_tile(free_list):
            tmp_map = self.merge_map()
            enemy_list = self.find_objs_on_map(HomgConsts.MAP_ENEMY, tmp_map)
            if prev_enemy_list == enemy_list:
                prev_enemy_list = enemy_list
            else:
                return True
        return False
        """
        if self.move_fleet_to_free_tile(free_list):
            return True
        else:
            return False

    def find_objs_on_map(self, item, sea_map):
        loc = np.flip(np.where(sea_map == item), axis=0)
        if len(loc[0]) > 0:
            return list(zip(*loc[::-1]))
        else:
            return list()

    def store_screen_to_homg(self):
        self.homg.load_color_screen(Utils.color_screen)

    # unused function
    def move_to_fleet(self):
        """Method to get the fleet's current location. Note it uses the green
        fleet marker to find the location but returns around the area of the
        feet of the flagship

        Returns:
            None
        """
        sea_map = self.merge_map()
        counter = 1
        while len(self.find_objs_on_map(HomgConsts.MAP_CHARACTER, sea_map)) == 0:
            self.swipe_map(int((counter + 4) / 4))
            sea_map = self.merge_map()
            counter += 1

        return sea_map
    
    