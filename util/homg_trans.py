import cv2
import numpy as np
import enum
import util.homg_trans_consts as trans_consts


class HomographyTransform:
    """
    Dependencies of each function must be executed at least once before calling it.
    """

    def __init__(self):
        self.__top_left_tile_x = None
        self.__top_left_tile_y = None
        self.__col_max_idx = None
        self.__row_max_idx = None
        self.__screen = None
        self.__color_screen = None
        self.__h_trans_m = None
        self.__inv_h_trans_m = None
        self.__h_trans_screen_size = None
        self.__small_boss_icon = False
        self.__debug_enabled = False
        self.__debug_out_func = None

        self.__free_tile_center_img = cv2.imread(trans_consts.FREE_TILE_CENTER_IMG, cv2.IMREAD_GRAYSCALE)
        self.__free_tile_imgs = [cv2.imread(trans_consts.FREE_TILES_IMG_UP, cv2.IMREAD_GRAYSCALE),
                                 cv2.imread(trans_consts.FREE_TILES_IMG_DOWN, cv2.IMREAD_GRAYSCALE),
                                 cv2.imread(trans_consts.FREE_TILES_IMG_LEFT, cv2.IMREAD_GRAYSCALE),
                                 cv2.imread(trans_consts.FREE_TILES_IMG_RIGHT, cv2.IMREAD_GRAYSCALE)]

        self.__free_tile_lu = cv2.imread(trans_consts.FREE_TILES_LU_IMG, cv2.IMREAD_GRAYSCALE)
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
        self.__h_trans_m = shifted_transf / shifted_transf[2, 2]
        self.__inv_h_trans_m = cv2.invert(shifted_transf)[1]
        self.__h_trans_screen_size = (anchor_x + max(max_x, src_w), anchor_y + max(max_y, src_h))

    def use_small_boss_icon(self, val):
        """
        Set using small boss icon
        :param val: True if using small boss icon. False if using normal icon.
        :return:
        """
        self.__small_boss_icon = val

    def enable_debug_log(self, enable, debug_out_func):
        if enable and debug_out_func is None:
            return False
        self.__debug_enabled = enable
        if self.__debug_enabled:
            self.__debug_out_func = debug_out_func
        return True

    def load_color_screen(self, color_screen):
        """
        Load the color screen.
        """
        self.__color_screen = color_screen
        self.__screen = cv2.cvtColor(color_screen, cv2.COLOR_BGR2GRAY)

    def init_map_coordinate(self):
        """
        Calculate the coordinates of the tiles on the map.
        Try swiping the map if it returns false.
        Dependencies: init_homg_vars, load_color_screen
        :return: True if successfully initialize the coordinates of the tiles. False otherwise.
        """
        # crop the color screen
        free_tile_center = self.__free_tile_center_img

        crop_color_screen = self.__color_screen[:][
                            trans_consts.MAP_CROP_TOP_LEFT[1]:trans_consts.MAP_CROP_BOTTOM_RIGHT[1],
                            trans_consts.MAP_CROP_TOP_LEFT[0]:trans_consts.MAP_CROP_BOTTOM_RIGHT[0]]
        # Warp source image to destination based on homography
        screen_trans = cv2.warpPerspective(crop_color_screen, self.__h_trans_m, self.__h_trans_screen_size)
        screen_edge = cv2.Canny(screen_trans, trans_consts.CV_CANNY_MIN, trans_consts.CV_CANNY_MAX)

        closing_kernel = trans_consts.CLOSING_KERNEL_MIN_SIZE
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (closing_kernel, closing_kernel))
        screen_edge_closed = cv2.morphologyEx(screen_edge, cv2.MORPH_CLOSE, kernel)
        res = cv2.matchTemplate(screen_edge_closed, free_tile_center, cv2.TM_CCOEFF_NORMED)
        max_similarity = np.max(res)
        if self.__debug_enabled:
            self.__debug_out_func("free tile center", max_similarity)
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
        self.__top_left_tile_x = int(x % trans_consts.TILE_WIDTH)
        self.__top_left_tile_y = int(y % trans_consts.TILE_HEIGHT)
        self.__row_max_idx = int(
            (self.__h_trans_screen_size[
                 1] - self.__top_left_tile_y + trans_consts.TILE_HEIGHT - 1) / trans_consts.TILE_HEIGHT)
        self.__col_max_idx = int(
            (self.__h_trans_screen_size[
                 0] - self.__top_left_tile_x + trans_consts.TILE_WIDTH - 1) / trans_consts.TILE_WIDTH)

        return True

    def get_map_shape(self):
        """
         Return the shape of the map which will be returned in create_map()
         Dependencies: init_map_coordinate
         """
        return (self.__row_max_idx, self.__col_max_idx)

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
        crop_color_screen = self.__color_screen[:][
                            trans_consts.MAP_CROP_TOP_LEFT[1]:trans_consts.MAP_CROP_BOTTOM_RIGHT[1],
                            trans_consts.MAP_CROP_TOP_LEFT[0]:trans_consts.MAP_CROP_BOTTOM_RIGHT[0]]
        # Warp source image to destination based on homography
        screen_trans = cv2.warpPerspective(crop_color_screen, self.__h_trans_m, self.__h_trans_screen_size)
        screen_edge = cv2.Canny(screen_trans, trans_consts.CV_CANNY_MIN, trans_consts.CV_CANNY_MAX)

        sea_map = np.zeros(shape=(self.__row_max_idx, self.__col_max_idx))

        free_tile_lu_scaled = cv2.resize(self.__free_tile_lu,
                                         (self.__free_tile_lu.shape[1] * 2, self.__free_tile_lu.shape[0] * 2)).astype(
            np.uint8)

        for j in range(self.__row_max_idx):
            for i in range(self.__col_max_idx):
                cur_x = self.__top_left_tile_x + i * trans_consts.TILE_WIDTH
                cur_y = self.__top_left_tile_y + j * trans_consts.TILE_HEIGHT
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

        self.__match_mob_tile_scale(self.__color_screen, sea_map, node_dict)
        self.__match_character_tile_scale(self.__color_screen, sea_map)
        self.__match_boss_tile_scale(self.__color_screen, sea_map)

        if self.__debug_enabled:
            self.debug_output(sea_map)
            self.__debug_out_func('Read Map:\n{}'.format(np.array2string(sea_map)))

        if node_info:
            return sea_map, node_dict
        else:
            return sea_map

    def debug_output(self, sea_map):
        crop_color_screen = self.__color_screen[:][
                            trans_consts.MAP_CROP_TOP_LEFT[1]:trans_consts.MAP_CROP_BOTTOM_RIGHT[1],
                            trans_consts.MAP_CROP_TOP_LEFT[0]:trans_consts.MAP_CROP_BOTTOM_RIGHT[0]]
        screen_trans = cv2.warpPerspective(crop_color_screen, self.__h_trans_m, self.__h_trans_screen_size)
        screen_edge = cv2.Canny(screen_trans, trans_consts.CV_CANNY_MIN, trans_consts.CV_CANNY_MAX)

        for i in range(self.__col_max_idx):
            for j in range(self.__row_max_idx):
                cur_x = self.__top_left_tile_x + i * trans_consts.TILE_WIDTH
                cur_y = self.__top_left_tile_y + j * trans_consts.TILE_HEIGHT
                rect = np.array(
                    [[[cur_x, cur_y]], [[cur_x + trans_consts.TILE_WIDTH, cur_y]],
                     [[cur_x + trans_consts.TILE_WIDTH, cur_y + trans_consts.TILE_HEIGHT]],
                     [[cur_x, cur_y + trans_consts.TILE_HEIGHT]]],
                    dtype=np.float64)
                rect = cv2.perspectiveTransform(rect, self.__inv_h_trans_m)
                rect = rect.astype(int)
                cv2.drawContours(crop_color_screen, [rect], -1, (255, 0, 0), 3)

                dot = np.array(
                    [[[cur_x + trans_consts.TILE_WIDTH / 2, cur_y + trans_consts.TILE_HEIGHT / 2]]])
                dot = cv2.perspectiveTransform(dot, self.__inv_h_trans_m)
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

        scaling_base = trans_consts.SCALING_BASE

        if self.__row_max_idx < 2:
            return
        for i in range(self.__row_max_idx):
            p1 = np.array(self.inv_transform_coord(self.map_index_to_coord((i, 0))))
            p2 = np.array(self.inv_transform_coord(self.map_index_to_coord((i, 1))))
            dist = np.linalg.norm(p1 - p2, ord=2)
            scale = dist / scaling_base
            e1_scaled = cv2.resize(self.__enemy1_img, None, fx=scale, fy=scale)
            e2_scaled = cv2.resize(self.__enemy2_img, None, fx=scale, fy=scale)
            e3_scaled = cv2.resize(self.__enemy3_img, None, fx=scale, fy=scale)
            search_square_edge = int(trans_consts.SCALED_ENEMY_MATCH_SQUARE_SIDE * scale)
            search_x_offset = int(trans_consts.SCALED_ENEMY_X_OFFSET * scale)
            search_y_offset = int(trans_consts.SCALED_ENEMY_Y_OFFSET * scale)
            for j in range(self.__col_max_idx):
                tile_center = self.map_index_to_coord((i, j))
                tile_corner = np.subtract(tile_center, [trans_consts.TILE_WIDTH / 2, trans_consts.TILE_HEIGHT / 2])
                org_tile_corner = np.array(self.inv_transform_coord(tile_corner), dtype=np.int)
                org_tile_corner[0] += search_x_offset
                org_tile_corner[1] += search_y_offset
                corp = screen[org_tile_corner[1]:org_tile_corner[1] + search_square_edge,
                       org_tile_corner[0]:org_tile_corner[0] + search_square_edge, :]
                if corp.shape[0] >= e1_scaled.shape[0] and corp.shape[1] >= e1_scaled.shape[1]:
                    res = cv2.matchTemplate(corp, e1_scaled, cv2.TM_CCOEFF_NORMED)
                    max_similarity = np.max(res)
                    if max_similarity > trans_consts.SCALED_ENEMY_MATCH_THRESH:
                        sea_map[i, j] = trans_consts.MAP_ENEMY
                        tmp = NodeInfo()
                        tmp.set_l1_fleet()
                        node_dict[(i, j)] = tmp

                if corp.shape[0] >= e2_scaled.shape[0] and corp.shape[1] >= e2_scaled.shape[1]:
                    res = cv2.matchTemplate(corp, e2_scaled, cv2.TM_CCOEFF_NORMED)
                    max_similarity = np.max(res)
                    if max_similarity > trans_consts.SCALED_ENEMY_MATCH_THRESH:
                        sea_map[i, j] = trans_consts.MAP_ENEMY
                        tmp = NodeInfo()
                        tmp.set_l2_fleet()
                        node_dict[(i, j)] = tmp

                if corp.shape[0] >= e3_scaled.shape[0] and corp.shape[1] >= e3_scaled.shape[1]:
                    res = cv2.matchTemplate(corp, e3_scaled, cv2.TM_CCOEFF_NORMED)
                    max_similarity = np.max(res)
                    if max_similarity > trans_consts.SCALED_ENEMY_MATCH_THRESH:
                        sea_map[i, j] = trans_consts.MAP_ENEMY
                        tmp = NodeInfo()
                        tmp.set_l3_fleet()
                        node_dict[(i, j)] = tmp

    def __match_character_tile_scale(self, screen, sea_map):
        """
        Find the tile where the character is located.
        Result will write into the corresponded tile in sea_map.
        Dependencies: init_map_coordinate
        :param screen: the color screen to find the boss icon
        :param sea_map: M x N numpy array
        :return:
        """

        scaling_base = trans_consts.SCALING_BASE

        if self.__row_max_idx < 2:
            return

        for i in range(self.__row_max_idx):
            p1 = np.array(self.inv_transform_coord(self.map_index_to_coord((i, 0))))
            p2 = np.array(self.inv_transform_coord(self.map_index_to_coord((i, 1))))
            dist = np.linalg.norm(p1 - p2, ord=2)
            scale = dist / scaling_base
            arrow = cv2.resize(self.__arrow_img, None, fx=scale, fy=scale)
            search_square_edge = int(trans_consts.SCALED_ARROW_MATCH_SQUARE_SIDE * scale)
            search_x_offset = int(trans_consts.SCALED_ARROW_X_OFFSET * scale)
            search_y_offset = int(trans_consts.SCALED_ARROW_Y_OFFSET * scale)
            for j in range(self.__col_max_idx):
                tile_center = self.map_index_to_coord((i, j))
                tile_corner = np.subtract(tile_center, [trans_consts.TILE_WIDTH / 2, trans_consts.TILE_HEIGHT / 2])
                org_tile_corner = np.array(self.inv_transform_coord(tile_corner), dtype=np.int)
                org_tile_corner[0] += search_x_offset
                org_tile_corner[1] += search_y_offset
                corp = screen[org_tile_corner[1]:org_tile_corner[1] + search_square_edge,
                       org_tile_corner[0]:org_tile_corner[0] + search_square_edge, :]
                if corp.shape[0] >= arrow.shape[0] and corp.shape[1] >= arrow.shape[1]:
                    res = cv2.matchTemplate(corp, arrow, cv2.TM_CCOEFF_NORMED)
                    max_similarity = np.max(res)
                    if max_similarity > trans_consts.SCALED_ARROW_MATCH_THRESH:
                        sea_map[i, j] = trans_consts.MAP_CHARACTER

    def __match_boss_tile_scale(self, screen, sea_map):
        """
        Find the tile where the character is located.
        Result will write into the corresponded tile in sea_map.
        Dependencies: init_map_coordinate
        :param screen: the color screen to find the boss icon
        :param sea_map: M x N numpy array
        :return:
        """

        scaling_base = trans_consts.SCALING_BASE

        if self.__row_max_idx < 2:
            return

        for i in range(self.__row_max_idx):
            p1 = np.array(self.inv_transform_coord(self.map_index_to_coord((i, 0))))
            p2 = np.array(self.inv_transform_coord(self.map_index_to_coord((i, 1))))
            dist = np.linalg.norm(p1 - p2, ord=2)
            scale = dist / scaling_base
            boss = cv2.resize(self.__boss_img, None, fx=scale, fy=scale)
            for j in range(self.__col_max_idx):
                cur_x = self.__top_left_tile_x + j * trans_consts.TILE_WIDTH
                cur_y = self.__top_left_tile_y + i * trans_consts.TILE_HEIGHT
                rect = np.array(
                    [[self.inv_transform_coord([cur_x, cur_y])],
                     [self.inv_transform_coord([cur_x + trans_consts.TILE_WIDTH, cur_y])],
                     [self.inv_transform_coord([cur_x + trans_consts.TILE_WIDTH, cur_y + trans_consts.TILE_HEIGHT])],
                     [self.inv_transform_coord([cur_x, cur_y + trans_consts.TILE_HEIGHT])]],
                    dtype=np.float32)
                x, y, w, h = cv2.boundingRect(rect)
                corp = screen[y:y + h, x:x + w, :]
                if corp.shape[0] >= boss.shape[0] and corp.shape[1] >= boss.shape[1]:
                    res = cv2.matchTemplate(corp, boss, cv2.TM_CCOEFF_NORMED)
                    max_similarity = np.max(res)
                    if max_similarity > trans_consts.SCALED_ARROW_MATCH_THRESH:
                        sea_map[i, j] = trans_consts.MAP_BOSS

    def coord_to_map_index(self, coord):
        """
        Return the coordinate in the transformed space of the tile.
        Dependencies: init_map_coordinate
        :param coord: coordinate in the transformed space
        :return: tile index
        """
        col = int((coord[0] - self.__top_left_tile_x) / trans_consts.TILE_WIDTH)
        row = int((coord[1] - self.__top_left_tile_y) / trans_consts.TILE_HEIGHT)
        return [row, col]

    def map_index_to_coord(self, index):
        """
        Return the coordinate in the transformed space of the tile.
        Dependencies: init_map_coordinate
        :param index: tile index
        :return: coordinate of the tile in the transformed space.
        """
        x = self.__top_left_tile_x + index[1] * trans_consts.TILE_WIDTH + trans_consts.TILE_WIDTH / 2
        y = self.__top_left_tile_y + index[0] * trans_consts.TILE_HEIGHT + trans_consts.TILE_HEIGHT / 2
        return [x, y]

    def inv_transform_coord(self, coord):
        """
        Transform coordinate in homography transformed space to original space.
        Dependencies: init_map_coordinate
        :param coord: point in transformed space
        :return: point in the original space
        """
        point = np.array([[coord]], dtype=np.float32)
        inv_persp_point = cv2.perspectiveTransform(point, self.__inv_h_trans_m)[0][0]
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
        persp_point = cv2.perspectiveTransform(point, self.__h_trans_m)[0][0]
        return persp_point

    def bfs_search(self, sea_map, start_tile):
        """
        Do a BFS search on sea_map starting from start_tile.
        The object on start_tile will be ignored.
        :param sea_map: map created by create_map()
        :param start_tile: the index of the tile to start BFS
        :return: found_enemies and found_supplies, both sorted from the nearest to the farthest.
        """

        if start_tile[0] < 0 or start_tile[0] >= sea_map.shape[0] or start_tile[1] < 0 or start_tile[1] >= \
                sea_map.shape[1]:
            return [], []

        pad_map = np.zeros(shape=(sea_map.shape[0] + 2, sea_map.shape[1] + 2))
        pad_map[1:sea_map.shape[0] + 1, 1:sea_map.shape[1] + 1] = sea_map[:, :]
        visited_map = np.zeros(shape=pad_map.shape)
        queue = []
        found_enemies = []
        found_supplies = []

        cur = (start_tile[0] + 1, start_tile[1] + 1)
        queue.append(cur)
        visited_map[cur] = -1
        while len(queue) > 0:
            new_queue = []
            for cur in queue:
                next_locs = [(cur[0] - 1, cur[1]), (cur[0] + 1, cur[1]), (cur[0], cur[1] - 1), (cur[0], cur[1] + 1)]
                for i in range(4):
                    loc = next_locs[i]
                    if visited_map[loc] == 0:
                        visited_map[loc] = i + 1
                        if pad_map[loc] == trans_consts.MAP_ENEMY or pad_map[loc] == trans_consts.MAP_BOSS:
                            found_enemies.append((loc[0] - 1, loc[1] - 1))
                        elif pad_map[loc] == trans_consts.MAP_SUPPLY:
                            found_supplies.append((loc[0] - 1, loc[1] - 1))
                        elif pad_map[loc] == trans_consts.MAP_FREE or pad_map[loc] == trans_consts.MAP_CHARACTER:
                            new_queue.append(loc)
            queue = new_queue
        return found_enemies, found_supplies


class NodeInfo:
    class _EnemyType(enum.Enum):
        SIREN = enum.auto()
        NORMAL = enum.auto()
        BOSS = enum.auto()

    def __init__(self):
        self.reset()

    def reset(self):
        self._is_ammo = False
        self._is_supply = False
        self._enemy_type = None
        self._enemy_level = None

    def is_siren(self):
        return self._enemy_type == self._EnemyType.SIREN

    def is_normal(self):
        return self._enemy_type == self._EnemyType.NORMAL

    def get_enemy_level(self):
        if self._enemy_type == self._EnemyType.NORMAL:
            return self._enemy_level
        else:
            return None

    def set_siren(self):
        self._enemy_type = self._EnemyType.SIREN

    def set_l3_fleet(self):
        self._enemy_type = self._EnemyType.NORMAL
        self._enemy_level = 3

    def set_l2_fleet(self):
        self._enemy_type = self._EnemyType.NORMAL
        self._enemy_level = 2

    def set_l1_fleet(self):
        self._enemy_type = self._EnemyType.NORMAL
        self._enemy_level = 1
