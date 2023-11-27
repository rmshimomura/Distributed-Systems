import pygame, sys, threading, time, datetime, socket

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

RED_COLOR_TEXT = '\033[31m'
GREEN_COLOR_TEXT = '\033[32m'
YELLOW_COLOR_TEXT = '\033[33m'
RESET_COLOR_TEXT = '\033[0m'

HEARTBEAT_PORT = 0
WHITEBOARD_DISCOVER_PORT = 1
WHITEBOARD_TRANSFER_PORT = 2
ELECTION_PORT = 3

class Whiteboard:

    def __init__(self, width, height, instance_name, whiteboard_name, host_place, running_on_port, whiteboard_instance_port):

        self.keep_server_running = True
        self.start_window(width, height, instance_name, whiteboard_name)
        self.render_interface = False
        self.lines = []
        self.host_place = host_place
        self.connections = []
        self.lines_being_modified = []
        self.line_i_want_is_safe_to_move = True
        self.other_clients = []
        self.running_on_port = running_on_port
        self.whiteboard_instance_port = whiteboard_instance_port
        self.new_host_announced = False
        self.keep_election_alive = None
        
    def reset_info(self, width, height, instance_name, whiteboard_name, host_place, running_on_port, whiteboard_instance_port):

        self.keep_server_running = True
        self.start_window(width, height, instance_name, whiteboard_name)
        self.render_interface = False
        self.host_place = host_place
        self.connections = []
        self.lines_being_modified = []
        self.line_i_want_is_safe_to_move = True
        self.other_clients = []
        self.running_on_port = running_on_port
        self.whiteboard_instance_port = whiteboard_instance_port
        self.new_host_announced = False
        self.keep_election_alive = None

    def start_window(self, width, height, instance_name, whiteboard_name):
            
        self.width = width
        self.height = height
        self.whiteboard_name = whiteboard_name
        self.instance_name = instance_name
        self.update_threads = []

        self.dragging_line_start = False
        self.dragging_line_end = False
        self.line_creation = False
        self.start_point_motion = None
        self.end_point_motion = None
    
        self.window = None

    def initialize_pygame(self, whiteboard_name):
        self.pygame_instance = pygame
        self.pygame_instance.init()
        self.window = self.pygame_instance.display.set_mode((self.width, self.height))
        self.pygame_instance.display.set_caption(f"Instance {self.instance_name} - Whiteboard {whiteboard_name}")
        self.render_interface = True

    def start_remote_thread(self, conn):
        # Function only used when a client connects to a server
        self.host_place = 'remote'
        print("Remote thread started")
        self.remote_thread = threading.Thread(target=self.await_changes, args=(conn,))
        self.remote_thread.start()
        self.update_threads.append([self.remote_thread, conn])
        self.connections.append(conn)
        self.keep_election_alive = True

    def start_local_thread(self, conn):
        # Function only used when a server accepts a client
        self.host_place = 'local'
        print("Local thread started")
        self.local_thread = threading.Thread(target=self.await_changes, args=(conn,))
        self.local_thread.start()
        self.update_threads.append([self.local_thread, conn])
        self.connections.append(conn)

    def announce_new_client(self, port):

        if self.host_place == 'local':

            for conn in self.connections:
                conn.send(f"P:{port}".encode())

        elif self.host_place == 'remote':
            print(RED_COLOR_TEXT + "Remote received request to announce a new client???" + RESET_COLOR_TEXT)

    def announce_client_disconnection(self, port):
            
        # print("Announcing client disconnection")

        if self.host_place == 'local':

            for conn in self.connections:
                conn.send(f"D:{port}".encode())

        elif self.host_place == 'remote':
            print(RED_COLOR_TEXT + "Remote received request to announce a client disconnection???" + RESET_COLOR_TEXT)

    def start_election_await(self):

        self.election_await_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.election_await_socket.bind(('127.0.0.1', self.whiteboard_instance_port + ELECTION_PORT))
        self.election_await_socket.settimeout(1)

        timestamps = []

        while self.keep_election_alive:

            try:

                data, addr = self.election_await_socket.recvfrom(1024)

                # Format: ELECTION;port;timestamp

                data = data.decode()

                if 'ELECTION' in data:

                    port = int(data.split(';')[1])
                    timestamp = int(data.split(';')[2])

                    if port not in [record[0] for record in timestamps]:
                        timestamps.append([port, timestamp])

                    timestamps.sort(key=lambda x: x[1])

                elif 'RESULT' in data:

                    port = int(data.split(';')[1])

                    print(GREEN_COLOR_TEXT + f"==============================================" + RESET_COLOR_TEXT)
                    print(GREEN_COLOR_TEXT + f"|| NEW HOST: {port}, please reset connection ||" + RESET_COLOR_TEXT)
                    print(GREEN_COLOR_TEXT + f"==============================================" + RESET_COLOR_TEXT)

                    self.keep_server_running = False
                    self.render_interface = False

                    break

            except Exception as e:
                continue

            if len(timestamps) == len(self.other_clients):

                timestamps.sort(key=lambda x: x[1])

                if timestamps[0][0] == self.whiteboard_instance_port:

                    print(YELLOW_COLOR_TEXT + "I am the new host" + RESET_COLOR_TEXT)

                    for port in self.other_clients:

                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            sock.sendto(f"RESULT;{self.whiteboard_instance_port}".encode(), ('127.0.0.1', port + ELECTION_PORT))

                        except ConnectionResetError:
                            continue

                    self.host_place = 'local'
                    self.keep_server_running = True
                    self.render_interface = False
                    self.new_host_announced = True
                    
                    break

        # print("Election await thread finished")

    def render(self, host_place):

        self.initialize_pygame(self.whiteboard_name)

        self.host_place = host_place

        self.start_election_thread = threading.Thread(target=self.start_election_await)
        self.start_election_thread.start()

        if self.host_place == 'local':
            self.announce_new_client(self.running_on_port)

        while self.render_interface:

            self.window.fill(WHITE)

            self.render_lines()

            self.pygame_instance.display.flip()

            self.pygame_instance.time.Clock().tick(60)

            self.handle_events()

        self.pygame_instance.quit()

        # Window closed

        if self.new_host_announced:

            self.keep_server_running = False
            return 'im_new_host'

        if self.host_place == 'local':
            self.announce_client_disconnection(self.running_on_port)
            return True
        
        elif self.host_place == 'remote':

            try:

                self.connections[0].send(f"EXIT;{self.whiteboard_instance_port}".encode())
                
            except ConnectionResetError:
                pass

            self.keep_server_running = False
            self.keep_election_alive = False
            self.connections[0].close()
            return False

    def render_lines(self):

        if len(self.lines):

            temp = self.lines.copy()

            for line, (start, end) in enumerate(temp):
                self.pygame_instance.draw.line(self.window, BLACK, start, end, 2)
                self.pygame_instance.draw.circle(self.window, RED, start, 5)
                self.pygame_instance.draw.circle(self.window, RED, end, 5)

            if self.start_point_motion and self.end_point_motion:
                self.pygame_instance.draw.line(self.window, BLACK, self.start_point_motion, self.end_point_motion, 2)
                self.pygame_instance.draw.circle(self.window, RED, self.start_point_motion, 5)
                self.pygame_instance.draw.circle(self.window, RED, self.end_point_motion, 5)

        elif self.start_point_motion and self.end_point_motion:
            self.pygame_instance.draw.line(self.window, BLACK, self.start_point_motion, self.end_point_motion, 2)
            self.pygame_instance.draw.circle(self.window, RED, self.start_point_motion, 5)
            self.pygame_instance.draw.circle(self.window, RED, self.end_point_motion, 5)

    def await_changes(self, conn):

        while self.keep_server_running:

            try:

                response = conn.recv(1024)

                response = response.decode()

                if not response:
                    break

                if 'EXIT' in response:

                    # Response only received when a client disconnects from the server

                    # print(YELLOW_COLOR_TEXT + "Client disconnected" + RESET_COLOR_TEXT)

                    port = response.split(';')[1]

                    for i in range(len(self.connections)):
                        if self.connections[i] == conn:

                            for index, (thread, connection) in enumerate(self.update_threads):

                                if connection == conn:
                                    self.connections.remove(connection)
                                    self.update_threads.pop(index)
                                    self.announce_client_disconnection(port)
                                    return
                            
                            break


                elif 'OK' in response:

                    print(GREEN_COLOR_TEXT + "Line is safe to move" + RESET_COLOR_TEXT)

                    if self.host_place == 'remote':
                        self.line_i_want_is_safe_to_move = True
                        self.waiting_request_answer = False
                    elif self.host_place == 'local':
                        print(RED_COLOR_TEXT + "Local received OK from server???" + RESET_COLOR_TEXT)

                elif 'NO' in response:

                    print(RED_COLOR_TEXT + "Line is locked, please wait" + RESET_COLOR_TEXT)

                    self.line_i_want_is_safe_to_move = False
                    self.waiting_request_answer = False

                elif 'P' in response:

                    # print(YELLOW_COLOR_TEXT + "New client connected" + RESET_COLOR_TEXT)

                    port = int(response[2:])

                    if port not in self.other_clients:
                        self.other_clients.append(port)
                        self.other_clients.sort()
                        # print(f"Connected clients: {self.other_clients}")

                elif 'D' in response:

                    # print(YELLOW_COLOR_TEXT + "Client disconnected" + RESET_COLOR_TEXT)

                    port = int(response[2:])

                    if port in self.other_clients:
                        self.other_clients.remove(port)
                        self.other_clients.sort()
                        # print(f"Connected clients: {self.other_clients}")

                elif 'C' in response:
                    # Create the line

                    print(GREEN_COLOR_TEXT + "Creating line" + RESET_COLOR_TEXT)

                    points = response[2:].split(',')
                    p1 = [int(points[0]), int(points[1])]
                    p2 = [int(points[2]), int(points[3])]
                    self.lines.append([p1, p2])

                    if self.host_place == 'local':
                    
                        for client in self.connections:

                            if client == conn:
                                continue

                            client.send(response.encode())

                    elif self.host_place == 'remote':
                        
                        pass

                elif 'M' in response:
                    # Move the line

                    print(GREEN_COLOR_TEXT + "Moving line" + RESET_COLOR_TEXT)

                    points = response[2:].split('>')
                    old_points = points[0].split(',')
                    new_points = points[1].split(',')
                    old_p1 = [int(old_points[0]), int(old_points[1])]
                    old_p2 = [int(old_points[2]), int(old_points[3])]
                    new_p1 = [int(new_points[0]), int(new_points[1])]
                    new_p2 = [int(new_points[2]), int(new_points[3])]

                    for i, (p1, p2) in enumerate(self.lines):
                        if p1 == old_p1 and p2 == old_p2:
                            self.lines[i] = [new_p1, new_p2]
                            for line in self.lines_being_modified:
                                if line[0] == old_p1 and line[1] == old_p2:
                                    self.lines_being_modified.remove(line)
                                    break
                            break

                    if self.host_place == 'local':
                        for client in self.connections:
                            if client == conn:
                                continue
                            client.send(response.encode())

                    elif self.host_place == 'remote':
                        pass

                elif 'R' in response:

                    if self.host_place == 'local':

                        line = response[2:].split(',')
                        start_point = [int(line[0]), int(line[1])]
                        end_point = [int(line[2]), int(line[3])]

                        found = False

                        for p1, p2 in self.lines_being_modified:
                            if p1 == start_point and p2 == end_point:
                                found = True
                                conn.send("NO".encode())
                                print(RED_COLOR_TEXT + "Request denied." + RESET_COLOR_TEXT)
                                break

                        if not found:
                            self.lines_being_modified.append([start_point, end_point])
                            conn.send("OK".encode())
                            print(GREEN_COLOR_TEXT + "Request accepted." + RESET_COLOR_TEXT)

                    elif self.host_place == 'remote':
                        print(RED_COLOR_TEXT + "Remote received request to request a line???" + RESET_COLOR_TEXT)
                        pass
            except ConnectionAbortedError:
                break
            except ConnectionResetError:
                print(RED_COLOR_TEXT + "Connection with server has been lost!" + RESET_COLOR_TEXT)

                for port in self.other_clients:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.sendto(f"ELECTION;{self.whiteboard_instance_port};{time.time_ns()}".encode(), ('127.0.0.1', port + ELECTION_PORT))
                    except ConnectionResetError:
                        continue

                self.render_interface = False
                self.keep_server_running = False
                break
            
            except Exception as e:
                continue

    def line_creation_notice(self, line_start, line_end):

        if self.host_place == 'local':
            # If this instance is the host, send the line to each client
            # Send the line to each client
            for conn in self.connections:
                conn.send(f"C:{line_start[0]},{line_start[1]},{line_end[0]},{line_end[1]}".encode())

        elif self.host_place == 'remote':
            # If this instance is a client, send the line to the server
            # Then, on server side, the server will send the line to each client

            try:
                self.connections[0].send(f"C:{line_start[0]},{line_start[1]},{line_end[0]},{line_end[1]}".encode())
            except ConnectionResetError:
                self.keep_server_running = False
                print(RED_COLOR_TEXT + "Connection with server lost" + RESET_COLOR_TEXT)

    def line_movement_notice(self, old_start_point, old_end_point, new_start_point, new_end_point):

        if self.host_place == 'local':
            # If this instance is the host, send the line to each client
            # Send the line to each client
            for conn in self.connections:
                conn.send(f"M:{old_start_point[0]},{old_start_point[1]},{old_end_point[0]},{old_end_point[1]}>{new_start_point[0]},{new_start_point[1]},{new_end_point[0]},{new_end_point[1]}".encode())

        elif self.host_place == 'remote':

            # If this instance is a client, send the line to the server
            # Then, on server side, the server will send the line to each client
            try:
                self.connections[0].send(f"M:{old_start_point[0]},{old_start_point[1]},{old_end_point[0]},{old_end_point[1]}>{new_start_point[0]},{new_start_point[1]},{new_end_point[0]},{new_end_point[1]}".encode())
            except ConnectionResetError:
                self.keep_server_running = False
                print(RED_COLOR_TEXT + "Connection with server lost" + RESET_COLOR_TEXT)

    def line_request_notice(self, line_start, line_end):

        if self.host_place == 'local':
            
            found = False

            for p1, p2 in self.lines_being_modified:
                if p1 == line_start and p2 == line_end:
                    found = True
                    self.line_i_want_is_safe_to_move = False
                    self.waiting_request_answer = False
                    break

            if not found:
                self.lines_being_modified.append([line_start, line_end])
                self.line_i_want_is_safe_to_move = True
                self.waiting_request_answer = False

        elif self.host_place == 'remote':

            # Send a message to server to check if the line is locked
            try:
                self.connections[0].send(f"R:{line_start[0]},{line_start[1]},{line_end[0]},{line_end[1]}".encode())
            except ConnectionResetError:
                self.keep_server_running = False
                print(RED_COLOR_TEXT + "Connection with server lost" + RESET_COLOR_TEXT)

    def handle_events(self):

        for event in self.pygame_instance.event.get():

            if event.type == self.pygame_instance.QUIT:
                self.pygame_instance.quit()
                self.render_interface = False
                return

            elif event.type == self.pygame_instance.MOUSEBUTTONDOWN:

                if event.button == self.pygame_instance.BUTTON_LEFT:
                    # Create a line if the left button is pressed
                    
                    if self.line_creation:

                        self.lines.append([list(self.line_start_point), list(event.pos)])

                        self.line_creation_notice(self.line_start_point, event.pos)

                        self.line_creation = False
                    else:
                        self.line_start_point = event.pos
                        self.line_creation = True

                elif event.button == self.pygame_instance.BUTTON_RIGHT:
                    # Move a line if the right button is pressed

                    for i, (p1, p2) in enumerate(self.lines):

                        self.line_start = self.pygame_instance.Rect(p1[0] - 5, p1[1] - 5, 10, 10)
                        self.line_end = self.pygame_instance.Rect(p2[0] - 5, p2[1] - 5, 10, 10)

                        # Check hitboxes

                        if self.line_start.collidepoint(event.pos):

                            self.waiting_request_answer = True

                            self.line_request_notice(p1, p2)

                            while self.waiting_request_answer:
                                continue

                            if not self.line_i_want_is_safe_to_move:
                                print(RED_COLOR_TEXT + "Line is locked, please wait" + RESET_COLOR_TEXT)
                                break
                            
                            self.start_point_motion, self.end_point_motion = list(p1), list(p2)
                            self.dragging_line_start = True
                            self.line_being_moved = self.lines.pop(i)
                            break

                        elif self.line_end.collidepoint(event.pos):

                            self.waiting_request_answer = True

                            self.line_request_notice(p1, p2)

                            while self.waiting_request_answer:
                                continue

                            if not self.line_i_want_is_safe_to_move:
                                print(RED_COLOR_TEXT + "Line is locked, please wait" + RESET_COLOR_TEXT)
                                break

                            self.start_point_motion, self.end_point_motion = list(p1), list(p2)
                            self.dragging_line_end = True
                            self.line_being_moved = self.lines.pop(i)
                            break


            elif event.type == self.pygame_instance.MOUSEMOTION:

                # Update the coordinates when dragging
                if self.dragging_line_start:
                    self.start_point_motion = list(event.pos)
                elif self.dragging_line_end:
                    self.end_point_motion = list(event.pos)

            elif event.type == self.pygame_instance.MOUSEBUTTONUP:

                # Stop dragging when the mouse button is released

                if event.button == self.pygame_instance.BUTTON_RIGHT:

                    if self.line_i_want_is_safe_to_move:

                        if self.dragging_line_start or self.dragging_line_end:

                            self.line_movement_notice(self.line_being_moved[0], self.line_being_moved[1], self.start_point_motion, self.end_point_motion)

                            self.lines.insert(0, [list(self.start_point_motion), list(self.end_point_motion)])

                            self.dragging_line_start = False
                            self.dragging_line_end = False
                            self.start_point_motion = None
                            self.end_point_motion = None
                            self.line_being_moved = None
