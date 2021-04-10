import pygame
from sys import exit
from math import sin, cos, radians
from random import random
import socket
import json
from time import sleep

def game_over(p2lost, p1lost):
    print("Game Over!")
    print('Winner: ', 'player 1' if p2lost else 'player 2')
    send(DISCONNECT_MSG)
    # gameInit()

# consts
ball_velocity = 6

# ball vel angle in degrees
ball_angle = 30
SCREEN_SIZE = (800, 500)
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_SIZE
SCREEN_CENTER_Y = SCREEN_HEIGHT//2
PADDLE_SIZE = (25, 110)
PADDLE_WIDTH, PADDLE_HEIGHT = PADDLE_SIZE
PLAYERNUM = None

PORT = 5050
SERVER_IP = "YOUR_PONG_SERVER_IP_HERE" # run the command " socket.gethostbyname(socket.gethostname()) " on your server and paste that IP here
ADDR = (SERVER_IP, PORT)
MSG_HEADER_SIZE = 64
FORMAT = 'utf-8'
DISCONNECT_MSG = '{ }'
READY_MSG = 'ready'

my_data = {
    'mypaddle_y': SCREEN_CENTER_Y,
    'player_num': None,
    'ready': True
}

# network stuff
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE) # display surface

# setting fixed framerate to avoid unstable framerates and inconsistent game speeds
clock = pygame.time.Clock()

# images (surfaces)
bg_surface = pygame.image.load('./background.png').convert()
paddle_img = pygame.image.load('./paddle.png').convert()
paddle_img2 = pygame.image.load('./paddle.png').convert()
ball_img = pygame.image.load('./ball.png').convert()

# coords
paddle1y = SCREEN_CENTER_Y
paddle2y = SCREEN_CENTER_Y
ballx, bally = 400, 250

# key pressed
pressed_keys = [False, False] # [UP, DOWN]

# rects
paddle1rect = paddle_img.get_rect(center=(PADDLE_WIDTH//2, paddle1y))
paddle2rect = paddle_img2.get_rect(center=(SCREEN_WIDTH - PADDLE_WIDTH//2, paddle2y))
ballrect = ball_img.get_rect(center=(ballx, bally))

def initVars(config):
    # consts
    global ball_velocity
    global ball_angle
    global PLAYERNUM
    global paddle1y
    global paddle2y
    global ballx
    global bally
    global is_game_over
    ball_angle = config['ball_angle']
    ball_velocity = config['ball_velocity']
    PLAYERNUM = config['your_playernum']
    paddle1y = config['P1_y']
    paddle2y = config['P2_y']
    ballx = config['ball_x']
    bally = config['ball_y']
    is_game_over = config['game_over']


response = {}
def send(msg):
    message = msg.encode(FORMAT)
    msg_len = len(message)
    send_length = str(msg_len).encode(FORMAT)
    send_length += b' ' * (MSG_HEADER_SIZE - len(send_length))
    client.send(send_length)
    client.send(message)
    global response
    global PLAYERNUM
    if msg != DISCONNECT_MSG:
        response = json.loads(client.recv(2048).decode(FORMAT))
        PLAYERNUM = response['your_playernum']
    # print('Response from server: ', response) # DEBUG
    return response

def send_info(info):
    message = info.encode(FORMAT)
    msg_len = len(message)
    send_length = str(msg_len).encode(FORMAT)
    send_length += b' ' * (MSG_HEADER_SIZE - len(send_length))
    client.send(send_length)
    client.send(message)
    res = json.loads(client.recv(2048).decode(FORMAT))
    return res

def gameInit():
    paddle1rect.centery = SCREEN_CENTER_Y
    paddle2rect.centery = SCREEN_CENTER_Y
    ballrect.center = (ballx, bally)


def setupAndStart():
    # game loop
    global ball_angle
    your_paddle = paddle1rect if PLAYERNUM == 1 else paddle2rect
    opp_paddle = paddle2rect if PLAYERNUM == 1 else paddle1rect
    while True:
        # do gameloop stuff

        # event-loop
        for event in pygame.event.get():
            # look for any event (quitting, button press, etc)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    pressed_keys[0] = True
                elif event.key == pygame.K_DOWN:
                    pressed_keys[1] = True
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    pressed_keys[0] = False
                elif event.key == pygame.K_DOWN:
                    pressed_keys[1] = False

            if event.type == pygame.QUIT:
                pygame.quit()
                client.close()
                losses = [True, True]
                losses[PLAYERNUM - 1] = False
                game_over(*losses)
                exit()

        if pressed_keys[0] and your_paddle.top > 0:
            your_paddle.centery -= 3
        elif pressed_keys[1] and your_paddle.bottom < SCREEN_HEIGHT:
            your_paddle.centery += 3
            
        opponent_info = send_info(json.dumps({'my_y': your_paddle.centery, 'player': PLAYERNUM}))
        opp_paddle.centery = opponent_info['y_val']
        

        ballrect.centerx += int( ball_velocity * cos(radians(ball_angle)) )
        ballrect.centery += int( ball_velocity * sin(radians(ball_angle)) )

        if ballrect.colliderect(paddle1rect):
            ball_angle = 180 - ball_angle # 180 - f(ball_angle) # the return angle frm paddle surface normal
        elif ballrect.colliderect(paddle2rect):
            ball_angle = 180 - ball_angle

        if ballrect.bottom >= SCREEN_HEIGHT or ballrect.top <= 0:
            # flip angle
            ball_angle = -ball_angle
        
        if ballrect.right >= SCREEN_WIDTH or ballrect.left <= 0:
            game_over(ballrect.right >= SCREEN_WIDTH, ballrect.left <= 0)
            ball_angle = 30

        screen.blit(bg_surface, (0, 0))
        screen.blit(paddle_img, paddle1rect)
        screen.blit(paddle_img2, paddle2rect)
        screen.blit(ball_img, ballrect)

        # update the game screen
        pygame.display.update()
        clock.tick(60) # run the game at 60fps

# connect to server
print("Client connecting to server....")
client.connect(ADDR)
print("Sending ready msg")
init_config = send(READY_MSG)
initVars(init_config)
print("Ready msg sent!")
setupAndStart()