import socket, threading, time, sys, os, datetime, whiteboard

RED_COLOR_TEXT = '\033[31m'
GREEN_COLOR_TEXT = '\033[32m'
YELLOW_COLOR_TEXT = '\033[33m'
RESET_COLOR_TEXT = '\033[0m'
NUMBER_OF_NODES = 0
WIDTH = 800
HEIGHT = 600

def recognize_instances(node_name, file_name):

    instances_to_send = dict()

    with open(file_name, 'r') as file:
        for line in file.readlines():
            instances_to_send[line.strip().split()[0]] = int(line.strip().split()[1])

    try:

        return instances_to_send, node_name, instances_to_send[node_name]

    except:
            
        print(RED_COLOR_TEXT + f"Invalid node name: {node_name}" + RESET_COLOR_TEXT)
        sys.exit(1)

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_available_whiteboards(instance):

    print("Hosts and whiteboards hosted (if available):")

    if len(instance.available_whiteboards) == 0:
        print("\t-> None")
        return

    connections = sorted(instance.available_whiteboards.items(), key=lambda x: x[0])

    for key, value in connections:
            
        print(f"HOST: {GREEN_COLOR_TEXT} {key} {RESET_COLOR_TEXT}")

        if len(instance.available_whiteboards[key]) > 0:

            whiteboards = sorted(instance.available_whiteboards[key])

            for whiteboard_name in whiteboards:
                print(f"\t-> {YELLOW_COLOR_TEXT} {whiteboard_name} {RESET_COLOR_TEXT}")

def available_whiteboards(instance):

    for name, port in instance.available_ports.items():

        if name == instance.name:
            continue

        instance.available_whiteboards[name] = instance.ask_for_whiteboards(port)
    
    instance.available_whiteboards[instance.name] = instance.whiteboards_hosted.keys()

    return True

