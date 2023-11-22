from socket import *
import sys
import os
import time
import threading
import json
import base64

BUFFER_SIZE = 1024 

# signal the thread to exit
exit_flag = False

connected_clients = []                 
disconnected_clients = []

# TODO: make a function that processes the commands from the client/s
def processCommandsFromClients(command_prompt, client_socket, client_address):

    # execute this block when the command_prompt value is a json object
    try:
        data = json.loads(command_prompt.decode())      # deserialize string to python <dict>
        command = data['command']                       # assign the command 

    # execute this block when the command_prompt value is a <dict>
    except:
        command = command_prompt['command']


    match command:
        case 'leave':
            client_socket.close()
            print(f'The client {client_address[1]} disconnected.\n')
            global exit_flag 
            exit_flag = True

        case 'register':
            handle = data['handle']

            filtered_clients = list(filter(lambda client: client['name'] == handle, connected_clients))

            if filtered_clients:             # check if null 
                print(f'User {handle} already exists.')
            else:
                filtered_clients = list(filter(lambda client: client['address'] == client_address, connected_clients))

                if filtered_clients:
                    client = filtered_clients[0]
                    client['name'] = handle

                    print(f'Successfully registered User {handle}')

                else:
                    print(f'User doesn\'t exist.')

        case 'dir':

            # Get all files from current directory
            dir = os.listdir("./") # Might need to change this
            os.chdir(os.getcwd()) # Back to original dir

            # Remove FileServer.py from list
            dir.remove('FileServer.py')

            print('Directory: ', end='')
            
            client_socket.send(str(dir).encode('utf-8'))

            # send the dir to client using client_socket.send()
        case 'store':
            filename = command_prompt['filename']
                                      # Store file to server folder

            # Check if file with same file name already exists in server directory
            server_dir = os.listdir("./")
            filename = get_unique_filename(filename, server_dir)

            file_path = './' + filename    

            print('Filename: ', filename)

            file_content = command_prompt['file_content']            # get the content of a file in <bytes>

            # Get the file content
            print(file_content)

            # print('Type of file_content: ', type(file_content))

            with open(file_path, 'wb') as file:                      # write the file_content to the newly created file
                file.write(file_content)

            print(f'{client_address} successfully stored {filename} to the server.')

        case 'get':
            filename = command_prompt['filename']

            file_path = './' + filename

            if os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    file_content = file.read()

                    client_socket.send(str(len(file_content)).encode())     # send the file length

                    print(len(file_content))

                    time.sleep(0.1)

                    print('Type of file_content: ', type(file_content))

                    # print('file_content: ', file_content)

                    client_socket.sendall(file_content) 
            
            else:
                print('Error: File does not exist.')

def get_unique_filename(file_name, server_dir):
    base, ext = os.path.splitext(file_name)
    counter = 1
    new_file_name = file_name

    while new_file_name in server_dir:
        new_file_name = f"{base}({counter}){ext}"
        counter += 1

    return new_file_name

def handle_client(client_socket, client_address):
    print(f"Connection established with{client_address}")

    global exit_flag

    while not exit_flag: 
        try: 
            command_prompt = client_socket.recv(BUFFER_SIZE)

            # break the loop if no data is received
            if not command_prompt:
                break

            decoded_command = command_prompt.decode()

            print('Decoded command: ', decoded_command)

            if decoded_command == 'store':
                # Receive additional data for the 'store' command
                filename = client_socket.recv(BUFFER_SIZE).decode()

                print(filename)

                file_size = int(client_socket.recv(BUFFER_SIZE).decode())

                file_content = recvall(client_socket, file_size)

                print('Length of file: ', file_size)

                # Construct a JSON-like object
                command_data = {
                    'command': 'store',
                    'filename': filename,
                    'file_content': file_content  # Assuming file_content is a string
                }

                # Process the 'store' command with the constructed data
                processCommandsFromClients(command_data, client_socket, client_address)

            elif decoded_command == 'get':
                # Receive the additional data for the 'get' command
                filename = client_socket.recv(BUFFER_SIZE).decode()

                # Construct a JSON-like object
                command_data = {
                    'command': 'get',
                    'filename': filename,
                }      

                processCommandsFromClients(command_data, client_socket, client_address)

            else:
                # For other commands, process as usual
                processCommandsFromClients(command_prompt, client_socket, client_address)

        except Exception as e:
            print(f'Error handling client. {e}')
            break

""" OTHER FUNCTIONS """
def recvall(sock, size):
    data = b""
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            break
        data += packet
    return data
        
# initialize the server socket 
server_socket = socket(AF_INET, SOCK_STREAM) 

# Loops until a successful server is started
while True:
    print("FIle Transfer TCP Server")
    try:
        # ip = input("Enter IP: ")                  # user inputs IP Address for the server to bind
        # port = input("Enter Port: ")              # user inputs the Port Number for the server to bind\
        ip = "127.0.0.1"
        port = "4000"
        server_socket.bind((ip, int(port)))         # Bind the socket to a specific IP address and port
        server_socket.listen(1)                     # sets the maximum ammount of connections allowed 
        print(f"Server running at {ip}:{port}")     
        break

    except Exception as e:
        os.system('cls')
        print(f"Error: {str(e)}\nTry again\n")



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