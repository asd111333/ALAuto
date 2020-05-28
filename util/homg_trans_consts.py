# Image file paths
FREE_TILES_LU_IMG = 'assets/map_detection/free_tile_lu.png'
FREE_TILE_CENTER_IMG = 'assets/map_detection/free_tile_center.png'
ENEMY_1_IMG = 'assets/map_detection/e1.png'
ENEMY_2_IMG = 'assets/map_detection/e2.png'
ENEMY_3_IMG = 'assets/map_detection/e3.png'
ARROW_IMG = 'assets/map_detection/arrow.png'
BOSS_IMG = 'assets/map_detection/boss.png'
MYSTERY_IMG = 'assets/map_detection/mystery.png'
AMMO_IMG = 'assets/map_detection/ammo.png'

MAP_OBJ_TYPES = 6
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
MAP_CROP_BOTTOM_RIGHT = [1920, 1080]
# normal maps
TRANS_SRC_PTS = [[430, 790], [630, 790], [616, 950], [407, 950]]
TRANS_DST_PTS = [[430, 790], [630, 790], [630, 990], [430, 990]]
#D3
#TRANS_SRC_PTS = [[1005, 566], [1327, 566], [1009, 837], [1350, 837]]
#TRANS_DST_PTS = [[1005, 566], [1005 + 2*TILE_WIDTH, 566], [1005, 566 + 2*TILE_HEIGHT], [1005 + 2*TILE_WIDTH, 566 + 2*TILE_HEIGHT]]

CV_CANNY_MIN = 50
CV_CANNY_MAX = 100
CLOSING_KERNEL_MIN_SIZE = 5
CLOSING_KERNEL_MAX_SIZE = 25
CLOSING_KERNEL_INCR_STEP = 5
FREE_TILE_MATCH_THRESH = 0.8
BOUNDARY_RED_LOWER = [160, 70, 240]
BOUNDARY_RED_UPPER = [180, 255, 255]
BOUNDARY_YELLOW_LOWER = [25, 100, 100]
BOUNDARY_YELLOW_UPPER = [35, 255, 255]
BOUNDARY_RED_COUNT_THRESH = 1000
BOUNDARY_YELLOW_COUNT_THRESH = 1000
BOUNDARY_DETECT_MASK_PERCENTAGE = 0.1
FREE_TILE_CENTER_THRESH = 0.9
FREE_TILE_X_OFFSET = -70
FREE_TILE_Y_OFFSET = -70

# detection methods that scale the image based on tile width
# offsets are calculated from the center of the tile with lower width = X_BASE
ARROW_SCALE = 195
ARROW_OFFSET = [0, -1.8]
ARROW_SEARCH_RECT = [0.75, 0.75]

BOSS_SCALE = 195
BOSS_OFFSET = [0, 0]
BOSS_SEARCH_RECT = [1, 1]

ENEMY_SCALE = 195
ENEMY_OFFSET = [-0.4, -0.65]
ENEMY_SEARCH_RECT = [0.75, 0.75]

MYSTERY_SCALE = 208
MYSTERY_OFFSET = [0, -0.5]
MYSTERY_SEARCH_RECT = [1, 1]


AMMO_SCALE = 215
AMMO_OFFSET = [0, -0.5]
AMMO_SEARCH_RECT = [1, 1]