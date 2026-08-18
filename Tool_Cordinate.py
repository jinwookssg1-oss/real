def world_to_screen(world_x, world_y, camera_x, camera_y):
    return world_x - camera_x, world_y - camera_y


def screen_to_world(screen_x, screen_y, camera_x, camera_y):
    return screen_x + camera_x, screen_y + camera_y


def get_object_world_center(obj_x, obj_y, obj_width, obj_height):
    return obj_x + (obj_width // 2), obj_y + (obj_height // 2)


def get_object_screen_center(obj_x, obj_y, obj_width, obj_height, camera_x, camera_y):
    screen_x, screen_y = world_to_screen(obj_x, obj_y, camera_x, camera_y)
    return screen_x + (obj_width // 2), screen_y + (obj_height // 2)


def get_player_world_center(player_x, player_y, player_width, player_height):
    return get_object_world_center(player_x, player_y, player_width, player_height)


def get_player_screen_center(player_x, player_y, player_width, player_height, camera_x, camera_y):
    return get_object_screen_center(player_x, player_y, player_width, player_height, camera_x, camera_y)


def get_camera_target(player_world_center_x, player_world_center_y, screen_width, screen_height):
    return player_world_center_x - (screen_width // 2), player_world_center_y - (screen_height // 2)
