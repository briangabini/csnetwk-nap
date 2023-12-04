from socket import *
import os
import time
import threading
import json

BUFFER_SIZE = 1024              # initialize buffer size
exit_flag = False               # signal the thread to exit, use for manually exiting the server
connected_clients = []          # store the connected clients 
disconnected_clients = []           

def processCommandsFromClients(command_prompt, client_socket, client_address):
    """Execute server commands based on client queries.

    This function interprets client commands and performs corresponding actions on the server.

    Parameters:
        command_prompt (bytes or object): The command entered by the client. It can be either a JSON-formatted string or a javascript object.
        client_socket (socket): The socket endpoint connected to the client.
        client_address (tuple): The address of the client in the form of (ip, port).

    Raises:
        JSONDecodeError: If the command_prompt is a string but cannot be decoded as a JSON object.

    Example:
        processCommandsFromClients('{"command": "leave"}', client_socket_instance, ('127.0.0.1', 12345))
    """

    # execute this block when the command_prompt value is a json object
    try:
        
        # deserialize string to python <dict>
        data = json.loads(command_prompt.decode())      

        # assign the command
        command = data['command']   
        #print(command)         # for debugging remove this             

    # execute this block when the command_prompt value is a <dict>
    except:
        command = command_prompt['command']
        #print(command) # for debugging remove this

    # check if the command exists in the list of cases
    match command:
        
        # Close the connection in the server side
        case 'leave':
            # Close the socket connected to the client
            print(f'The client {client_address} disconnected.\n')

            # DEBUG
            # print(connected_clients) 

            # Remove the disconnected client from the connected_clients list
            disconnected_client = next((client for client in connected_clients if client['address'] == client_address), None)

            # remove disconnected_client from the list of connected clients
            if disconnected_client:
                connected_clients.remove(disconnected_client)


            response = "Closing the connection to the client."

            # Let the client know a response will be sent
            to_send = json.dumps({'command': 'response', 'message': 'Server: Sending a response'}).encode()
            to_send_size = len(to_send)
            client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
            client_socket.send(to_send)

            # Send response to the client
            to_send = json.dumps({'status': 'OK', 'message': response}).encode()
            to_send_size = len(to_send)
            client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
            client_socket.send(to_send)

            client_socket.close()

            global exit_flag
            exit_flag = True

            # DEBUG
            # print(connected_clients) 
            # print(disconnected_client)

        # Register the client to the server by appending to the array of connected clients
        case 'register':

            # assign the handle name 
            handle = data['handle']

            # get the client from the connected_clients list based on the 'name' property
            filtered_clients = list(filter(lambda client: client['name'] == handle, connected_clients))

            # check if the client is already registered
            if filtered_clients:             

                # print the mesasge 
                print(f'User {handle} already exists.')

                # set the response
                response = f'User {handle} already exists. Choose a different handle.'

                # Let the client know a response will be sent
                to_send = json.dumps({'command': 'response', 'message': 'Server: Sending a response'}).encode()
                to_send_size = len(to_send)
                client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
                client_socket.send(to_send)

                # Send the response
                to_send = json.dumps({'status': 'NO', 'message': response}).encode()
                to_send_size = len(to_send)
                client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
                client_socket.send(to_send)

            else:
                # get the client from the connected_clients list based on the 'address' property
                filtered_clients = list(filter(lambda client: client['address'] == client_address, connected_clients))

                # check if the client is already connected
                if filtered_clients:

                    # access the client's data
                    client = filtered_clients[0]

                    # assign the client's handle name to the client's existing data in the connected_clients list
                    client['name'] = handle
 
                    # initialize a response 
                    response = f'Successfully registered User {handle}'
                    
                    # Let the client know a response will be sent
                    to_send = json.dumps({'command': 'response', 'message': 'Server: Sending a response'}).encode()
                    to_send_size = len(to_send)
                    client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
                    client_socket.send(to_send)

                    # Send the response
                    to_send = json.dumps({'status': 'OK', 'message': response}).encode()
                    to_send_size = len(to_send)
                    client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
                    client_socket.send(to_send)
                else:
                    # print the message
                    print(f'User doesn\'t exist.')
        
            # DEBUG
            # print(f'connected: {connected_clients}')
            # print(f'disconnected: {disconnected_clients}')

        # Send the filenames of files in the server directory to the client
        case 'dir':

            # Get all files from current directory
            dir_list = os.listdir("./")

            # Back to original dir 
            os.chdir(os.getcwd()) 

            # Remove FileServer.py from list
            dir_list.remove('FileServer.py')

            # initialize 'directory' which will be assigned with the dir_list
            directory = 'Directory: \n'

            # iterate through the dir_list and assign the filenames to 'directory'
            for file in dir_list:
                directory += f'- {file}\n'
            
            # assign the message 
            message = 'Successfully retrieved file list in directory.'

            # Let the client know a response will be sent
            to_send = json.dumps({'command': 'response', 'message': 'Server: Sending a directory'}).encode()
            to_send_size = len(to_send)
            client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
            client_socket.send(to_send)

            # Send the response
            to_send = json.dumps({'status': 'OK', 'message': message, 'directory': directory}).encode()
            to_send_size = len(to_send)
            client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
            client_socket.send(to_send)

        case 'store':
            # Store file to server folder
            filename = command_prompt['filename']

            # get the file size from the client
            file_size = int(client_socket.recv(BUFFER_SIZE).decode())

            # get the content of the file from the client
            file_content = recvall(client_socket, file_size)  

            # Check if file with same file name already exists in server directory
            server_dir = os.listdir("./")

            # set the filename
            filename = get_unique_filename(filename, server_dir)

            # set the file path
            file_path = './' + filename    

            # print to terminal 
            print('Filename: ', filename)        

            # Get the file content
            # print(file_content)

            with open(file_path, 'wb') as file:                      
                # write the file_content to the newly created file
                file.write(file_content)

            response = f'Successfully stored {filename}.'

            # Let the client know a response will be sent
            to_send = json.dumps({'command': 'response', 'message': 'Server: Sending a response'}).encode()
            to_send_size = len(to_send)
            client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
            client_socket.send(to_send)

            # Send the response
            to_send = json.dumps({'status': 'OK', 'message': response}).encode()
            to_send_size = len(to_send)
            client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
            client_socket.send(to_send)

            log_message = f'{client_address} successfully stored {filename} to the server.'

            print(f'Log: {log_message}')

            # get the client from the connected_clients list based on the 'address' property
            filtered_clients = list(filter(lambda client: client['address'] == client_address, connected_clients))

            # access the client's data
            client = filtered_clients[0]

            # get the client's name 
            client_name = client['name']

            # NOT WORKING WHEN A CLIENT HAS ONGOING PROCESS
            # Inform all users a file has been uploaded
            message = json.dumps(f'{client_name} uploaded a file')
            broadcast_to_all(client_address, message)

        case 'get':
            # set the filename
            filename = command_prompt['filename']

            # set the file path
            file_path = './' + filename

            # check if the file exists
            if os.path.exists(file_path):

                # Let the client know a file will be sent
                to_send = json.dumps({'command': 'file', 'message': 'Sending a file'}).encode()
                to_send_size = len(to_send)
                client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
                client_socket.send(to_send)

                time.sleep(0.1)

                # read the file as binary and assign to 'file'
                with open(file_path, 'rb') as file:
                    # get the content of the file
                    file_content = file.read()

                # send the file length
                client_socket.send(str(len(file_content)).encode().zfill(BUFFER_SIZE))    

                # DEBUG 
                # print(len(file_content))

                # for data integrity
                time.sleep(0.1)

                # DEBUG
                # print('Type of file_content: ', type(file_content))

                # DEBUG
                # print('file_content: ', file_content)

                # send the file to the client
                send_file(client_socket, file_content)

                # for data integrity
                time.sleep(0.1)

                response = f'Successfully stored {filename} to the client directory.'

                # Send response to server
                to_send = json.dumps({'status': 'OK', 'message': response}).encode()
                to_send_size = len(to_send)
                client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
                client_socket.send(to_send)

                log_message = f"A user retrieved {filename}."

                print(f'Log: {log_message}')

                # broadcast_to_all(client_address, 'Some user retrieved a file.')
            
            else:
                # print error to terminal 
                print('Error: File does not exist.')

                # Let the client know a file will be sent
                to_send = json.dumps({'command': 'file', 'message': 'Sending a file'}).encode()
                to_send_size = len(to_send)
                client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
                client_socket.send(to_send)

                # Signal to client that file does not exist
                client_socket.send(str(0).encode().zfill(BUFFER_SIZE))

                # Send error message to the client
                response = f'File does not exist'
                to_send = json.dumps({'status': 'ERROR', 'message': response}).encode()
                to_send_size = len(to_send)
                client_socket.send(str(to_send_size).encode().zfill(BUFFER_SIZE))
                client_socket.send(to_send)
                print('server done')
                
