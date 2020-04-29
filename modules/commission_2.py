from util.utils import Region, Utils
from util.logger import Logger
from util.stats import Stats
from util.config import Config
import cv2
import pytesseract
import numpy as np
import os


class CommissionModule:
    class ObjectRegion:
        left_menu = Region(0, 203, 57, 86)
        collect_oil = Region(206, 105, 98, 58)
        collect_gold = Region(579, 102, 98, 58)
        complete_commission = Region(574, 393, 181, 61)
        button_go = Region(574, 393, 181, 61)
        urgent_tab = Region(24, 327, 108, 103)
        daily_tab = Region(22, 185, 108, 103)
        last_commission = Region(298, 846, 1478, 146)
        commission_recommend = Region(1306, 483, 192, 92)
        commission_start = Region(1543, 483, 191, 92)
        oil_warning = Region(1073, 738, 221, 59)
        button_back = Region(48, 43, 76, 76)
        tap_to_continue = Region(661, 840, 598, 203)
        dismiss_side_tab = Region(970, 148, 370, 784)
        dismiss_message = Region(688, 11, 538, 55)
        commission_detect_region = Region(15, 330, 765, 180)

    class ImageFileName:
        commission_title = "menu/commission"
        alert_completed = "commission/button_completed"
        alert_available = "commission/alert_available"
        alert_begun = "commission/alert_begun"
        alert_perfect = "commission/alert_perfect"
        button_cancel = "commission/button_cancel"
        button_completed = "commission/button_completed"
        button_go = "commission/button_go"
        button_ready = "commission/button_ready"
        button_recommend = "commission/button_recommend"
        status_in_action = "commission/commission_in_action"
        status_idle = "commission/commission_status"
        status_full = "commission/commissions_full"
        button_daily_normal = "commission/daily_normal"
        button_daily_clicked = "commission/daily_clicked"
        button_urgent_normal = "commission/urgent_normal"
        button_urgent_clicked = "commission/urgent_clicked"
        button_battle = "menu/button_battle"
        item_found = "menu/item_found"
        button_confirm = "menu/button_confirm"
        sidebar = "menu/sidebar"

    def __init__(self, config, stats):
        """Initializes the Expedition module.

        Args:
            config (Config): ALAuto Config instance
            stats (Stats): ALAuto stats instance
        """
        self.enabled = True
        self.config = config
        self.stats = stats
        self.region = {
            'left_menu': Region(0, 203, 57, 86),
            'collect_oil': Region(206, 105, 98, 58),
            'collect_gold': Region(579, 102, 98, 58),
            'complete_commission': Region(574, 393, 181, 61),
            'button_go': Region(574, 393, 181, 61),
            'urgent_tab': Region(24, 327, 108, 103),
            'daily_tab': Region(22, 185, 108, 103),
            'last_commission': Region(298, 846, 1478, 146),
            'commission_recommend': Region(1306, 483, 192, 92),
            'commission_start': Region(1543, 483, 191, 92),
            'oil_warning': Region(1073, 738, 221, 59),
            'button_back': Region(48, 43, 76, 76),
            'tap_to_continue': Region(661, 840, 598, 203),
            'dismiss_side_tab': Region(970, 148, 370, 784),
            'dismiss_message': Region(688, 11, 538, 55),
            'commission_detect_region': Region(15, 330, 765, 180),
            'classroom_detect_region': Region(15, 545, 765, 180),
            'lab_detect_region': Region(15, 755, 765, 180)
        }

        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
        self.__tessdata_path = os.path.join(os.getcwd(), r'tesseract\tessdata')
        self.__tesseract_config = r'--tessdata-dir "{}" --psm 6 --dpi 240 digits'.format(self.__tessdata_path)

    def detect_in_side_bar(self, image, similarity=None):
        if similarity:
            return Utils.find_in_region(image, self.ObjectRegion.commission_detect_region, similarity)
        else:
            return Utils.find_in_region(image, self.ObjectRegion.commission_detect_region)

    def commission_logic_wrapper(self):
        """Method that fires off the necessary child methods that encapsulates
        the entire action of starting and completing commissions.
        """

        retry_max = 5

        Logger.log_msg("Checking Commissions.")

        if self.open_sidebar() == False:
            return False

        Utils.touch_randomly(self.ObjectRegion.collect_oil)
        Utils.touch_randomly(self.ObjectRegion.collect_gold)
        completed_region = self.detect_in_side_bar(self.ImageFileName.alert_completed)
        if completed_region:
            Logger.log_debug("Found commission complete button.")
            self.completed_handler()
        Utils.update_screen()

        failed = True

        for i in range(retry_max):
            alert_region = self.detect_in_side_bar(self.ImageFileName.alert_available, 0.9)
            if alert_region:
                Logger.log_debug("Found commission available indicator.")
                Utils.touch_randomly(self.ObjectRegion.button_go)
                Utils.wait_update_screen(1)
            if Utils.find(self.ImageFileName.commission_title):
                failed = False
                break
            Utils.update_screen()

        if failed:
            Logger.log_msg("All commissions are running.")
            return self.close_sidebar()
        else:
            Logger.log_msg("Entered commission menu.")

        if self.click_urgent():
            Logger.log_msg("Moved to urgent tab.")
        else:
            Logger.log_msg("Unable to move to urgent tab.")
            return False

        rank = 0
        while not self.check_commission_full():
            if self.click_nth_commission(rank):
                if not self.start_commission():
                    Logger.log_msg("Unable to start commission, move to next one.")
                    Utils.touch_randomly(self.ObjectRegion.dismiss_message)
                    rank += 1
                else:
                    Logger.log_msg("Commission started successfully.")
                    rank = rank
            else:
                Logger.log_msg("No more available commission.")
                break

        if self.click_daily():
            Logger.log_msg("Moved to daily tab.")
        else:
            Logger.log_msg("Unable to Move to daily tab.")
            return False

        if failed:
            return False

        rank = 0
        while not self.check_commission_full():
            if self.click_nth_commission(rank):
                if not self.start_commission():
                    Logger.log_msg("Unable to start commission, move to next one.")
                    # should rewrite the program using exception and move this into start_commision_
                    Utils.touch_randomly(self.ObjectRegion.dismiss_message)
                    rank += 1
                else:
                    Logger.log_msg("Commission started successfully.")
                    rank = rank
            else:
                Logger.log_msg("No more available commission.")
                break

        failed = True

        for i in range(retry_max):
            if Utils.find(self.ImageFileName.commission_title):
                Utils.touch_randomly(self.ObjectRegion.button_back)
                Utils.wait_update_screen(1)
            go_region = self.detect_in_side_bar(self.ImageFileName.button_go)
            completed_region = self.detect_in_side_bar(self.ImageFileName.button_completed)
            if go_region or completed_region:
                failed = False
                break
            Utils.wait_update_screen(1)

        if failed:
            Logger.log_msg("Cannot move back to main menu sidebar.")
            return False
        else:
            Logger.log_msg("Moved back to main menu sidebar.")

        self.close_sidebar()
        return True

    def open_sidebar(self):
        retry_max = 5

        failed = True

        for i in range(retry_max):
            Utils.touch_randomly(self.ObjectRegion.left_menu)
            Utils.wait_update_screen(1)
            if self.detect_in_side_bar(self.ImageFileName.sidebar):
                failed = False
                break

        if failed:
            Logger.log_msg("Cannot open sidebar.")
            return False
        else:
            Logger.log_msg("Sidebar opened.")
            return True

    def close_sidebar(self):
        retry_max = 5

        failed = True

        for i in range(retry_max):
            sidebar = self.detect_in_side_bar(self.ImageFileName.sidebar)
            if sidebar:
                Utils.touch_randomly(self.ObjectRegion.dismiss_side_tab)
                Utils.wait_update_screen(1)
            if Utils.find(self.ImageFileName.button_battle):
                failed = False
                break
            Utils.wait_update_screen(1)

        if failed:
            Logger.log_msg("Cannot close sidebar.")
            return False
        else:
            Logger.log_msg("Sidebar closed.")
            return True

    def completed_handler(self):

        completed_region = self.detect_in_side_bar(self.ImageFileName.button_completed)
        while completed_region:
            Utils.touch_randomly(completed_region)
            Utils.wait_update_screen(1)
            completed_region = self.detect_in_side_bar(self.ImageFileName.button_completed)

        retry_counter = 0
        retry_max = 5

        while retry_max > retry_counter:
            Utils.update_screen()
            if Utils.find(self.ImageFileName.alert_perfect):
                Utils.touch_randomly(self.ObjectRegion.tap_to_continue)
                self.stats.increment_commissions_received()
            elif Utils.find(self.ImageFileName.item_found):
                Utils.touch_randomly(self.ObjectRegion.tap_to_continue)
                Utils.script_sleep(1)
            elif self.detect_in_side_bar(self.ImageFileName.alert_available, 0.9):
                Logger.log_debug("Finished completing commissions.")
                Utils.script_sleep(0.5)
                break
            else:
                retry_counter += 1
                Utils.script_sleep(1)
        return

    def get_all_commissions_info(self):
        ret_list = []
        item_coords = {}

        Utils.swipe(960, 680, 960, 400, 300)
        Utils.wait_update_screen(2)
        commissions_coord = Utils.find_all(self.ImageFileName.status_idle)
        item_coords['cubes'] = Utils.find_all("commission/cubes")
        item_coords['oil'] = Utils.find_all("commission/oil")
        for com in commissions_coord:
            rewards = {"oil": False, "cubes": False}
            for name, locations in item_coords:
                for loc in locations:
                    if com[0] < loc[0] < com[0] + 1250 and com[1] - 105 < loc[1] < com[1] + 75:
                        rewards[name] = True
                        break
            ret_list.append((com[0], com[1], rewards))
        return ret_list

    def click_nth_commission(self, rank):
        retry = 5
        for i in range(retry):
            Utils.swipe(960, 880, 960, 400, 300)
            Utils.wait_update_screen(2)
            avail_commissions = Utils.find_all(self.ImageFileName.status_idle)
            if rank >= len(avail_commissions):
                return False
            x = avail_commissions[-(rank + 1)][0]
            y = avail_commissions[-(rank + 1)][1]
            offset = 10
            Utils.touch_randomly(Region(x - offset, y - offset, 2 * offset, 2 * offset))
            Utils.wait_update_screen(1)
            if Utils.find(self.ImageFileName.button_recommend):
                return True
        return False

    def check_commission_full(self):
        return Utils.find(self.ImageFileName.status_full)

    def click_urgent(self):
        retry_max = 5
        for i in range(retry_max):
            if Utils.find_and_touch(self.ImageFileName.button_urgent_normal):
                Utils.wait_update_screen(1)
            if Utils.find(self.ImageFileName.button_urgent_clicked):
                return True
            Utils.update_screen()
        return False

    def click_daily(self):
        retry_max = 5
        for i in range(retry_max):
            if Utils.find_and_touch(self.ImageFileName.button_daily_normal):
                Utils.wait_update_screen(1)
            if Utils.find(self.ImageFileName.button_daily_clicked):
                return True
            Utils.update_screen()
        return False

    def start_commission(self):
        Logger.log_debug("Starting commission.")
        retry_max = 5
        failed = True

        for i in range(retry_max):
            if Utils.find(self.ImageFileName.button_recommend):
                Logger.log_debug("Found commission recommend button.")
                Logger.log_debug("The " + str(int(i)) + " attempt.")
                try:
                    oil_required = self.read_oil(1670, 439, 53, 30)
                    Logger.log_msg("Found commission required oil: " + str(oil_required) + ".")
                except ValueError as verr:
                    Logger.log_msg("Cannot read commission required oil, starting it anyway.")
                    oil_required = -1
                if oil_required > 99:
                    Logger.log_msg("Exceed oil consumption limit")
                    break
                Utils.touch_randomly(self.ObjectRegion.commission_recommend)
                Utils.wait_update_screen(1)
            if Utils.find(self.ImageFileName.button_ready):
                failed = False
                break
            Utils.update_screen()

        if failed:
            return False

        failed = True

        for i in range(retry_max):
            if Utils.find(self.ImageFileName.button_ready):
                Logger.log_debug("Found commission start button.")
                Utils.touch_randomly(self.ObjectRegion.commission_start)
                Utils.wait_update_screen(1)
            oil_warning = Utils.find(self.ImageFileName.button_confirm)
            commission_begun = Utils.find(self.ImageFileName.alert_begun)
            if oil_warning or commission_begun:
                failed = False
                break
            Utils.update_screen()

        if failed:
            return False

        failed = True
        for i in range(retry_max):
            oil_warning = Utils.find(self.ImageFileName.button_confirm)
            commission_begun = Utils.find(self.ImageFileName.alert_begun)
            if oil_warning:
                Logger.log_debug("Found commission oil warning message.")
                Utils.touch_randomly(self.ObjectRegion.oil_warning)
                Utils.wait_update_screen(1)
                commission_begun = Utils.find(self.ImageFileName.alert_begun)
            if commission_begun:
                Logger.log_msg("Successfully started commission.")
                Utils.touch_randomly(self.ObjectRegion.dismiss_message)
                self.stats.increment_commissions_started()
                failed = False
                break
            Utils.update_screen()

        if failed:
            return False
        else:
            return True

    def read_oil(self, x, y, w, h):
        img = Utils.screen[y:y + h, x:x + w]
        # only pick the light color in the image
        l_chan_thres = np.max(img) * 0.6
        mask = cv2.inRange(img, l_chan_thres, 255)
        img = cv2.bitwise_and(img, img, mask=mask)
        # invert the color, tesseract LSTM prefers dark text light background
        img = cv2.bitwise_not(img)
        # tesseract needs boundary around the text
        half_height = int(img.shape[0] / 2)
        half_width = int(img.shape[1] / 2)
        img = cv2.copyMakeBorder(img, top=half_height, bottom=half_height, left=half_width, right=half_width,
                                 borderType=cv2.BORDER_CONSTANT, value=255)
        cv2.imwrite('tesseract_input.png', img)
        return int(pytesseract.image_to_string(img, config=self.__tesseract_config))
