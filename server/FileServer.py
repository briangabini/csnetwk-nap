from socket import *
import sys
import os
import time
import threading
import json
import base64

BUFFER_SIZE = 1024 
file_content = b''

# signal the thread to exit
exit_flag = False

connected_clients = []                 
disconnected_clients = []

# TODO: make a function that processes the commands from the client/s
def processCommandsFromClients(command_prompt, client_socket, client_address):

    try:
        data = json.loads(command_prompt.decode())
        command = data['command']
    except Exception as e:
        # command = client_socket.recv(BUFFER_SIZE)
        command = command_prompt['command']
        # command = command_prompt.decode()
        print('Command: ' + command)
        # print('Next: ', client_socket.recv(BUFFER_SIZE).decode())

    # print(data)

    """ if not data:
        command = client_socket.recv(BUFFER_SIZE) """

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
            print(dir)

            # send the dir to client using client_socket.send()
        # case 'store':
        #     # TODO: Avoid duplicates when storing
        #     filename = data['filename']             # Get filename
        #     file_path = './server/' + filename      # Store file to server folder
        #     file = data['file']                     # Get the contents of the file

        #     # file_bytes = file.encode()
        #     received_image = base64.b64decode(file.encode())

        #     # f = open(file_path,"w+")                # Create a file     
        #     # f.write(received_image)                 # Overwrite the contents

        #     with open(file_path, 'wb') as file:
        #             file.write(received_image)
        #     print(f'{client_address} successfully stored {filename} to the server.')
        case 'store':
            # TODO: Avoid duplicates when storing
            # filename = data['filename']  # Get filename
            # filename = client_socket.recv(BUFFER_SIZE)
            filename = command_prompt['filename']
            file_path = './' + filename  # Store file to server folder

            print('Filename: ', filename)

            global file_content

            # Get the file content
            # file_content = command_prompt['file_content']
            local_file_content = file_content

            print('Type of file_content: ', type(file_content))

            with open(file_path, 'wb') as file:
                file.write(file_content)

            print(f'{client_address} successfully stored {filename} to the server.')

        case 'get':
            pass

def handle_client(client_socket, client_address):
    print(f"Connection established with{client_address}")

    global exit_flag
    global file_content

    # Wait for commands from the client
    # while not exit_flag: 
    #     try: 
    #         command_prompt = client_socket.recv(BUFFER_SIZE)

    #         # break the loop if no data is received
    #         if not command_prompt:
    #             break

    #         if command_prompt.decode() == 'store':
    #             # assign command_prompt with as an object containing
    #             """ 
    #             {
    #                command: 'store',
    #                filename: client_socket.recv(BUFFER_SIZE).encode(),
    #                file_content: client_socket.recv(BUFFER_SIZE)
    #             } 
    #             """

    #         processCommandsFromClients(command_prompt, client_socket, client_address) # Process the command
        
    #     except Exception as e:
    #         print(f'Error handling client. {e}')
    #         break

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

                print('Length of file: ', len(file_content))

                # Construct a JSON-like object
                command_data = {
                    'command': 'store',
                    'filename': filename,
                    # 'file_content': file_content  # Assuming file_content is a string
                }

                # Process the 'store' command with the constructed data
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