def get_unique_filename(file_name, server_dir):
    """
    Generate a unique filename by appending a counter to the base filename
    if a file with the same name already exists in the specified directory.

    Parameters:
        file_name (str): The original filename.
        server_dir (list): A list of existing filenames in the server directory.

    Returns:
        str: A unique filename.

    Usage:
        unique_filename = get_unique_filename("example.txt", server_directory_list)
    """

    # get the base filename, and file ext of the file
    base, ext = os.path.splitext(file_name)

    # set the counter
    counter = 1

    # assign new_file_name with original filename
    new_file_name = file_name

    # loop until successfully finding a unique filename
    while new_file_name in server_dir:

        # set new filename
        new_file_name = f"{base}({counter}){ext}"
        counter += 1

    # return the new filename
    return new_file_name

def handle_client(client_socket, client_address):
    """ 
    Handle queries sent by the client.

    Parameters:
        client_socket (socket): The socket endpoint connected to the client.
        client_address (_RetAddress): The address of the client in the form of (ip, port).

    Global Variable:
        exit_flag (bool): A global variable indicating whether to exit the client handling loop.

    Usage:
        handle_client(client_socket_instance, client_address_tuple)
    """
    # print to terminal 
    print(f"Connection established with {client_address}")

    global exit_flag        
    exit_flag = False
    

    # loop until exit_flag is True
    while not exit_flag: 
        try: 

            # get the queries from the client 
            command_prompt = client_socket.recv(BUFFER_SIZE)

            # break the loop if no data is received
            if not command_prompt:
                break

            # get the command from the query
            decoded_command = command_prompt.decode()

            # check if the command is 'store'
            if decoded_command == 'store':

                # get the filename from the client                
                filename = client_socket.recv(BUFFER_SIZE).decode()


                # Construct a JSON-like object
                command_data = {
                    'command': 'store',
                    'filename': filename,
                }

                # Process the 'store' command with the constructed data
                processCommandsFromClients(command_data, client_socket, client_address)

            # check if the command is 'get'
            elif decoded_command == 'get':

                # get the filename from the client                
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

            # Remove the disconnected client from the connected_clients list
            disconnected_client = next((client for client in connected_clients if client['address'] == client_address), None)

            # remove disconnected_client from the list of connected clients
            if disconnected_client:
                connected_clients.remove(disconnected_client)

            client_socket.close()

            break

