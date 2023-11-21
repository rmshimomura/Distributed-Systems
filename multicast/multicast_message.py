import socket, threading, time, sys, os, datetime

RED_COLOR = '\033[31m'
GREEN_COLOR = '\033[32m'
YELLOW_COLOR = '\033[33m'
RESET_COLOR = '\033[0m'

FALSE_POSITIVES = 0

def read_ips_to_send(file_name):

    ips_to_send = []

    with open(file_name, 'r') as file:
        for line in file.readlines():
            ips_to_send.append(line.strip().split())

    this_pc_ips = socket.gethostbyname_ex(socket.gethostname())[2]
    print(this_pc_ips)

    this_pc = [ip for ip in ips_to_send if ip[0] in this_pc_ips]

    if len(this_pc) > 1:
        print(f"This PC ({' / '.join(this_pc_ips)}) has more than one IP in the list of IPs of the file {file_name}: {', '.join([ip[1] for ip in this_pc])}")
        sys.exit(1)
    elif len(this_pc) == 0:
        print(f"This PC ({' / '.join(this_pc_ips)}) is not in the list of IPs of the file {file_name}")
        sys.exit(1)

    indices = [i for i, host in enumerate(ips_to_send) if host[0] == this_pc[0][0]]

    ips_to_send.pop(indices[0])

    this_pc = this_pc[0]

    return ips_to_send, this_pc

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

