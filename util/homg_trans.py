import cv2
import numpy as np
import enum
import util.homg_trans_consts as trans_consts


class HomographyTransform:
    """
    Dependencies of each function must be executed at least once before calling it.
    """

    def __init__(self):
        self._top_left_tile_x = None
        self._top_left_tile_y = None
        self._col_max_idx = None
        self._row_max_idx = None
        self._screen = None
        self._color_screen = None
        self._h_trans_m = None
        self._inv_h_trans_m = None
        self._h_trans_screen_size = None
        self._small_boss_icon = False
        self._debug_enabled = False
        self._debug_out_func = None

        self.__free_tile_center_img = cv2.imread(trans_consts.FREE_TILE_CENTER_IMG, cv2.IMREAD_GRAYSCALE)
        self.__free_tile_imgs = [cv2.imread(trans_consts.FREE_TILES_IMG_UP, cv2.IMREAD_GRAYSCALE),
                                 cv2.imread(trans_consts.FREE_TILES_IMG_DOWN, cv2.IMREAD_GRAYSCALE),
                                 cv2.imread(trans_consts.FREE_TILES_IMG_LEFT, cv2.IMREAD_GRAYSCALE),
                                 cv2.imread(trans_consts.FREE_TILES_IMG_RIGHT, cv2.IMREAD_GRAYSCALE)]

        self.__free_tile_lu = cv2.imread(trans_consts.FREE_TILES_LU_IMG, cv2.IMREAD_GRAYSCALE)

        self.__enemy1_obj = DetectionObjet()
        self.__enemy1_obj.set_img_file_path(trans_consts.ENEMY_1_IMG)
        self.__enemy1_obj.set_scale_base(trans_consts.ENEMY_SCALE)
        self.__enemy1_obj.set_search_rect(trans_consts.ENEMY_SEARCH_RECT)
        self.__enemy1_obj.set_search_offset(trans_consts.ENEMY_OFFSET)
        self.__enemy1_obj.read_img_file()

        self.__enemy2_obj = DetectionObjet()
        self.__enemy2_obj.set_img_file_path(trans_consts.ENEMY_2_IMG)
        self.__enemy2_obj.set_scale_base(trans_consts.ENEMY_SCALE)
        self.__enemy2_obj.set_search_rect(trans_consts.ENEMY_SEARCH_RECT)
        self.__enemy2_obj.set_search_offset(trans_consts.ENEMY_OFFSET)
        self.__enemy2_obj.read_img_file()


        self.__enemy3_obj = DetectionObjet()
        self.__enemy3_obj.set_img_file_path(trans_consts.ENEMY_3_IMG)
        self.__enemy3_obj.set_scale_base(trans_consts.ENEMY_SCALE)
        self.__enemy3_obj.set_search_rect(trans_consts.ENEMY_SEARCH_RECT)
        self.__enemy3_obj.set_search_offset(trans_consts.ENEMY_OFFSET)
        self.__enemy3_obj.read_img_file()


        self.__arrow_obj = DetectionObjet()
        self.__arrow_obj.set_img_file_path(trans_consts.ARROW_IMG)
        self.__arrow_obj.set_scale_base(trans_consts.ARROW_SCALE)
        self.__arrow_obj.set_search_rect(trans_consts.ARROW_SEARCH_RECT)
        self.__arrow_obj.set_search_offset(trans_consts.ARROW_OFFSET)
        self.__arrow_obj.read_img_file()


        self.__boss_obj = DetectionObjet()
        self.__boss_obj.set_img_file_path(trans_consts.BOSS_IMG)
        self.__boss_obj.set_scale_base(trans_consts.BOSS_SCALE)
        self.__boss_obj.set_search_rect(trans_consts.BOSS_SEARCH_RECT)
        self.__boss_obj.set_search_offset(trans_consts.BOSS_OFFSET)
        self.__boss_obj.read_img_file()


        self.__mystery_obj = DetectionObjet()
        self.__mystery_obj.set_img_file_path(trans_consts.MYSTERY_IMG)
        self.__mystery_obj.set_scale_base(trans_consts.MYSTERY_SCALE)
        self.__mystery_obj.set_search_rect(trans_consts.MYSTERY_SEARCH_RECT)
        self.__mystery_obj.set_search_offset(trans_consts.MYSTERY_OFFSET)
        self.__mystery_obj.read_img_file()

        self.__ammo_obj = DetectionObjet()
        self.__ammo_obj.set_img_file_path(trans_consts.AMMO_IMG)
        self.__ammo_obj.set_scale_base(trans_consts.AMMO_SCALE)
        self.__ammo_obj.set_search_rect(trans_consts.AMMO_SEARCH_RECT)
        self.__ammo_obj.set_search_offset(trans_consts.AMMO_OFFSET)
        self.__ammo_obj.read_img_file()




        self.__arrow_img = cv2.imread(trans_consts.ARROW_IMG, cv2.IMREAD_COLOR)
        self.__enemy1_img = cv2.imread(trans_consts.ENEMY_1_IMG, cv2.IMREAD_COLOR)
        self.__enemy2_img = cv2.imread(trans_consts.ENEMY_2_IMG, cv2.IMREAD_COLOR)
        self.__enemy3_img = cv2.imread(trans_consts.ENEMY_3_IMG, cv2.IMREAD_COLOR)
        self.__boss_img = cv2.imread(trans_consts.BOSS_IMG, cv2.IMREAD_COLOR)

    def init_homg_vars(self, custom_trans_pts=None):
        """
        Initialize the variables used in this class.
        Must be executed once before executing any other functions.
        """
        if custom_trans_pts is None:
            src_pts = np.subtract(trans_consts.TRANS_SRC_PTS, trans_consts.MAP_CROP_TOP_LEFT)
            dst_pts = np.subtract(trans_consts.TRANS_DST_PTS, trans_consts.MAP_CROP_TOP_LEFT)
        else:
            src_pts = np.subtract(custom_trans_pts[0], trans_consts.MAP_CROP_TOP_LEFT)
            dst_pts = np.subtract(custom_trans_pts[1], trans_consts.MAP_CROP_TOP_LEFT)

        # Calculate Homography
        h, status = cv2.findHomography(src_pts, dst_pts)
        diff_arr = np.subtract(trans_consts.MAP_CROP_BOTTOM_RIGHT, trans_consts.MAP_CROP_TOP_LEFT)
        src_w = diff_arr[0]
        src_h = diff_arr[1]
        lin_homg_pts = np.array([
            [0, src_w, src_w, 0],
            [0, 0, src_h, src_h],
            [1, 1, 1, 1]])

        # transform points
        transf_lin_homg_pts = h.dot(lin_homg_pts)
        transf_lin_homg_pts /= transf_lin_homg_pts[2, :]

        # find min and max points
        min_x = np.floor(np.min(transf_lin_homg_pts[0])).astype(int)
        min_y = np.floor(np.min(transf_lin_homg_pts[1])).astype(int)
        max_x = np.ceil(np.max(transf_lin_homg_pts[0])).astype(int)
        max_y = np.ceil(np.max(transf_lin_homg_pts[1])).astype(int)

        # add translation to the transformation matrix to shift to positive values
        anchor_x, anchor_y = 0, 0
        transl_transf = np.eye(3, 3)
        if min_x < 0:
            anchor_x = -min_x
            transl_transf[0, 2] += anchor_x
        if min_y < 0:
            anchor_y = -min_y
            transl_transf[1, 2] += anchor_y
        shifted_transf = transl_transf.dot(h)
        self._h_trans_m = shifted_transf / shifted_transf[2, 2]
        self._inv_h_trans_m = cv2.invert(shifted_transf)[1]
        self._h_trans_screen_size = (anchor_x + max(max_x, src_w), anchor_y + max(max_y, src_h))

    def use_small_boss_icon(self, val):
        """
        Set using small boss icon
        :param val: True if using small boss icon. False if using normal icon.
        :return:
        """
        self._small_boss_icon = val

    def enable_debug_log(self, enable, debug_out_func):
        if enable and debug_out_func is None:
            return False
        self._debug_enabled = enable
        if self._debug_enabled:
            self._debug_out_func = debug_out_func
        return True

    def load_color_screen(self, color_screen):
        """
        Load the color screen.
        """
        self._color_screen = color_screen
        self._screen = cv2.cvtColor(color_screen, cv2.COLOR_BGR2GRAY)

    def init_map_coordinate(self):
        """
        Calculate the coordinates of the tiles on the map.
        Try swiping the map if it returns false.
        Dependencies: init_homg_vars, load_color_screen
        :return: True if successfully initialize the coordinates of the tiles. False otherwise.
        """
        # crop the color screen
        free_tile_center = self.__free_tile_center_img

        crop_color_screen = self._color_screen[:][
                            trans_consts.MAP_CROP_TOP_LEFT[1]:trans_consts.MAP_CROP_BOTTOM_RIGHT[1],
                            trans_consts.MAP_CROP_TOP_LEFT[0]:trans_consts.MAP_CROP_BOTTOM_RIGHT[0]]
        # Warp source image to destination based on homography
        screen_trans = cv2.warpPerspective(crop_color_screen, self._h_trans_m, self._h_trans_screen_size)
        screen_edge = cv2.Canny(screen_trans, trans_consts.CV_CANNY_MIN, trans_consts.CV_CANNY_MAX)

        closing_kernel = trans_consts.CLOSING_KERNEL_MIN_SIZE
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (closing_kernel, closing_kernel))
        screen_edge_closed = cv2.morphologyEx(screen_edge, cv2.MORPH_CLOSE, kernel)
        res = cv2.matchTemplate(screen_edge_closed, free_tile_center, cv2.TM_CCOEFF_NORMED)
        max_similarity = np.max(res)
        if self._debug_enabled:
            self._debug_out_func("free tile center", max_similarity)
        if max_similarity > trans_consts.FREE_TILE_MATCH_THRESH:
            loc = np.where(res == max_similarity)
            point = list(zip(*loc[::-1]))
            x, y = (
                point[0][0] + trans_consts.FREE_TILE_X_OFFSET,
                point[0][1] + trans_consts.FREE_TILE_Y_OFFSET)
        else:
            rects = []
            while len(rects) == 0 and closing_kernel <= trans_consts.CLOSING_KERNEL_MAX_SIZE:
                # try to close the edges
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (closing_kernel, closing_kernel))
                screen_edge_closed = cv2.morphologyEx(screen_edge, cv2.MORPH_CLOSE, kernel)
                trans_contours, _ = cv2.findContours(screen_edge_closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                for cont in trans_contours:
                    # get the convex hull
                    hull = cv2.convexHull(cont)
                    hull = hull.astype(np.float32)
                    # get the bounding rectangle
                    x, y, w, h = cv2.boundingRect(hull)
                    if w * h == 0:
                        continue
                    area_diff = abs(1 - trans_consts.TILE_WIDTH * trans_consts.TILE_HEIGHT / (w * h))
                    if 0.2 > area_diff:
                        # check it's shape is close to a square
                        ratio = abs(1 - w / h)
                        if 0.1 > ratio:
                            rects.append((x, y))
                closing_kernel += trans_consts.CLOSING_KERNEL_INCR_STEP

            if closing_kernel > trans_consts.CLOSING_KERNEL_MAX_SIZE:
                return False

            accum_dist = np.zeros(len(rects))
            for i in range(len(rects)):
                for j in range(len(rects)):
                    if i == j:
                        continue
                    remain_width = abs(rects[i][0] - rects[j][0]) % trans_consts.TILE_WIDTH
                    remain_height = abs(rects[i][1] - rects[j][1]) % trans_consts.TILE_HEIGHT
                    accum_dist[i] += min(trans_consts.TILE_WIDTH - remain_width, remain_width) + min(
                        trans_consts.TILE_HEIGHT - remain_height,
                        remain_height)

            pivot_idx = np.argmin(accum_dist)
            x, y = rects[pivot_idx]

        # Calculate how many tiles on the map and the coordinate of top left tile in homography space
        self._top_left_tile_x = int(x % trans_consts.TILE_WIDTH)
        self._top_left_tile_y = int(y % trans_consts.TILE_HEIGHT)
        self._row_max_idx = int(
            (self._h_trans_screen_size[
                 1] - self._top_left_tile_y + trans_consts.TILE_HEIGHT - 1) / trans_consts.TILE_HEIGHT)
        self._col_max_idx = int(
            (self._h_trans_screen_size[
                 0] - self._top_left_tile_x + trans_consts.TILE_WIDTH - 1) / trans_consts.TILE_WIDTH)

        return True

    def get_map_shape(self):
        """
         Return the shape of the map which will be returned in create_map()
         Dependencies: init_map_coordinate
         """
        return (self._row_max_idx, self._col_max_idx)

    def create_map(self, node_info=False):
        """
        Detect the object in each tile.
        See homg_trans_consts for the definitions of the constants used in the returned map.
        Dependencies: init_map_coordinate
        :return: M x N numpy array filled with constants defined in homg_trans_consts
        """

        # {(row,col): NodeInfo}
        node_dict = dict()

        # crop the color screen
        crop_color_screen = self._color_screen[:][
                            trans_consts.MAP_CROP_TOP_LEFT[1]:trans_consts.MAP_CROP_BOTTOM_RIGHT[1],
                            trans_consts.MAP_CROP_TOP_LEFT[0]:trans_consts.MAP_CROP_BOTTOM_RIGHT[0]]
        # Warp source image to destination based on homography
        screen_trans = cv2.warpPerspective(crop_color_screen, self._h_trans_m, self._h_trans_screen_size)
        screen_edge = cv2.Canny(screen_trans, trans_consts.CV_CANNY_MIN, trans_consts.CV_CANNY_MAX)

        sea_map = np.zeros(shape=(self._row_max_idx, self._col_max_idx))

        free_tile_lu_scaled = cv2.resize(self.__free_tile_lu,
                                         (self.__free_tile_lu.shape[1] * 2, self.__free_tile_lu.shape[0] * 2)).astype(
            np.uint8)

        for j in range(self._row_max_idx):
            for i in range(self._col_max_idx):
                cur_x = self._top_left_tile_x + i * trans_consts.TILE_WIDTH
                cur_y = self._top_left_tile_y + j * trans_consts.TILE_HEIGHT
                crop = screen_edge[cur_y: cur_y + trans_consts.TILE_HEIGHT,
                       cur_x:cur_x + trans_consts.TILE_WIDTH]
                # Get the coordinate of the center of a tile in the original space

                free_tile_matched = False

                if crop.shape[0] >= self.__free_tile_center_img.shape[0] and crop.shape[1] >= \
                        self.__free_tile_center_img.shape[
                            1]:
                    res = cv2.matchTemplate(crop, self.__free_tile_center_img, cv2.TM_CCOEFF_NORMED)
                    if np.max(res) > trans_consts.FREE_TILE_MATCH_THRESH:
                        free_tile_matched = True

                if free_tile_matched is False:
                    crop_closed = crop
                    corner_w = int(0.2 * trans_consts.TILE_WIDTH)
                    corner_h = int(0.2 * trans_consts.TILE_HEIGHT)

                    corners = list()
                    corners.append(crop_closed[:corner_h, :corner_w])
                    corners.append(crop_closed[:corner_h, -1:-corner_w:-1])
                    corners.append(crop_closed[-1:-corner_h:-1, :corner_w])
                    corners.append(crop_closed[-1:-corner_h:-1, -1:-corner_w:-1])

                    counter = 0
                    for corner in corners:
                        if corner.shape[0] >= self.__free_tile_lu.shape[0] and corner.shape[1] >= \
                                self.__free_tile_lu.shape[
                                    1]:
                            corner = cv2.resize(corner, (corner.shape[1] * 2, corner.shape[0] * 2)).astype(np.uint8)
                            corner = cv2.morphologyEx(corner, cv2.MORPH_CLOSE,
                                                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
                            res = cv2.matchTemplate(corner, free_tile_lu_scaled, cv2.TM_CCOEFF_NORMED)
                            if np.count_nonzero(res >= trans_consts.FREE_TILE_MATCH_THRESH) > 0:
                                counter += 1
                        if counter > 1:
                            free_tile_matched = True
                            break

                if free_tile_matched:
                    sea_map[j, i] = trans_consts.MAP_FREE

                # crop the perspective transformed color screen
                color_crop = screen_trans[cur_y: cur_y + trans_consts.TILE_HEIGHT,
                             cur_x:cur_x + trans_consts.TILE_WIDTH]
                if color_crop.shape < (trans_consts.TILE_HEIGHT * 0.8, trans_consts.TILE_WIDTH * 0.8):
                    continue
                hor_bound_width = int(trans_consts.TILE_HEIGHT * trans_consts.BOUNDARY_DETECT_MASK_PERCENTAGE)
                ver_bound_width = int(trans_consts.TILE_WIDTH * trans_consts.BOUNDARY_DETECT_MASK_PERCENTAGE)
                mask = np.zeros(color_crop.shape[:2], dtype=np.uint8)
                mask[:, :hor_bound_width] = 255  # up
                mask[:, -hor_bound_width:] = 255  # down
                mask[:ver_bound_width, :] = 255  # left
                mask[-ver_bound_width:, :] = 255  # right
                color_crop = cv2.bitwise_and(color_crop, color_crop, mask=mask)
                hsv_crop = cv2.cvtColor(color_crop, cv2.COLOR_BGR2HSV)
                # detect red and yellow boundaries
                lower_red = np.array(trans_consts.BOUNDARY_RED_LOWER)
                upper_red = np.array(trans_consts.BOUNDARY_RED_UPPER)
                lower_yellow = np.array(trans_consts.BOUNDARY_YELLOW_LOWER)
                upper_yellow = np.array(trans_consts.BOUNDARY_YELLOW_UPPER)
                red_hsv_color_mask = cv2.inRange(hsv_crop, lower_red, upper_red)
                yellow_hsv_color_mask = cv2.inRange(hsv_crop, lower_yellow, upper_yellow)
                if np.count_nonzero(red_hsv_color_mask) > trans_consts.BOUNDARY_RED_COUNT_THRESH:
                    sea_map[j, i] = trans_consts.MAP_ENEMY
                    tmp = NodeInfo()
                    tmp.set_siren()
                    node_dict[(j, i)] = tmp
                elif np.count_nonzero(yellow_hsv_color_mask) > trans_consts.BOUNDARY_YELLOW_COUNT_THRESH:
                    sea_map[j, i] = trans_consts.MAP_SUPPLY
                    # TODO: Ase mystery node for all supply nodes as a workaround for now
                    # Add ammo node detection method in the futue
                    tmp = NodeInfo()
                    tmp.set_mystery()
                    node_dict[(j, i)] = tmp



        self.__match_mob_tile_scale(self._color_screen, sea_map, node_dict)
        self.__match_character_tile_scale(self._color_screen, sea_map)
        self.__match_boss_tile_scale(self._color_screen, sea_map)
        self.__match_supply_tile_scale(self._color_screen, sea_map, node_dict)

        if self._debug_enabled:
            self.debug_output(sea_map)
            self._debug_out_func('Read Map:\n{}'.format(np.array2string(sea_map)))

        if node_info:
            return sea_map, node_dict
        else:
            return sea_map

    def debug_output(self, sea_map):
        crop_color_screen = self._color_screen[:][
                            trans_consts.MAP_CROP_TOP_LEFT[1]:trans_consts.MAP_CROP_BOTTOM_RIGHT[1],
                            trans_consts.MAP_CROP_TOP_LEFT[0]:trans_consts.MAP_CROP_BOTTOM_RIGHT[0]]
        screen_trans = cv2.warpPerspective(crop_color_screen, self._h_trans_m, self._h_trans_screen_size)
        screen_edge = cv2.Canny(screen_trans, trans_consts.CV_CANNY_MIN, trans_consts.CV_CANNY_MAX)

        for i in range(self._col_max_idx):
            for j in range(self._row_max_idx):
                cur_x = self._top_left_tile_x + i * trans_consts.TILE_WIDTH
                cur_y = self._top_left_tile_y + j * trans_consts.TILE_HEIGHT
                rect = np.array(
                    [[[cur_x, cur_y]], [[cur_x + trans_consts.TILE_WIDTH, cur_y]],
                     [[cur_x + trans_consts.TILE_WIDTH, cur_y + trans_consts.TILE_HEIGHT]],
                     [[cur_x, cur_y + trans_consts.TILE_HEIGHT]]],
                    dtype=np.float64)
                rect = cv2.perspectiveTransform(rect, self._inv_h_trans_m)
                rect = rect.astype(int)
                cv2.drawContours(crop_color_screen, [rect], -1, (255, 0, 0), 3)

                dot = np.array(
                    [[[cur_x + trans_consts.TILE_WIDTH / 2, cur_y + trans_consts.TILE_HEIGHT / 2]]])
                dot = cv2.perspectiveTransform(dot, self._inv_h_trans_m)
                dot = dot.astype(int)

                if sea_map[j, i] == trans_consts.MAP_CHARACTER:
                    cv2.circle(crop_color_screen, tuple(dot[0][0]), 3, (255, 0, 255), thickness=3)
                if sea_map[j, i] == trans_consts.MAP_FREE:
                    cv2.circle(crop_color_screen, tuple(dot[0][0]), 3, (0, 255, 0), thickness=3)
                if sea_map[j, i] == trans_consts.MAP_SUPPLY:
                    cv2.circle(crop_color_screen, tuple(dot[0][0]), 3, (0, 255, 255), thickness=3)
                if sea_map[j, i] == trans_consts.MAP_ENEMY:
                    cv2.circle(crop_color_screen, tuple(dot[0][0]), 3, (0, 0, 255), thickness=3)

        cv2.imwrite("debug_color_trans.png", screen_trans)
        cv2.imwrite("debug_edge.png", cv2.morphologyEx(screen_edge, cv2.MORPH_CLOSE,
                                                       cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (
                                                           trans_consts.CLOSING_KERNEL_MIN_SIZE,
                                                           trans_consts.CLOSING_KERNEL_MIN_SIZE))))
        cv2.imwrite("debug_color.png", crop_color_screen)

    def __match_mob_tile_scale(self, screen, sea_map, node_dict):
        """
        Find the tiles where the enemies are located.
        Result will write into the corresponded tile in sea_map.
        Dependencies: init_map_coordinate
        :param screen: the color screen to find the boss icon
        :param sea_map: M x N numpy array
        :return:
        """

        ret = self.__enemy1_obj.match_objects(screen, self)
        sea_map[ret] = trans_consts.MAP_ENEMY
        l1_idx_list = zip(*np.where(ret))
        for pair in l1_idx_list:
            tmp = NodeInfo()
            tmp.set_l1_fleet()
            node_dict[pair] = tmp

        ret = self.__enemy2_obj.match_objects(screen, self)
        sea_map[ret] = trans_consts.MAP_ENEMY
        l2_idx_list = zip(*np.where(ret))
        for pair in l2_idx_list:
            tmp = NodeInfo()
            tmp.set_l2_fleet()
            node_dict[pair] = tmp

        ret = self.__enemy3_obj.match_objects(screen, self)
        sea_map[ret] = trans_consts.MAP_ENEMY
        l3_idx_list = zip(*np.where(ret))
        for pair in l3_idx_list:
            tmp = NodeInfo()
            tmp.set_l3_fleet()
            node_dict[pair] = tmp

    def __match_character_tile_scale(self, screen, sea_map):
        """
        Find the tile where the character is located.
        Result will write into the corresponded tile in sea_map.
        Dependencies: init_map_coordinate
        :param screen: the color screen to find the boss icon
        :param sea_map: M x N numpy array
        :return:
        """

        ret = self.__arrow_obj.match_objects(screen, self)
        sea_map[ret] = trans_consts.MAP_CHARACTER

    def __match_boss_tile_scale(self, screen, sea_map):
        """
        Find the tile where the character is located.
        Result will write into the corresponded tile in sea_map.
        Dependencies: init_map_coordinate
        :param screen: the color screen to find the boss icon
        :param sea_map: M x N numpy array
        :return:
        """

        ret = self.__boss_obj.match_objects(screen, self)
        sea_map[ret] = trans_consts.MAP_BOSS

    def __match_supply_tile_scale(self, screen, sea_map, node_dict):

        ret = self.__ammo_obj.match_objects(screen, self)
        sea_map[ret] = trans_consts.MAP_SUPPLY
        ammo_idx_list = zip(*np.where(ret))
        for pair in ammo_idx_list:
            tmp = NodeInfo()
            tmp.set_ammo()
            node_dict[pair] = tmp

        ret = self.__mystery_obj.match_objects(screen, self)
        sea_map[ret] = trans_consts.MAP_SUPPLY
        mystery_idx_list = zip(*np.where(ret))
        for pair in mystery_idx_list:
            tmp = NodeInfo()
            tmp.set_mystery()
            node_dict[pair] = tmp

    def coord_to_map_index(self, coord):
        """
        Return the coordinate in the transformed space of the tile.
        Dependencies: init_map_coordinate
        :param coord: coordinate in the transformed space
        :return: tile index
        """
        col = int((coord[0] - self._top_left_tile_x) / trans_consts.TILE_WIDTH)
        row = int((coord[1] - self._top_left_tile_y) / trans_consts.TILE_HEIGHT)
        return [row, col]

    def map_index_to_coord(self, index):
        """
        Return the coordinate in the transformed space of the tile.
        Dependencies: init_map_coordinate
        :param index: tile index
        :return: coordinate of the tile in the transformed space.
        """
        x = self._top_left_tile_x + index[1] * trans_consts.TILE_WIDTH + trans_consts.TILE_WIDTH / 2
        y = self._top_left_tile_y + index[0] * trans_consts.TILE_HEIGHT + trans_consts.TILE_HEIGHT / 2
        return [x, y]

    def inv_transform_coord(self, coord):
        """
        Transform coordinate in homography transformed space to original space.
        Dependencies: init_map_coordinate
        :param coord: point in transformed space
        :return: point in the original space
        """
        point = np.array([[coord]], dtype=np.float32)
        inv_persp_point = cv2.perspectiveTransform(point, self._inv_h_trans_m)[0][0]
        inv_persp_point[0] += trans_consts.MAP_CROP_TOP_LEFT[0]
        inv_persp_point[1] += trans_consts.MAP_CROP_TOP_LEFT[1]
        return inv_persp_point

    def transform_coord(self, coord):
        """
        Transform coordinate in original space to homography transformed space.
        Dependencies: init_map_coordinate
        :param coord: point in original space
        :return: point in transformed space
        """
        point = np.array([[[coord[0] - trans_consts.MAP_CROP_TOP_LEFT[0],
                            coord[1] - trans_consts.MAP_CROP_TOP_LEFT[1]]]])
        persp_point = cv2.perspectiveTransform(point, self._h_trans_m)[0][0]
        return persp_point


class NodeInfo:
    class _EnemyType(enum.Enum):
        SIREN = enum.auto()
        NORMAL = enum.auto()
        BOSS = enum.auto()

    class _SupplyType(enum.Enum):
        AMMO = enum.auto()
        MYSTERY = enum.auto()

    def __init__(self):
        self.reset()

    def reset(self):
        self._enemy_type = None
        self._enemy_level = None
        self._supply_type = None

    def is_enemy(self):
        return self.is_normal() or self.is_siren()

    def is_siren(self):
        return self._enemy_type == self._EnemyType.SIREN

    def is_normal(self):
        return self._enemy_type == self._EnemyType.NORMAL

    def is_supply(self):
        return self.is_ammo() or self.is_mystery()

    def is_ammo(self):
        return self._supply_type == self._SupplyType.AMMO

    def is_mystery(self):
        return self._supply_type == self._SupplyType.MYSTERY

    def get_enemy_level(self):
        if self._enemy_type == self._EnemyType.NORMAL:
            return self._enemy_level
        else:
            return None

    def set_siren(self):
        self.reset()
        self._enemy_type = self._EnemyType.SIREN

    def set_l3_fleet(self):
        self.reset()
        self._enemy_type = self._EnemyType.NORMAL
        self._enemy_level = 3

    def set_l2_fleet(self):
        self.reset()
        self._enemy_type = self._EnemyType.NORMAL
        self._enemy_level = 2

    def set_l1_fleet(self):
        self.reset()
        self._enemy_type = self._EnemyType.NORMAL
        self._enemy_level = 1

    def set_ammo(self):
        self.reset()
        self._supply_type = self._SupplyType.AMMO

    def set_mystery(self):
        self.reset()
        self._supply_type = self._SupplyType.MYSTERY


class DetectionObjet:
    def __init__(self):
        self._img_path = None
        self._img = None
        self._scale_base = None
        self._search_rect = [1, 1]
        self._search_offset = [0, 0]
        self._match_threshold = 0.9

    def set_img_file_path(self, path):
        self._img_path = path

    def set_scale_base(self, base):
        self._scale_base = base

    def set_search_rect(self, rect):
        self._search_rect = rect

    def set_search_offset(self, offset):
        self._search_offset = offset

    def set_match_threshold(self, threshold):
        self._match_threshold = threshold

    def read_img_file(self):
        self._img = cv2.imread(self._img_path, cv2.IMREAD_COLOR)

    def match_objects(self, color_screen, homg):

        match_map = np.zeros(homg.get_map_shape(),dtype=bool)

        for i in range(homg._row_max_idx):
            p1 = np.array(homg.inv_transform_coord(
                [homg._top_left_tile_x, homg._top_left_tile_y + (i + 1) * trans_consts.TILE_HEIGHT]))
            p2 = np.array(homg.inv_transform_coord([homg._top_left_tile_x + trans_consts.TILE_WIDTH,
                                                    homg._top_left_tile_y + (i + 1) * trans_consts.TILE_HEIGHT]))
            s1 = np.array(homg.inv_transform_coord(
                [homg._top_left_tile_x, homg._top_left_tile_y + (i + 1) * trans_consts.TILE_HEIGHT]))
            s2 = np.array(homg.inv_transform_coord(
                [homg._top_left_tile_x, homg._top_left_tile_y + (i + 2) * trans_consts.TILE_HEIGHT]))
            real_tile_width = p2[0] - p1[0]
            real_tile_height = s2[1] - s1[1]
            ratio = real_tile_width / self._scale_base
            w_half = trans_consts.TILE_WIDTH * self._search_rect[0] / 2
            h_half = trans_consts.TILE_HEIGHT * self._search_rect[1] / 2
            scaled_x_offset = real_tile_width * self._search_offset[0]
            scaled_y_offset = real_tile_height * self._search_offset[1]
            scaled_img = cv2.resize(self._img, None, fx=ratio, fy=ratio)
            for j in range(homg._col_max_idx):
                c = homg.map_index_to_coord([i, j])
                rect = np.array(
                    [[homg.inv_transform_coord([c[0] - w_half, c[1] - h_half])],
                     [homg.inv_transform_coord([c[0] + w_half, c[1] - h_half])],
                     [homg.inv_transform_coord([c[0] + w_half, c[1] + h_half])],
                     [homg.inv_transform_coord([c[0] - w_half, c[1] + h_half])]],
                    dtype=np.float32)
                x, y, w, h = cv2.boundingRect(rect)
                x += scaled_x_offset
                y += scaled_y_offset

                x1 = int(x)
                x1 = x1 if x1 < color_screen.shape[1] else color_screen.shape[1]
                x2 = int(x + w)
                x2 = x2 if x2 < color_screen.shape[1] else color_screen.shape[1]
                y1 = int(y)
                y1 = y1 if y1 < color_screen.shape[0] else color_screen.shape[0]
                y2 = int(y + h)
                y2 = y2 if y2 < color_screen.shape[0] else color_screen.shape[0]

                if x1>=0 and x2>=0 and y1>=0 and y2>=0:
                    corp = color_screen[y1:y2, x1:x2, :]

                    if corp.shape[0] >= scaled_img.shape[0] and corp.shape[1] >= scaled_img.shape[1]:
                        res = cv2.matchTemplate(corp, scaled_img, cv2.TM_CCOEFF_NORMED)
                        max_similarity = np.max(res)
                        if max_similarity > self._match_threshold:
                            match_map[i, j] = 1


        return match_map