""" OTHER FUNCTIONS """
def recvall(sock, size):
    """ 
    Receive a specified amount of data from a socket.

    Parameters:
        sock (socket): The socket endpoint connected to the client.
        size (int): The total size of the data being received.

    Returns:
        bytes: The received data.

    Raises:
        Any exceptions raised during socket operations.

    Usage:
        received_data = recvall(socket_instance, total_data_size)
    """

    bytes_read = 0  # Keep track of the number of bytes read
    data = b"" # Stores the data being received

    # Loop until there are no more bytes left to read
    while bytes_read < size:

        # Read data from the sender
        if (size - bytes_read) < BUFFER_SIZE:
            packet = sock.recv(size - bytes_read)
        else:
            packet = sock.recv(BUFFER_SIZE)

        # pause for a moment for data integrity
        time.sleep(0.01)

        # Store data 
        data += packet 

        # Get the number of bytes read so far
        bytes_read = len(data)  

    # return 'data' which contains the file data
    return data

def send_file(socket, file_content):
    """
    Send the content of a file over a socket in chunks.

    Parameters:
        socket (socket): The socket over which the file content will be sent.
        file_content (bytes): The content of the file in bytes.

    Returns:
        None

    Raises:
        Any exceptions raised during socket operations.

    Usage:
        send_file(socket_instance, file_content_bytes)
    """

    # set file position to 0
    file_position = 0

    # loop until file position is within the length of the file size
    while file_position < len(file_content):

        # assign the remaining bytes 
        remaining_bytes = min(BUFFER_SIZE, len(file_content) - file_position)

        # Send a part of data to client
        socket.send(file_content[file_position:file_position + remaining_bytes])

        # for data integrity
        time.sleep(0.01)

        # Update file position
        file_position += remaining_bytes

