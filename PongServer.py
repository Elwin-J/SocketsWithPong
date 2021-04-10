import socket
import json
from random import random
import atexit
import threading

# consts for sockets
PORT = 5050
SERVER_IP = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER_IP, PORT)
MSG_HEADER_SIZE = 64
FORMAT = 'utf-8'
DISCONNECT_MSG = '{ }'

# consts for game
ball_velocity = 6
SCREEN_SIZE = (800, 500)
SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN_SIZE
SCREEN_CENTER_Y = SCREEN_HEIGHT//2
PADDLE_SIZE = (25, 110)
PADDLE_WIDTH, PADDLE_HEIGHT = PADDLE_SIZE
CURR_PLAYERNUM = 2
READY_MSG = 'ready'

readyQueue = []
player_ips = []
receiver = 2

def get_random_degree_angle():
    # get a random angle between [15, 180-15] U [-15, -(180-15)]
    r = random()
    ang = 150 * r + 15
    if abs(ang - 90) <= 10:
        ang = 69
    if random() > 0.5:
        return ang
    return -ang

data_payload = {
    'P1_y': SCREEN_CENTER_Y,
    'P2_y': SCREEN_CENTER_Y,
    'ball_x': 400,
    'ball_y':250,
    'ball_velocity': 6,
    'ball_angle': 30,
    'your_playernum': 1,
    'game_over': False,
}

p1data = {
    'y_val': data_payload['P1_y'],
    'player': 1,
    'ball_x': data_payload['ball_x'],
    'ball_y': data_payload['ball_y'],
    'ball_angle': data_payload['ball_angle'],
    'game_over': False
}

p2data = {
    'y_val': data_payload['P2_y'],
    'player': 2,
    'ball_x': data_payload['ball_x'],
    'ball_y': data_payload['ball_y'],
    'ball_angle': data_payload['ball_angle'],
    'game_over': False
}

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):
    print(f"New connection from {addr} !")
    connected_to_client = True
    readyQueue.append((addr, conn))
    while connected_to_client:
        msg_length_str = conn.recv(MSG_HEADER_SIZE).decode(FORMAT)
        if msg_length_str:
            msg_len = int(msg_length_str)
            msg = conn.recv(msg_len).decode(FORMAT)
            if msg == DISCONNECT_MSG:
                connected_to_client = False
            elif msg == READY_MSG:
                ext = ' wait' if len(readyQueue) != 2 else ' start'
                if ext == ' start':
                    while readyQueue:
                        readyQueue.reverse()
                        a, c = readyQueue.pop()
                        c.send((str(CURR_PLAYERNUM) + ext).encode(FORMAT))
            else:
                json_dict = json.loads(msg)
    
    conn.close()

def handleReadyQueue(readyQueue):
    for i, s in enumerate(readyQueue):
        conn, addr = s
        print("Serving connection from", addr)
        msglen = conn.recv(MSG_HEADER_SIZE).decode(FORMAT)
        if msglen:
            msg = conn.recv(int(msglen)).decode(FORMAT)
            if msg == READY_MSG:
                print("Message from client: ", msg)
                # data_payload preprocessing
                data_payload['your_playernum'] = i+1
                conn.send(json.dumps(data_payload).encode(FORMAT))
    readyQueue.clear()

def handleRequest(conn, addr):
    msglen = conn.recv(MSG_HEADER_SIZE).decode(FORMAT) # size of message to receive
    if msglen:
        msg = conn.recv(int(msglen)).decode(FORMAT) # the JSON containing client's y-value
        print(msg)
        msg = json.loads(msg)
        pnum = msg['player']
        y_val = msg['y_val']
        opp_pnum = 3 - pnum
        print("sending json dump from server to ", player_ips[opp_pnum - 1][0])
        player_ips[opp_pnum - 1][0].send(json.dumps({ 'opp_y_val': y_val, 'player': pnum }).encode(FORMAT))

def clientServerExchange(conn, addr):
    connected = True
    print(f"{addr} connected!")
    while connected:
        msg_len = conn.recv(MSG_HEADER_SIZE).decode(FORMAT)
        if msg_len:
            msg = conn.recv(int(msg_len)).decode(FORMAT)
            if msg == DISCONNECT_MSG :
                connected = False
                conn.send('{}'.encode(FORMAT))
            else:
                msg_json = json.loads(msg)
                # msg_json has 'my_y' and 'player'
                if msg_json['player'] == 1:
                    p1data['y_val'] = msg_json['my_y']
                    conn.send(json.dumps(p2data).encode(FORMAT))
                elif msg_json['player'] == 2:
                    p2data['y_val'] = msg_json['my_y']
                    conn.send(json.dumps(p1data).encode(FORMAT))
                else:
                    print("Huge error!")
                
                
                


def start():
    ''' function to start the server '''
    # listen for any clients and pass relevant params to clientServerExchange() on a new thread
    server.listen()
    print(f"Server Listening on {SERVER_IP}")
    while True:
        conn, addr = server.accept()
        readyQueue.append((conn, addr))
        player_ips.append((conn, addr))
        if len(readyQueue) == 2:
            handleReadyQueue(readyQueue)
            break

    p1info, p2info = player_ips
    p1thread = threading.Thread(target=clientServerExchange, args=p1info[:2])
    p1thread.start()
    p2thread = threading.Thread(target=clientServerExchange, args=p2info[:2])
    p2thread.start()
        
        
def exit_handler():
    for conn, addr in player_ips:
        conn.close()
    print("Closed all connections!")

atexit.register(exit_handler)

print("Starting Pong server....")
start()