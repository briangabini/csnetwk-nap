from socket import *
import sys
import os
import time
import threading
import json

BUFFER_SIZE = 1024 

# signal the thread to exit
exit_flag = False

# TODO: make a function that processes the commands from the client/s
def processCommandsFromClients(command_prompt, client_socket, client_address):
    data = json.loads(command_prompt.decode())
    command = data['command']

    match command:
        case 'leave':
            client_socket.shutdown(SHUT_WR)
            client_socket.close()
            print('The client disconnected.\n')
            global exit_flag 
            exit_flag = True



def handle_client(client_socket, client_address):
    print(f"Connection established with{client_address}")

    global exit_flag

    # Wait for commands from the client
    while not exit_flag: 
        try: 
            command_prompt = client_socket.recv(BUFFER_SIZE)

            # break the loop if no data is received
            if not command_prompt:
                break

            processCommandsFromClients(command_prompt, client_socket, client_address) # Process the command
        
        except Exception as e:
            print(f'Error handling client.{e}')
            break

        
# initialize the server socket 
server_socket = socket(AF_INET, SOCK_STREAM) 

# Loops until a successful server is started
while True:
    print("FIle Transfer TCP Server")
    try:
        ip = input("Enter IP: ")                    # user inputs IP Address for the server to bind
        port = input("Enter Port: ")                # user inputs the Port Number for the server to bind
        server_socket.bind((ip, int(port)))         # Bind the socket to a specific IP address and port
        server_socket.listen(1)                     # sets the maximum ammount of connections allowed 
        print(f"Server running at {ip}:{port}")
        break

    except Exception as e:
        os.system('cls')
        print(f"Error: {str(e)}\nTry again\n")

connected_clients = []                 
disconnected_clients = []

try:      
    # Accept incoming connections  
    while True:
        print("Waiting for a connection...")
        client_socket, client_address = server_socket.accept()      # accept the connection from incoming clients

        # call some functions here
        # Create a new thread for each client
        # this allows multiple tasks to run concurrently, in this case, handling multiple clients
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

        # Add user to list of connected clients
        new_user = {'address' : client_address, 'socket': client_socket, 'name': ""}
        connected_clients.append(new_user)

        
finally:
    #closes the server socket when done
    server_socket.close()