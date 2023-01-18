from pygame.locals import *
import pygame
import sys
import random
#import noise
import json
from data import save
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

global path
path = os.path.dirname(os.path.realpath(__file__))

clock = pygame.time.Clock()

# get Config Files
f = open(f'{path}/data/config/config.json')
data = json.load(f)
width, height = data['config']['width'], data['config']['height']
WindowName = data['config']['name']
Version = data['config']['version']

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()  # initiates pygame
pygame.mixer.set_num_channels(64)

pygame.display.set_caption(WindowName + " " + Version)

WINDOW_SIZE = (width, height)

screen = pygame.display.set_mode(WINDOW_SIZE, 0, 32)  # initiate the window


display = pygame.Surface(
    (300, 200))  # used as the surface for rendering, which is scaled

moving_right = False
moving_left = False
vertical_momentum = 0
air_timer = 0
loadX, loadY, Seed = save.load()
true_scroll = [loadX, loadY]

CHUNK_SIZE = 8


def generate_chunk(x, y):
    chunk_data = []
    for y_pos in range(CHUNK_SIZE):
        for x_pos in range(CHUNK_SIZE):
            target_x = x * CHUNK_SIZE + x_pos
            target_y = y * CHUNK_SIZE + y_pos
            tile_type = 0  # nothing
            if x >= 9999 or x <= -9999:
                # int(noise.pnoise1(target_x * 0.1, repeat=999999) * 5)
                height = random.randrange(0, 21)
            else:
                height = 7
                #int(noise.pnoise1(target_x * 0.1, repeat=999999) * 5)

            if target_y > 8 - height:
                tile_type = 2  # dirt
            elif target_y == 8 - height:
                tile_type = 1  # grass
            elif target_y == 8 - height - 1:
                if random.randint(1, 5) == 1:
                    tile_type = 3  # plant
            if tile_type != 0:
                chunk_data.append([[target_x, target_y], tile_type])
    return chunk_data


global animation_frames
animation_frames = {}


def load_animation(path, frame_durations):
    global animation_frames
    animation_name = path.split('/')[-1]
    animation_frame_data = []
    n = 0
    for frame in frame_durations:
        animation_frame_id = animation_name + '_' + str(n)
        img_loc = path + '/' + animation_frame_id + '.png'
        # player_animations/idle/idle_0.png
        animation_image = pygame.image.load(img_loc).convert()
        animation_image.set_colorkey((255, 255, 255))
        animation_frames[animation_frame_id] = animation_image.copy()
        for i in range(frame):
            animation_frame_data.append(animation_frame_id)
        n += 1
    return animation_frame_data


def change_action(action_var, frame, new_value):
    if action_var != new_value:
        action_var = new_value
        frame = 0
    return action_var, frame


animation_database = {}

animation_database['run'] = load_animation('data/images/entities/player/run',
                                           [7, 7])
animation_database['idle'] = load_animation('data/images/entities/player/idle',
                                            [7, 7, 40])

game_map = {}

grass_img = pygame.image.load('./data/images/grass.png')
dirt_img = pygame.image.load('./data/images/dirt.png')
plant_img = pygame.image.load('./data/images/plant.png').convert()
plant_img.set_colorkey((255, 255, 255))

tile_index = {1: grass_img, 2: dirt_img, 3: plant_img}

jump_sound = pygame.mixer.Sound('./data/sound/jump.wav')
jump_sound.set_volume(0.2)
global music
music = pygame.mixer.music.load('./data/sound/music.wav')
grass_sounds = [
    pygame.mixer.Sound('./data/sound/grass_0.wav'),
    pygame.mixer.Sound('./data/sound/grass_1.wav')
]
grass_sounds[0].set_volume(0.2)
grass_sounds[1].set_volume(0.2)


player_action = 'idle'
player_frame = 0
player_flip = False

grass_sound_timer = 0

player_rect = pygame.Rect(100, 100, 5, 13)

background_objects = [[0.25, [120, 10, 70, 400]], [0.25, [280, 30, 40, 400]],
                      [0.5, [30, 40, 40, 400]], [0.5, [130, 90, 100, 400]],
                      [0.5, [300, 80, 120, 400]]]


def collision_test(rect, tiles):
    hit_list = []
    for tile in tiles:
        if rect.colliderect(tile):
            hit_list.append(tile)
    return hit_list


