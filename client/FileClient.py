from socket import *
import json
import time
import os

BUFFER_SIZE = 1024          # initialize buffer size
is_connected = False        # initialize the connection status of the client to False
is_registered = False       # initialize the registered status of the client fo False

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
    global is_registered        # refer to the global variable 'is_registered'
    global server_address       # refer to the global variable 'server_address'
    global client_socket        # refer to the global variable 'client_socket'
    
    # get the commands by separating the string
    inputs =  command_prompt.split()        # use the split() to separate strings
    command = inputs[0]                     # assign the command var with the first string
    params = inputs[1:]                     # assign the params list with the second string onwards

    # switch statement to handle commands
    match command:

        # Connect to the server application
        case '/join':
            
            # check first if the client is already connected to the server
            if not is_connected:    

                # check if there are params which consist of the ip address and port number
                if len(params) == 2:                                    
                    server_address = (params[0], int(params[1]))        # assign the address with the params 

                    try: 
                        # create a new client every time 
                        client_socket = create_client_socket()          

                        # connect the new socket with the server_address(ip, port)
                        client_socket.connect(server_address)          

                        # get the response from the server after attempting to connect to the server
                        server_response = json.loads(client_socket.recv(BUFFER_SIZE).decode())

                        # assign the message var with the message property of the response
                        message = server_response['message']

                        # print the message response sent by the server
                        print(f'Server: {message}')

                        # check if the server sent a status OK
                        if server_response['status'] == 'OK':
                            # assign the 'is_connected' var with True
                            is_connected = True

                    except Exception as e:
                        print(f'Connection unsuccessful: {e}')

                else:
                    print('Error: Command parameters do not match or is not allowed.\nType /? for help.')
            else:
                print('Client is already connected. Use /leave to disconnect from the server.')

        # Disconnect to the server application
        case '/leave':

            # check if the client is connected 
            if is_connected:

                # check if the user did not input params 
                if len(params) != 0:
                    # print the error to the terminal 
                    print('Error: Command parameters do not match or is not allowed.\nUsage: /leave')

                else:

                    # send a json object that contains the command of the user 
                    client_socket.send(json.dumps({'command': 'leave'}).encode())
                    client_socket.close()
            else:
                print('Error. Please connect to the server first.')

        # Register a unique handle or alias
        case '/register':
            if is_connected:
                if not is_registered:
                    if len(params) != 1:
                        print('Error: Command parameters do not match or is not allowed.\nUsage: /register <handle>')
                    else:
                        client_socket.send(json.dumps({'command' : 'register', 'handle' : params[0]}).encode())

                        server_response = json.loads(client_socket.recv(BUFFER_SIZE).decode()) # get the response of the server in json format

                        print(server_response['message'])

                        if server_response['status'] == 'OK':
                            is_registered = True

                else:
                    # print to terminal
                    print('You can only register once.')

            else:
                # print to terminal
                print('Error: Please connect to the server first.')
            
        # Send file to server
        case '/store':
            if is_connected:
                if is_registered:
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

                            send_file(client_socket, file_content)
                            
                        print(f'{params[0]} successfully sent to the server.')
                        
                        else:
                            print('Error: File does not exist.')
                else:
                    print('Error: Please register first.')
            else:
                print('Error: Please connect to the server first.')

        # Fetch a file from a server
        case '/get':
            if is_connected:
                if is_registered:
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
                    print('Error: Please register first.')

            else:
                print('Error: Please connect to the server first.')

        # Request directory file list from a server
        case '/dir':

            # check if the user is connected
            if is_connected:

                # check if the user is registered
                if is_registered:

                    # check if there are params entered by the user
                    if len(params) != 0:

                        # print to terminal
                        print('Error: Command parameters do not match or is not allowed.\nUsage: /dir')
                    else:

                        # send the command to server via json object
                        client_socket.send(json.dumps({'command' : 'dir'}).encode())

                        # get the response from the server in object notation
                        server_response = json.loads(client_socket.recv(BUFFER_SIZE).decode())

                        directory = server_response['directory']

                        # check if the response status is OK
                        if server_response['status'] == 'OK':
                            print(directory)

                else:
                    # print to terminal
                    print('Error: Please register first')

            else:
                # print to terminal
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
    """ This method executes the appropriate functions of the server based on the query from client/s

    PARAMETERS
    ----------
    sock: socket
        socket endpoint connected to the client
    size: int
        total size of the file being retrieved.
    """

    bytes_read = 0  # Keep track of the number of bytes read
    data = b"" # Stores the data being received

    # Loop until there are no more bytes left to read
        
    while bytes_read < size:
        packet = sock.recv(BUFFER_SIZE)  # Read data from the sender
        time.sleep(0.01)
        data += packet # Store data 
        bytes_read = len(data)  # Get the number of bytes read so far

    # return 'data' which contains the file data
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