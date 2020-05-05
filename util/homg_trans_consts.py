# Image file paths
FREE_TILES_IMG_UP = 'assets/map_detection/free_tile_u.png'
FREE_TILES_IMG_DOWN = 'assets/map_detection/free_tile_d.png'
FREE_TILES_IMG_LEFT = 'assets/map_detection/free_tile_l.png'
FREE_TILES_IMG_RIGHT = 'assets/map_detection/free_tile_r.png'
TRANS_ARROW_IMG = 'assets/map_detection/persp_arrow.png'
TRANS_BOSS_IMG = 'assets/map_detection/persp_boss.png'
TRANS_SMALL_BOSS_IMG = 'assets/map_detection/persp_boss_small.png'
TRANS_QUESTION_MARK_IMG = 'assets/map_detection/persp_qmark.png'
FREE_TILE_CENTER_IMG = 'assets/map_detection/free_tile_center.png'
ENEMY_1_IMG = 'assets/map_detection/e1.png'
ENEMY_2_IMG = 'assets/map_detection/e2.png'
ENEMY_3_IMG = 'assets/map_detection/e3.png'
ARROW_IMG = 'assets/map_detection/arrow.png'

# Constants used in the returned map
MAP_OBSTACLE = 0
MAP_FREE = 1
MAP_CHARACTER = 2
MAP_SUPPLY = 3
MAP_ENEMY = 4
MAP_BOSS = 5

# Constants used in the class
TILE_WIDTH = 209
TILE_HEIGHT = 209
# MAP_CROP_TOP_LEFT = [185, 240]
MAP_CROP_TOP_LEFT = [185, 170]
# MAP_CROP_BOTTOM_RIGHT = [1795, 945]
MAP_CROP_BOTTOM_RIGHT = [1795, 1080]
# normal maps
#TRANS_SRC_PTS = [[430, 790], [630, 790], [616, 950], [407, 950]]
#TRANS_DST_PTS = [[430, 790], [630, 790], [630, 990], [430, 990]]
# crimson echoes
TRANS_SRC_PTS = [[816, 270], [1168, 270], [805, 518], [1187, 518]]
TRANS_DST_PTS = [[816, 270], [816 + 2*TILE_WIDTH, 270], [816, 270 + 2*TILE_HEIGHT], [816 + 2*TILE_WIDTH, 270 + 2*TILE_HEIGHT]]

CV_CANNY_MIN = 50
CV_CANNY_MAX = 100
CLOSING_KERNEL_MIN_SIZE = 5
CLOSING_KERNEL_MAX_SIZE = 25
CLOSING_KERNEL_INCR_STEP = 5
FREE_TILE_MATCH_THRESH = 0.7
BOUNDARY_RED_LOWER = [160, 70, 240]
BOUNDARY_RED_UPPER = [180, 255, 255]
BOUNDARY_YELLOW_LOWER = [25, 100, 100]
BOUNDARY_YELLOW_UPPER = [35, 255, 255]
BOUNDARY_RED_COUNT_THRESH = 600
BOUNDARY_YELLOW_COUNT_THRESH = 600
BOUNDARY_DETECT_MASK_PERCENTAGE = 0.2
ARROW_MATCH_THRESH = 0.9
FREE_TILE_CENTER_THRESH = 0.9
FREE_TILE_X_OFFSET = -70
FREE_TILE_Y_OFFSET = -70
ARROW_CHARACTER_Y_OFFSET = TILE_HEIGHT * 2.25
BOSS_MATCH_THRESH = 0.9

# detection methods that scale the image based on tile width
# offsets are calculated from the upper left corner of the tile with lower width = SCALING_BASE
SCALING_BASE = 195
SCALED_ARROW_MATCH_SQUARE_SIDE = 140
SCALED_ARROW_X_OFFSET = 0
SCALED_ARROW_Y_OFFSET = -2.2 * SCALED_ARROW_MATCH_SQUARE_SIDE
SCALED_ARROW_MATCH_THRESH = 0.9

SCALED_ENEMY_MATCH_SQUARE_SIDE = 80
SCALED_ENEMY_X_OFFSET = -1 / 4 * SCALED_ENEMY_MATCH_SQUARE_SIDE
SCALED_ENEMY_Y_OFFSET = -4 / 5 * SCALED_ENEMY_MATCH_SQUARE_SIDE
SCALED_ENEMY_MATCH_THRESH = 0.9