def move(rect, movement, tiles):
    collision_types = {
        'top': False,
        'bottom': False,
        'right': False,
        'left': False
    }
    rect.x += movement[0]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[0] > 0:
            rect.right = tile.left
            collision_types['right'] = True
        elif movement[0] < 0:
            rect.left = tile.right
            collision_types['left'] = True
    rect.y += movement[1]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[1] > 0:
            rect.bottom = tile.top
            collision_types['bottom'] = True
        elif movement[1] < 0:
            rect.top = tile.bottom
            collision_types['top'] = True
    return rect, collision_types


    
player_rect.x = true_scroll[0]
player_rect.y = true_scroll[1]
playing = False
pygame.mixer.music.set_volume(0.2)

while True:  # game loop
    display.fill((146, 244, 255))  # clear screen by filling it with blue
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.play()
        
        

    if grass_sound_timer > 0:
        grass_sound_timer -= 1

    true_scroll[0] += (player_rect.x - true_scroll[0] - 152) / 20
    true_scroll[1] += (player_rect.y - true_scroll[1] - 106) / 20
    scroll = true_scroll.copy()
    scroll[0] = int(scroll[0])
    scroll[1] = int(scroll[1])

    pygame.draw.rect(display, (7, 80, 75), pygame.Rect(0, 120, 300, 80))
    for background_object in background_objects:
        obj_rect = pygame.Rect(
            background_object[1][0] - scroll[0] * background_object[0],
            background_object[1][1] - scroll[1] * background_object[0],
            background_object[1][2], background_object[1][3])
        if background_object[0] == 0.5:
            pygame.draw.rect(display, (20, 170, 150), obj_rect)
        else:
            pygame.draw.rect(display, (15, 76, 73), obj_rect)

    tile_rects = []
    print(scroll[0], scroll[1])
    for y in range(3):
        for x in range(4):
            target_x = x - 1 + int(round(scroll[0] / (CHUNK_SIZE * 16)))
            target_y = y - 1 + int(round(scroll[1] / (CHUNK_SIZE * 16)))
            target_chunk = str(target_x) + ';' + str(target_y)
            if target_chunk not in game_map:
                game_map[target_chunk] = generate_chunk(target_x, target_y)

            for tile in game_map[target_chunk]:
                display.blit(
                    tile_index[tile[1]],
                    (tile[0][0] * 16 - scroll[0], tile[0][1] * 16 - scroll[1]))
                if tile[1] in [1, 2]:
                    tile_rects.append(
                        pygame.Rect(tile[0][0] * 16, tile[0][1] * 16, 16, 16))

    player_movement = [0, 0]
    if moving_right == True:
        player_movement[0] += 2
    if moving_left == True:
        player_movement[0] -= 2
    player_movement[1] += vertical_momentum
    vertical_momentum += 0.2
    if vertical_momentum > 3:
        vertical_momentum = 3

    if player_movement[0] == 0:
        player_action, player_frame = change_action(player_action, player_frame,
                                                    'idle')
    if player_movement[0] > 0:
        player_flip = False
        player_action, player_frame = change_action(player_action, player_frame,
                                                    'run')
    if player_movement[0] < 0:
        player_flip = True
        player_action, player_frame = change_action(player_action, player_frame,
                                                    'run')

    player_rect, collisions = move(player_rect, player_movement, tile_rects)

    if collisions['bottom'] == True:
        air_timer = 0
        vertical_momentum = 0
        if player_movement[0] != 0:
            if grass_sound_timer == 0:
                grass_sound_timer = 30
                random.choice(grass_sounds).play()
    else:
        air_timer += 1

    player_frame += 1
    if player_frame >= len(animation_database[player_action]):
        player_frame = 0
    player_img_id = animation_database[player_action][player_frame]
    player_img = animation_frames[player_img_id]
    display.blit(pygame.transform.flip(player_img, player_flip, False),
                 (player_rect.x - scroll[0], player_rect.y - scroll[1]))

    for event in pygame.event.get():  # event loop
        if event.type == QUIT:
            save.save((player_rect.x), (player_rect.y))
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_w:
                pygame.mixer.music.fadeout(1000)
            if event.key == K_RIGHT:
                moving_right = True
            if event.key == K_LEFT:
                moving_left = True
            if event.key == K_UP:
                if air_timer < 6:
                    jump_sound.play()
                    vertical_momentum = -5
        if event.type == KEYUP:
            if event.key == K_RIGHT:
                moving_right = False
            if event.key == K_LEFT:
                moving_left = False

    screen.blit(pygame.transform.scale(display, WINDOW_SIZE), (0, 0))
    pygame.display.update()
    clock.tick(60)