def broadcast_to_all(current_user_address, message):
    """
    Broadcast a message to all connected clients except the current user.

    Parameters:
        current_user_address (tuple): The address of the current user in the form of (ip, port).
        message (str): The message to be broadcasted.

    Usage:
        broadcast_to_all(('127.0.0.1', 12345), 'Hello, everyone!')
    """
    print('Curr address: ', current_user_address)

    for client in connected_clients:
        # print(client)

        if client['address'] != current_user_address:
            try:
                # Let the client know a broadcast will be sent
                to_send = json.dumps({'command': 'broadcast', 'message': 'Server: Sending a broadcast'}).encode()
                to_send_size = len(to_send)
                client['socket'].send(str(to_send_size).encode().zfill(BUFFER_SIZE))
                client['socket'].send(to_send)

                # Send the broadcast
                to_send = json.dumps({'status': 'OK', 'message': message}).encode()
                to_send_size = len(to_send)
                client['socket'].send(str(to_send_size).encode().zfill(BUFFER_SIZE))
                client['socket'].send(to_send)

                # print(message)
                # print(client['socket'])
            except Exception as e:
                print(f"Error broadcasting to {client['address']}: {e}")
        
# initialize the server socket 
server_socket = socket(AF_INET, SOCK_STREAM) 

# Loops until a successful server is started
while True:

    # print to terminal 
    print("File Transfer TCP Server")

    # ip = input("Enter IP: ")                  # user inputs IP Address for the server to bind
    # port = input("Enter Port: ")              # user inputs the Port Number for the server to bind\
    ip = "127.0.0.1"                            # hard coded for now
    port = "12345"                               # hard coded for now

    try:
        server_socket.bind((ip, int(port)))         # Bind the socket to a specific IP address and port
        server_socket.listen(5)                     # sets the maximum ammount of connections allowed 

        # print to terminal 
        print(f"Server running at {ip}:{port}")     
        break

    except Exception as e:

        # clear the terminal if there's an exception
        os.system('cls')
        print(f"Error: {str(e)}\nTry again\n")



try:      
    # Accept incoming connections  
    while True:

        # print to terminal
        print("Waiting for a connection...")

        # accept the connection from incoming clients
        client_socket, client_address = server_socket.accept()      

        # response of the server to the client
        response = "Connection established to server." 

        # send the response to the client after connecting
        client_socket.send(json.dumps({'status': 'OK', 'message': response}).encode())

        # Create a new thread for each client
        # this allows multiple tasks to run concurrently, in this case, handling multiple clients
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

        # test what will happen if we don't use threads
        # handle_client(client_socket, client_address) # only one client at a time is possible since, multiple clients will share 

        # initialize a new user 
        new_user = {'address' : client_address, 'socket': client_socket, 'name': ""}

        # Add user to list of connected clients
        connected_clients.append(new_user)

        
finally:
    #closes the server socket when done
    server_socket.close()