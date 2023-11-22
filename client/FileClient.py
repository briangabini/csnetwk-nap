from socket import *
import threading # aralin pa to
import json
import time
import os
import base64

BUFFER_SIZE = 1024
is_connected = False # initialize the connection status of the client to False

# function to create a new socket
def create_client_socket():
    return socket(AF_INET, SOCK_STREAM)

# Create client socket
client_socket = create_client_socket()

def forwardToServer(command_prompt):
    """ Forwards the command of the user to the server via sockets.
    Parameters
    ----------
    command_prompt : str
        command entered by the user 
    """

    global is_connected         # refer to the global variable 'is_connected'
    global server_address       # refer to the global variable 'server_address'
    global client_socket        # refer to the global variable 'client_socket'

    # check if the command starts with '/'
    if not command_prompt.startswith('/'):
        print('Error: Command not found. Type /? for help.')    # Error Prompt due to command syntax 
        return 
    
    # get the commands by separating the string
    inputs =  command_prompt.split()        # use the split() to separate strings
    command = inputs[0]                     # assign the command var with the first string
    params = inputs[1:]                     # assign the params list with the second string onwards

    # TODO: Implement the following commands

    # switch statement to handle commands
    match command:

        # Connect to the server application
        case '/join':
            

            # check first if the client is already connected to the server
            if not is_connected:    
                if len(params) == 2:                    # check if there are params
                    server_address = (params[0], int(params[1])) # assign the address with the params 

                    try: 
                        client_socket = create_client_socket()

                        client_socket.connect(server_address)
                        print('Connection to the File Exchange Server is successful!')

                        # client_socket.send(json.dumps({'command': 'join'}).encode())

                        # server_response = client_socket.recv(BUFFER_SIZE).decode()

                        # print(f'Server: {server_response}')

                        is_connected = True

                    except Exception as e:
                        print(f'Connection unsuccessful: {e}')

                else:
                    print('Error: Command parameters do not match or is not allowed.\nType /? for help.')
            else:
                print('Client is already connected. Use /leave to disconnect from the server.')

        # Disconnect to the server application
        case '/leave':
            if is_connected:
                if len(params) != 0:
                    print('Error: Command parameters do not match or is not allowed.\nUsage: /leave')
                else:
                    client_socket.send(json.dumps({'command': 'leave'}).encode())
                    client_socket.close()
            else:
                print('Error. Please connect to the server first.')

        # Register a unique handle or alias
        case '/register':
            if is_connected:
                if len(params) != 1:
                    print('Error: Command parameters do not match or is not allowed.\nUsage: /register <handle>')
                else:
                    client_socket.send(json.dumps({'command' : 'register', 'handle' : params[0]}).encode())
            else:
                print('Error: Please connect to the server first.')
            

        # Send file to server
        case '/store':
            if is_connected:
                if len(params) != 1:
                    print('Error: Command parameters do not match or are not allowed.\nUsage: /store <filename>')
                else:
                    file_path = './' + params[0]  # Store file to server folder

                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as file:
                            file_content = file.read()

                            client_socket.send(b'store')            # Signal the server that the client wants to store a file

                            time.sleep(0.1)

                            client_socket.send(params[0].encode())  # Send the filename

                            time.sleep(0.1)
                            # Send the file content
                            print('Length of file: ', len(file_content))

                            client_socket.send(str(len(file_content)).encode())

                            send_file(client_socket, file_content)
                            
                        print(f'{params[0]} successfully sent to the server.')
                        
                    else:
                        print('Error: File does not exist.')
            else:
                print('Error: Please connect to the server first.')

        # Fetch a file from a server
        case '/get':
            if is_connected:
                if len(params) != 1:
                    print('Error: Command parameters do not match or are not allowed.\nUsage: /get <filename>')

                else:
                    client_socket.send(b'get')            # Signal the server that the client wants to get a file

                    client_socket.send(params[0].encode())  # Send the filename

                    # receive the data
                    file_size = int(client_socket.recv(BUFFER_SIZE).decode())

                    print(file_size)

                    file_content = recvall(client_socket, file_size)

                    
                    filename = params[0]

                     # Check if file with same file name already exists in server directory
                    server_dir = os.listdir("./")
                    filename = get_unique_filename(filename, server_dir)
                    file_path = './' + filename

                    with open(file_path, 'wb') as file:                      # write the file_content to the newly created file
                        file.write(file_content)

                    print(f'Server successfully stored {filename} to the client directory.')


            else:
                print('Error: Please connect to the server first.')

        # Request directory file list from a server
        case '/dir':
            if is_connected:
                if len(params) != 0:
                    print('Error: Command parameters do not match or is not allowed.\nUsage: /dir')
                else:
                    client_socket.send(json.dumps({'command' : 'dir'}).encode())

                    server_response = client_socket.recv(BUFFER_SIZE).decode()

                    print(f'Server: {server_response}')
            else:
                print('Error: Please connect to the server first.')

        # displays the command help 
        case '/?':
            help_prompt()
            
        # default command: handles command syntax that doesn't match pre-defined commands
        case _:
            print('Error: Command not found. Type /? for help.')    # might be redundant, test later

""" OTHER FUNCTIONS """
def help_prompt():
    """ Displays the command help to the command line interface.
    """

    print('COMMAND DESCRIPTION                          INPUT SYNTAX')
    print('Connect to the server Application            /join <server_ip_add> <port>')
    print('Disconnect to the server application         /leave')
    print('Register a unique handle or alias            /register <handle>')
    print('Send file to server                          /store <filename>')
    print('Request directory file list from a server    /dir')
    print('Fetch a file from a server                   /get <filename>')
    print('Fetch a file from a server                   /get <filename>')

def recvall(sock, size):
    bytes_read = 0  # Keep track of the number of bytes read
    data = b"" # Stores the data being received

    # Loop until there are no more bytes left to read
    while bytes_read < size:
        packet = client_socket.recv(BUFFER_SIZE)  # Read data from the sender
        time.sleep(0.01)
        data += packet # Store data 
        bytes_read = len(data)  # Get the number of bytes read so far

    return data

def send_file(socket, file_content):
    file_position = 0
    while file_position < len(file_content):
        remaining_bytes = min(BUFFER_SIZE, len(file_content) - file_position)
        # Send a part of data to client
        socket.send(file_content[file_position:file_position + remaining_bytes])
        time.sleep(0.01)
        # Update file position
        file_position += remaining_bytes

def get_unique_filename(file_name, server_dir):
    base, ext = os.path.splitext(file_name)
    counter = 1
    new_file_name = file_name

    while new_file_name in server_dir:
        new_file_name = f"{base}({counter}){ext}"
        counter += 1

    return new_file_name


# loops while the client is running to send commands to server until the client is running
while True: 
    # Get commands from the user, forwarded to the server
    command = input("\nInput Command\n> ")
    print()
    
    # use a function to forward this to the server along with the command
    forwardToServer(command)