class Node:

    def __init__(self, this_pc, ips_to_send:list) -> None:

        self.start_variables(this_pc, ips_to_send)
        self.start_params()
        self.start_sockets()
        self.start_threads()

    def exit_program(self):
        self.running = False
        self.close_sockets()
        self.stop_threads()

    def start_variables(self, this_pc, ips_to_send):
        
        self.ips_to_send = ips_to_send

        self.ips_history = dict()

        self.start_time = time.time()

        for i in range(len(self.ips_to_send)):
            self.ips_history[self.ips_to_send[i][0]] = self.ips_to_send[i][1]

        self.ip = this_pc[0]
        self.name = this_pc[1]
        self.last_heartbeat_time = dict()

        for i in range(len(self.ips_to_send)):
            self.last_heartbeat_time[self.ips_to_send[i][0]] = self.start_time

        self.running = True

    def start_params(self):
        self.heartbeat_interval = 2
        self.heartbeat_port = 3000
        self.message_port = 3001
        self.ack_port = 3002
        self.latency = 0.0 # Artificial latency to simulate network latency changed by professor
        self.message_timeout = 1
        self.delta_t = self.heartbeat_interval + self.message_timeout # Defined by the ack from the messages
        self.default_delta_t = self.heartbeat_interval + self.message_timeout
        self.max_resend_attempts = 5

    def start_sockets(self):

        self.socket_heartbeat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_message = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_message_ack = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.socket_heartbeat.bind((self.ip, self.heartbeat_port))
        self.socket_message.bind((self.ip, self.message_port))
        self.socket_message_ack.bind((self.ip, self.ack_port))

        self.socket_message_ack.settimeout(2*self.delta_t)

    def close_sockets(self):

        self.socket_heartbeat.close()
        self.socket_message.close()
        self.socket_message_ack.close()

    def start_threads(self):
        self.thread_listen_heartbeat = threading.Thread(target=self.listen_heartbeat)
        self.thread_listen_heartbeat.start()
        self.thread_send_heartbeat = threading.Thread(target=self.send_heartbeat)
        self.thread_send_heartbeat.start()
        self.thread_listen_message = threading.Thread(target=self.listen_message)
        self.thread_listen_message.start()
        self.thread_check_inactive_hosts = threading.Thread(target=self.check_inactive_hosts)
        self.thread_check_inactive_hosts.start()

    def stop_threads(self):
        self.thread_listen_heartbeat.join()
        self.thread_send_heartbeat.join()
        self.thread_listen_message.join()
        self.thread_check_inactive_hosts.join()

    def listen_heartbeat(self):
        
        global FALSE_POSITIVES

        while self.running:

            try:

                message, addr = self.socket_heartbeat.recvfrom(1024)

                time.sleep(self.latency)

                host_ip = addr[0]

                if host_ip not in [ip[0] for ip in self.ips_to_send]:
                    
                    if host_ip in self.ips_history.keys():

                        print(YELLOW_COLOR + f"\n[{datetime.datetime.now().time().strftime('%H:%M:%S')}] {self.ips_history[host_ip]} ({host_ip}) is trying to connect again" + RESET_COLOR)
                        self.ips_to_send.append((host_ip, self.ips_history[host_ip]))
                        print(GREEN_COLOR + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Connection with {self.ips_history[host_ip]} ({host_ip}) reestablished" + RESET_COLOR)
                        FALSE_POSITIVES += 1

                    else:

                        print(RED_COLOR + f"\n[{datetime.datetime.now().time().strftime('%H:%M:%S')}] {host_ip} is trying to connect, but is not in the list of IPs" + RESET_COLOR)
                        continue

                self.last_heartbeat_time[host_ip] = time.time()

            except:
                    
                continue

    def send_heartbeat(self):

        while self.running:

            copy = self.ips_to_send.copy()

            time.sleep(self.heartbeat_interval + self.latency)

            for i in range(len(copy)):

                self.socket_heartbeat.sendto(b'heartbeat', (copy[i][0], self.heartbeat_port))

    def listen_message(self):
        
        while self.running:

            try:

                message, addr = self.socket_message.recvfrom(1024)
                print(f"\n[{datetime.datetime.now().time().strftime('%H:%M:%S')}][{self.ips_history[addr[0]]}]: {message.decode()}")
                time.sleep(self.latency)
                self.socket_message_ack.sendto(b'ack', (addr[0], self.ack_port))

            except:

                continue

    def send_message(self, message):

        marked_to_remotion = []

        received_ack = []

        copy = self.ips_to_send.copy()

        for i in range(len(copy)):
            
            start_time_message = time.time()

            time.sleep(self.latency)

            self.socket_message.sendto(message.encode(), (copy[i][0], self.message_port))

            print(f"\n[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Sending message to {self.ips_history[copy[i][0]]} ({copy[i][0]})")

            answer, time_ack = self.wait_for_ack(copy[i][0], message, start_time_message)

            if not answer:
                    
                marked_to_remotion.append(copy[i][0])
            
            else:
                print(GREEN_COLOR + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Received ack from {self.ips_history[copy[i][0]]} ({copy[i][0]}) in {round(time_ack, 3)} seconds" + RESET_COLOR)
                received_ack.append((copy[i][0], time_ack))

        print(f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Received acks:")

        for i in range(len(received_ack)):

            print(f"\t-> {self.ips_history[received_ack[i][0]]} ({received_ack[i][0]}) in {received_ack[i][1]} seconds")

        print("\n")

        for i in range(len(marked_to_remotion)):    

            self.remove_host(marked_to_remotion[i])

    def wait_for_ack(self, ip, message, start_time_message):

        retries = 0

        while retries < self.max_resend_attempts:

            try:

                message, addr = self.socket_message_ack.recvfrom(1024)

                if addr[0] == ip and message.decode() == 'ack':

                    end_time_message_ack = time.time()

                    time_to_ack = end_time_message_ack - start_time_message

                    if time_to_ack < self.delta_t * 2:

                        if time_to_ack >= self.delta_t:

                            self.message_timeout = (time_to_ack) - self.heartbeat_interval

                            self.delta_t = self.message_timeout + self.heartbeat_interval

                            print(YELLOW_COLOR + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] New delta t: {self.delta_t} seconds, slightly worse time" + RESET_COLOR)

                            self.socket_message_ack.settimeout(2*self.delta_t)
                        else:

                            self.message_timeout = self.message_timeout / 2

                            self.delta_t = self.message_timeout + self.heartbeat_interval

                            print(GREEN_COLOR + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] New delta t: {self.delta_t} seconds, better time" + RESET_COLOR)
                            self.socket_message_ack.settimeout(2*self.delta_t)
                    else:

                        print("?????????????????????????")
                        print(time_to_ack)

                    return True, time_to_ack
                
                else:
                    continue

            except Exception as e:
                
                time.sleep(self.latency)
                self.socket_message.sendto(message.encode(), (ip, self.message_port))
                print(YELLOW_COLOR + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Didn't received an Ack, resending message to {self.ips_history[ip]}" + RESET_COLOR)
                retries += 1
        
        if retries == self.max_resend_attempts:

            print(RED_COLOR + f"\n[{datetime.datetime.now().time().strftime('%H:%M:%S')}] Max resend attempts reached, removing {self.ips_history[ip]} from list" + RESET_COLOR)
            return False, -1

    def check_inactive_hosts(self):
        
        while self.running:

            to_remove = []  

            current_time = time.time()

            copy = self.last_heartbeat_time.copy()

            for host_ip, last_time in copy.items():

                if current_time - last_time > self.delta_t * 2:

                    print(RED_COLOR + f"[{datetime.datetime.now().time().strftime('%H:%M:%S')}] {self.ips_history[host_ip]} potentially inactive, removing it (failed to send heartbeat: {round(current_time - last_time, 4)})" + RESET_COLOR)
                    to_remove.append(host_ip)

            for i in range(len(to_remove)):

                self.remove_host(to_remove[i])

    def remove_host(self, ip):

        self.delta_t = self.default_delta_t
        self.message_timeout = 1
        self.socket_message_ack.settimeout(2*self.delta_t)

        print(RED_COLOR + f"DELTA T RESETED TO {self.delta_t} SECONDS" + RESET_COLOR)
        print(RED_COLOR + f"MESSAGE TIMEOUT RESETED TO {self.message_timeout} SECONDS" + RESET_COLOR)
        print(RED_COLOR + f"SOCKET TIMEOUT RESETED TO {2*self.delta_t} SECONDS" + RESET_COLOR)

        ip_to_find = ip
        indices = [i for i, host in enumerate(self.ips_to_send) if host[0] == ip_to_find]

        if len(indices) == 0:
            return

        self.ips_to_send.pop(indices[0])
        self.last_heartbeat_time.pop(ip_to_find)

if __name__ == "__main__":

    hosts, this_pc = read_ips_to_send('ips.txt')

    instance = Node(this_pc, hosts)

    while True:

        print("Connected hosts:")

        for i in range(len(instance.ips_to_send)):
            print(GREEN_COLOR + f"\t-> {instance.ips_to_send[i][1]} ({instance.ips_to_send[i][0]})" + RESET_COLOR)

        print("Disconnected hosts:")

        all_ips = [ip[0] for ip in instance.ips_to_send]
        all_history_ips = [ip for ip in instance.ips_history.keys()]

        for i in range(len(all_history_ips)):
            if all_history_ips[i] not in all_ips:
                print(RED_COLOR + f"\t-> {instance.ips_history[all_history_ips[i]]} ({all_history_ips[i]})" + RESET_COLOR)

        print("Configuration:")
        print(f"\t-> Artificial latency: {instance.latency} seconds")
        print(f"\t-> Heartbeat interval: {instance.heartbeat_interval} seconds")
        print(f"\t-> Message timeout: {instance.message_timeout} seconds")
        print(f"\t-> Delta t: {instance.delta_t} seconds")
        print(f"\t-> 2 * Delta t: {2*instance.delta_t} seconds")

        print(f"\nFALSE POSITIVES: {FALSE_POSITIVES}\n")

        print("Options:")
        print("| (1) - Send message | (2) - Alter latency | (3) - Refresh hosts lists | (4) - Clear terminal | (5) - Exit |")

        option = input("Choose an option: ")

        if option == '1':
                
            message = input("Type a message: ")
            instance.send_message(message)

        elif option == '2':
                
            try:

                instance.latency = float(input("Update latency: "))

            except ValueError:

                print(RED_COLOR + f"Invalid value" + RESET_COLOR)

        elif option == '3':
                
            continue

        elif option == '4':
                
            clear_terminal()

        elif option == '5':

            instance.exit_program()
            sys.exit(0)

        else:

            print(RED_COLOR + f"Invalid option: {option}" + RESET_COLOR)