class Node:

    def __init__(self, this_instance_name, this_instance_port, ports:dict) -> None:

        self.start_variables(this_instance_name, this_instance_port, ports)
        self.start_params()
        self.start_sockets()
        self.start_threads()

    def exit_program(self):

        print("Exiting...")

        for whiteboard in self.whiteboards_hosted.values():

            whiteboard.keep_server_running = False

            for conn in whiteboard.connections:

                conn.close()
                time.sleep(0.01)

        print("Whiteboards closed")

        self.running = False
        self.close_sockets()

        print("Sockets closed")

        self.stop_threads()

        print("Threads stopped")

    def start_variables(self, this_instance_name, this_instance_port, available_ports):
        
        self.available_ports = available_ports

        self.name = this_instance_name
        self.port = int(this_instance_port)

        self.connected_to_whiteboard = None
        self.connected_to_connection = None

        self.running = True

        self.whiteboards_hosted = dict()
        self.available_whiteboards = dict()

    def start_params(self):
        self.heartbeat_interval = 3
        self.heartbeat_port = 0
        self.whiteboard_discover_port = 1
        self.whiteboard_transfer_port = 2
        self.election_port = 3
        self.heartbeat_timeout = 2 * self.heartbeat_interval

    def start_sockets(self):

        self.socket_heartbeat = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_whiteboard_discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_whiteboard_transfer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket_heartbeat.bind(('127.0.0.1', self.port + self.heartbeat_port))
        self.socket_whiteboard_discover.bind(('127.0.0.1', self.port + self.whiteboard_discover_port))
        self.socket_whiteboard_transfer.bind(('127.0.0.1', self.port + self.whiteboard_transfer_port))

        self.socket_heartbeat.listen(NUMBER_OF_NODES)
        self.socket_whiteboard_discover.listen(NUMBER_OF_NODES)
        self.socket_whiteboard_transfer.listen(NUMBER_OF_NODES)

        print(GREEN_COLOR_TEXT + f"HEARTBEAT SOCKET: {self.port + self.heartbeat_port}" + RESET_COLOR_TEXT)
        print(GREEN_COLOR_TEXT + f"WHITEBOARD DISCOVER SOCKET: {self.port + self.whiteboard_discover_port}" + RESET_COLOR_TEXT)
        print(GREEN_COLOR_TEXT + f"WHITEBOARD TRANSFER SOCKET: {self.port + self.whiteboard_transfer_port}" + RESET_COLOR_TEXT)

        self.socket_heartbeat.settimeout(self.heartbeat_timeout)

    def start_threads(self):

        self.thread_discover = threading.Thread(target=self.listen_for_discover)
        self.thread_transfer = threading.Thread(target=self.transfer_whiteboard)

        self.thread_discover.start()
        self.thread_transfer.start()

    def stop_threads(self):

        self.thread_discover.join()
        self.thread_transfer.join()

        for whiteboard in self.whiteboards_hosted.values():
            whiteboard.exit_flag = True

    def close_sockets(self):

        self.socket_heartbeat.close()
        self.socket_whiteboard_discover.close()
        self.socket_whiteboard_transfer.close()

    def get_instance_name(self, port_to_look):
        
        for name, port in self.available_ports.items():

            if port == port_to_look:

                return name

    def get_instance_port(self, name_to_look):
            
            for name, port in self.available_ports.items():
    
                if name == name_to_look:
    
                    return port
                
            return None

    def create_whiteboard(self):

        name = input("Whiteboard name: ")

        if name not in self.whiteboards_hosted.keys():

            self.whiteboards_hosted[name] = whiteboard.Whiteboard(WIDTH, HEIGHT, name, name, 'local', self.port, self.port)

        else:

            print(YELLOW_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] You already have your own whiteboard!" + RESET_COLOR_TEXT)

    def ask_for_whiteboards(self, port):

        print(f"Asking {self.get_instance_name(port)} for whiteboards on port {port + self.whiteboard_discover_port}")

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            conn.connect(('127.0.0.1', port + self.whiteboard_discover_port))
        except ConnectionRefusedError:
            print(RED_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Couldn't connect to {self.get_instance_name(port)} (connection refused)" + RESET_COLOR_TEXT)
            return []

        conn.send(b'whiteboards')

        try:

            answer = conn.recv(1024)

            if answer.decode() == 'no_whiteboards':

                print(YELLOW_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] {self.get_instance_name(port)} doesn't have any whiteboards" + RESET_COLOR_TEXT)
                return []

            elif answer.decode() == 'whiteboards':

                print(GREEN_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] {self.get_instance_name(port)} has some whiteboards" + RESET_COLOR_TEXT)

                new_answer = conn.recv(1024)

                return new_answer.decode().split(';')
                
            else:
                print("Unknown answer:")
                print(answer.decode())

            conn.close()
                
        except Exception as e:

            conn.close()
            print(RED_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Couldn't receive whiteboards from {self.get_instance_name(port)}" + RESET_COLOR_TEXT)
            return []

    def listen_for_discover(self):

        while self.running:

            try:

                conn, (addr, port) = self.socket_whiteboard_discover.accept()

                if conn.recv(1024).decode() == 'whiteboards':

                    if len(self.whiteboards_hosted) == 0:

                        conn.send(b'no_whiteboards')

                    else:

                        conn.send(b'whiteboards')
                        conn.send(';'.join(self.whiteboards_hosted.keys()).encode())

                conn.close()

            except:

                continue

    def request_whiteboard(self, whiteboard_name):

        for name, whiteboards in self.available_whiteboards.items():
                
            if whiteboard_name in whiteboards:

                if whiteboard_name in self.whiteboards_hosted.keys():

                    self.connected_to_whiteboard = self.whiteboards_hosted[whiteboard_name]
                    self.connected_to_connection = None
                    return 'connected'

                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.connect(('127.0.0.1', self.get_instance_port(name) + self.whiteboard_transfer_port))
                conn.send(f'whiteboard;{whiteboard_name};{self.port}'.encode())

                try:

                    answer = conn.recv(1024)

                    requested_whiteboard = whiteboard.Whiteboard(WIDTH, HEIGHT, self.name, whiteboard_name, 'remote', self.get_instance_port(name), self.port)

                    if answer.decode() != 'empty':

                        lines = [points.split('|') for points in answer.decode().split(';')]

                        for index, (start_point, end_point) in enumerate(lines):

                            start_point = list([int(x) for x in start_point.split(',')])
                            end_point = list([int(x) for x in end_point.split(',')])
                            requested_whiteboard.lines.append([start_point, end_point])

                    self.connected_to_whiteboard = requested_whiteboard
                    self.connected_to_connection = conn

                    try:
                        other_clients = conn.recv(1024).decode().split(';')

                        if other_clients[0] == 'empty':
                            other_clients = []
                        else:
                            self.connected_to_whiteboard.other_clients = [int(x) for x in other_clients]

                    except Exception as e:
                        print(e)
                        other_clients = []
                        self.connected_to_whiteboard.other_clients = []

                    requested_whiteboard.start_remote_thread(conn)

                    return 'connected'
                    
                except Exception as e:

                    print(e)
                        
                    print(RED_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Couldn't receive whiteboard from {name}" + RESET_COLOR_TEXT)
                    return 'not_connected'
                
        return 'not_found'

    def transfer_whiteboard(self):

        while self.running:

            try:

                conn, (addr, temp_port) = self.socket_whiteboard_transfer.accept()

                parts = conn.recv(1024).decode().split(';')

                whiteboard_name, port_origin = parts[1], int(parts[2])

                print("Received request for whiteboard " + YELLOW_COLOR_TEXT + f"{whiteboard_name}" + RESET_COLOR_TEXT)

                if whiteboard_name in self.whiteboards_hosted.keys():

                    if len(self.whiteboards_hosted[whiteboard_name].lines) == 0:
                            
                        conn.send('empty'.encode())

                    else:

                        whiteboard_lines = self.whiteboards_hosted[whiteboard_name].lines

                        lines_string = ';'.join(['|'.join([f"{x},{y}" for x, y in inner_tuple]) for inner_tuple in whiteboard_lines])

                        conn.send(lines_string.encode())

                    if len(self.whiteboards_hosted[whiteboard_name].other_clients) > 0:
                        # print("Sending other clients")
                        conn.send(';'.join([str(x) for x in self.whiteboards_hosted[whiteboard_name].other_clients]).encode())
                    else:
                        conn.send('empty'.encode())

                    self.whiteboards_hosted[whiteboard_name].start_local_thread(conn)

                    self.whiteboards_hosted[whiteboard_name].other_clients.append(int(port_origin))

                    self.whiteboards_hosted[whiteboard_name].announce_new_client(port_origin)

                else:
                    conn.send('not_found'.encode())
                
            except:
                continue

if __name__ == "__main__":

    try:

        instances, this_instance_name, this_instance_port = recognize_instances(sys.argv[1], 'ports.txt')
    
    except:
            
        print(RED_COLOR_TEXT + "Invalid arguments, usage example: python3 connection.py node1" + RESET_COLOR_TEXT)
        sys.exit(1)

    NUMBER_OF_NODES = len(instances)

    instance = Node(this_instance_name, this_instance_port, instances)

    while True:

        print("Instance name: " + YELLOW_COLOR_TEXT + f"{instance.name}" + RESET_COLOR_TEXT + " running on port " + YELLOW_COLOR_TEXT + f"{instance.port}" + RESET_COLOR_TEXT)
        print("Current mode: " + YELLOW_COLOR_TEXT + f"{'Server' if len(instance.whiteboards_hosted) > 0 else 'Client'}" + RESET_COLOR_TEXT)

        print_available_whiteboards(instance)

        print("Whiteboards hosted:")

        if len(instance.whiteboards_hosted) == 0:
            print("\t-> None")
        else:
            for whiteboard_name in instance.whiteboards_hosted.keys():
                print(f"\t-> {whiteboard_name} - {len(instance.whiteboards_hosted[whiteboard_name].connections)} connections")
                

        print("Options:")
        print("| (1) - Create whiteboard | (2) - Ask for available whiteboards | (3) - Connect to whiteboard | (4) - Clear terminal | (5) - Exit |")

        option = input("Choose an option: ")

        if option == '1':
            
            if instance.connected_to_whiteboard != None:
                print(RED_COLOR_TEXT + "This instance mode is client, you can't create a whiteboard" + RESET_COLOR_TEXT)
                continue
            if len(instance.whiteboards_hosted) > 0:
                print(RED_COLOR_TEXT + "You can't create more than one whiteboard" + RESET_COLOR_TEXT)
                continue

            instance.create_whiteboard()

            print()

        elif option == '2':
                
            available_whiteboards(instance)

            print(GREEN_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Available whiteboards updated" + RESET_COLOR_TEXT)

        elif option == '3':

            print(YELLOW_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Discovering available whiteboards... please wait." + RESET_COLOR_TEXT)
            available_whiteboards(instance)

            print_available_whiteboards(instance)

            name = input("Whiteboard name: ")

            if len(instance.whiteboards_hosted) > 0:
                if name not in instance.whiteboards_hosted.keys():
                    print(RED_COLOR_TEXT + "This instance is a Server, you can't connect to a whiteboard hosted by another instance" + RESET_COLOR_TEXT)
                    continue

            response = instance.request_whiteboard(name)

            if response == 'connected':
                print(GREEN_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Connected to {name}" + RESET_COLOR_TEXT)

                if instance.connected_to_connection == None:
                    election_result = instance.connected_to_whiteboard.render('local')
                else:
                    election_result = instance.connected_to_whiteboard.render('remote')
                    if election_result == 'im_new_host':
                        instance.whiteboards_hosted[name] = instance.connected_to_whiteboard
                        for conn in instance.whiteboards_hosted[name].connections:
                            conn.close()
                        instance.whiteboards_hosted[name].reset_info(WIDTH, HEIGHT, instance.name, name, 'local', instance.port, instance.port)
                        instance.connected_to_connection = None
                        instance.connected_to_whiteboard = None
                        
                        print(GREEN_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] You are now hosting {name}" + RESET_COLOR_TEXT)

            elif response == 'not_connected':
                print(RED_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Couldn't connect to {name}" + RESET_COLOR_TEXT)
            elif response == 'not_found':
                print(RED_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] {name} not found" + RESET_COLOR_TEXT)

        elif option == '4':
                
            clear_terminal()

        elif option == '5':

            instance.exit_program()
            print(GREEN_COLOR_TEXT + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Program successfully exited" + RESET_COLOR_TEXT)
            sys.exit(0)

        else:

            print(RED_COLOR_TEXT + f"Invalid option: {option}" + RESET_COLOR_TEXT)