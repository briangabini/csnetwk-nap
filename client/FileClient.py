from socket import *
from tabulate import tabulate
import json
import time
import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk

BUFFER_SIZE = 1024          # initialize buffer size
is_connected = False        # initialize the connection status of the client to False
is_registered = False       # initialize the registered status of the client fo False
exit_flag = False           # initialize the exit flag for receiving thread
server_response = None      # initialize the responses from the server
file_size = None            # initialize the file size from the server
file_contents = None        # initialize the file contents from the server
bytes_read = 0              # initialize the bytes read so far from the server

class FileClient():
    # Initalize an instance of FileClient class
    def __init__(self, gui):
        self.GUI = gui

    # function to create a new socket
    def create_client_socket(self):
        return socket(AF_INET, SOCK_STREAM)

    # # Create client socket
    # client_socket = create_client_socket()

    def forwardToServer(self, command_prompt):
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
        global exit_flag            # refer to the global variable 'exit_flag'
        global server_response      # refer to the global variable 'server_response'
        global file_size            # refer to the global variable 'file_size '
        global file_contents        # refer to the global variable 'file_contents'
        global bytes_read
        
        # get the commands by separating the string
        inputs =  command_prompt.split()        # use the split() to separate strings
        
        if len(inputs) == 0:
            return

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
                            exit_flag = False

                            # create a new client every time 
                            client_socket = self.create_client_socket()          

                            # connect the new socket with the server_address(ip, port)
                            client_socket.connect(server_address)          

                            # get the response from the server after attempting to connect to the server
                            server_response = json.loads(client_socket.recv(BUFFER_SIZE).decode())

                            # assign the message var with the message property of the response
                            message = server_response['message']

                            # print the message response sent by the server
                            print(f'Server: {message}')
                            self.GUI.log(f'Server: {message}')
                            

                            # check if the server sent a status OK
                            if server_response['status'] == 'OK':
                                # assign the 'is_connected' var with True
                                is_connected = True

                                # DEBUG: Display is_connected status
                                # print(f'is_connected is now: {is_connected}')

                                # Start the receive thread
                                self.start_receive_thread()
                        except Exception as e:
                            # print error to terminal 
                            print(f'Connection unsuccessful: {e}')
                            self.GUI.log(f'Connection unsuccessful: {e}')

                    else:
                        # print error to terminal 
                        print('Error: Command parameters do not match or is not allowed.\nType /? for help.')
                        self.GUI.log('Error: Command parameters do not match or is not allowed.\nType /? for help.')

                else:
                    # print error to terminal 
                    print('Client is already connected. Use /leave to disconnect from the server.')
                    self.GUI.log('Client is already connected. Use /leave to disconnect from the server.')
                
            # Disconnect to the server application
            case '/leave':

                # check if the client is connected 
                if is_connected:

                    # check if the user did not input params 
                    if len(params) != 0:
                        # print the error to the terminal 
                        print('Error: Command parameters do not match or is not allowed.\nUsage: /leave')
                        self.GUI.log('Error: Command parameters do not match or is not allowed.\nUsage: /leave')

                    else:
                        # send a json object that contains the command of the user 
                        client_socket.send(json.dumps({'command': 'leave'}).encode())

                        # Wait until a response is received from the server
                        while True:
                                if server_response != None:
                                    break

                        if server_response['status'] == 'OK':
                            # set the connection status to 'False'
                            is_connected = False

                            # set the registered status to 'False'
                            is_registered = False

                            # close the connection
                            client_socket.close()

                            exit_flag = True

                        # DEBUG: print message to terminal 
                        # print(f'is_connected is now: {is_connected}')
                else:
                    # print error to terminal
                    print('Error. Please connect to the server first.')
                    self.GUI.log('Error. Please connect to the server first.')

            # Register a unique handle or alias
            case '/register':

                # check if the client is connected 
                if is_connected:

                    # check if the user is not registered
                    if not is_registered:

                        # check if the user did not input params 
                        if len(params) != 1:
                            # print the error to the terminal 
                            print('Error: Command parameters do not match or is not allowed.\nUsage: /register <handle>')
                            self.GUI.log('Error: Command parameters do not match or is not allowed.\nUsage: /register <handle>')


                        else:
                            # Send command to the server
                            client_socket.send(json.dumps({'command' : 'register', 'handle' : params[0]}).encode())                     

                            # check if the server responded with status 'OK'
                            while True:
                                if server_response != None:
                                    break

                            if server_response['status'] == 'OK':

                                # set registered status to True
                                is_registered = True

                            else:
                                # set registered status to False
                                is_registered = False
                    else:
                        # print to terminal
                        print('You can only register once.')
                        self.GUI.log('You can only register once.')

                else:
                    # print to terminal
                    print('Error: Please connect to the server first.')
                    self.GUI.log('Error: Please connect to the server first.')

                # DEBUG
                # print(f'isRegistered: {is_registered}')

            # Send file to server
            case '/store':

                # check if the user is connected 
                if is_connected:

                    # check if the user is registered
                    if is_registered:

                        # check if the user inputted params
                        if len(params) != 1:

                            # print error to terminal 
                            print('Error: Command parameters do not match or are not allowed.\nUsage: /store <filename>')
                            self.GUI.log('Error: Command parameters do not match or are not allowed.\nUsage: /store <filename>')

                        else:
                            # initialize the file path to the file 
                            file_path = './' + params[0] 

                            # check if the file exists
                            if os.path.exists(file_path):
                                
                                # read the file as binary and assign to 'file'
                                with open(file_path, 'rb') as file:

                                    # assign the content of the file to 'file_content'
                                    file_content = file.read()

                                # Signal the server that the client wants to store a file
                                client_socket.send(b'store') 

                                print('Uploading file to the server. Please wait...')
                                self.GUI.log('Uploading file to the server. Please wait...')
                                

                                # pause first before sending again 
                                time.sleep(0.01)

                                # Send the filename
                                client_socket.send(params[0].encode()) 

                                # pause first before sending again 
                                time.sleep(0.01)

                                # DEBUG
                                # Send the file content
                                # print('Length of file: ', len(file_content))

                                client_socket.send(str(len(file_content)).encode()) 

                                # send the file to the server
                                self.send_file(client_socket, file_content)

                                time.sleep(0.1)

                                # Wait until the server sends a response
                                while True:
                                    if server_response != None:
                                        break
                                
                                # set the server response
                                message = server_response['message']

                                # print success message
                                print(f'Server: {message}')

                            else:
                                # print error to terminal 
                                print('Error: File does not exist.')
                                self.GUI.log('Error: File does not exist.')
                    else:
                        # print error to terminal 
                        print('Error: Please register first.')
                        self.GUI.log('Error: Please register first.')

                else:
                    # print error to terminal 
                    print('Error: Please connect to the server first.')
                    self.GUI.log('Error: Please connect to the server first.')

            # Fetch a file from a server
            case '/get':
                # check if the user is connected
                if is_connected:

                    # check if the user is registered
                    if is_registered:

                        # check if the user inputted params
                        if len(params) != 1:
                            # print error to terminal 
                            print('Error: Command parameters do not match or are not allowed.\nUsage: /get <filename>')
                            self.GUI.log('Error: Command parameters do not match or are not allowed.\nUsage: /get <filename>')
                            
                        else:
                            # Signal the server that the client wants to get a file
                            client_socket.send(b'get') 

                            # Send the filename
                            client_socket.send(params[0].encode())  

                            # Show the progress bar
                            self.GUI.show_progress_dialog(100, 'Retrieving')
                            self.GUI.progress_dialog.update()  

                            print('Retrieving file from the server. Please wait...')
                            self.GUI.log('Retrieving file from the server. Please wait...')

                            # Wait until all the data have been received from the server
                            while True:
                                if file_size != None:
                                     self.GUI.progress_bar['maximum'] = file_size
                                     self.GUI.update_progress(bytes_read)
                                if file_size != None and server_response != None and file_contents != None:
                                    break   

                            if file_size == 0:

                                message = server_response['message']

                                # print error message
                                print(f'Server: {message}')
                                self.GUI.log(f'Server: {message}')

                                # exit function
                                return

                            file_content = file_contents

                            message = server_response['message']

                            # print success message
                            print(f'Server: {message}')
                            self.GUI.log(f'Server: {message}')

                            # set the filename
                            filename = params[0]

                            # Check if file with same file name already exists in server directory
                            server_dir = os.listdir("./")
                            
                            # get unique filename
                            filename = self.get_unique_filename(filename, server_dir)

                            # set filepath
                            file_path = './' + filename

                            # write a file and assign to 'file'
                            with open(file_path, 'wb') as file:                      
                                # write the file_content to the newly created file
                                file.write(file_content)

                            self.GUI.close_progress_dialog()
                            message = f'Successfully stored {filename} to the client directory.'

                    else:
                        # print error to terminal 
                        print('Error: Please register first.')
                        self.GUI.log('Error: Please register first.')

                else:
                    # print error to terminal 
                    print('Error: Please connect to the server first.')
                    self.GUI.log('Error: Please connect to the server first.')

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
                            self.GUI.log('Error: Command parameters do not match or is not allowed.\nUsage: /dir')

                        else:

                            # send the command to server via json object
                            client_socket.send(json.dumps({'command' : 'dir'}).encode())

                            time.sleep(0.1)

                            # Wait until the server sends a response
                            while True:
                                if server_response != None:
                                    break

                            directory = server_response['directory']

                            if server_response['status'] == 'OK':
                                print(directory)
                                self.GUI.log(directory)

                    else:
                        # print to terminal
                        print('Error: Please register first')
                        self.GUI.log('Error: Please register first')

                else:
                    # print to terminal
                    print('Error: Please connect to the server first.')
                    self.GUI.log('Error: Please connect to the server first.')

            # displays the command help 
            case '/?':
                self.help_prompt()
                
            # default command: handles command syntax that doesn't match pre-defined commands
            case _:
                print('Error: Command not found. Type /? for help.')    # might be redundant, test later
                self.GUI.log('Error: Command not found. Type /? for help.')
        # Clear global variables used for receiving data
        server_response = None
        file_size = None
        file_contents = None


    """ OTHER FUNCTIONS """
    def help_prompt(self):
        """ 
        Display the command help in the command line interface.

        Usage:
            help_prompt()
        """

        commands = [
            ("/join", "Connect to the server application", "/join <server_ip_add> <port>"),
            ("/leave", "Disconnect from the server application", "/leave"),
            ("/register", "Register a unique handle or alias", "/register <handle>"),
            ("/store", "Send file to server", "/store <filename>"),
            ("/dir", "Request directory file list from a server", "/dir"),
            ("/get", "Fetch a file from a server", "/get <filename>")
        ]

        headers = ["Command", "Description", "Input Syntax"]

        print(tabulate(commands, headers=headers, tablefmt="fancy_grid"))
        self.GUI.log(tabulate(commands, headers=headers, tablefmt="simple", maxcolwidths=[None, 35]))

    def recvall(self, sock, size):
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
        global bytes_read


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

            # Update the progress bar


        # Close the progress bar

        # return 'data' which contains the file data
        return data

    def send_file(self, socket, file_content):
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

        
        # Show the progress bar
        self.GUI.show_progress_dialog(len(file_content), 'Uploading')

        # loop until file position is within the length of the file size
        while file_position < len(file_content):

            # assign the remaining bytes 
            remaining_bytes = min(BUFFER_SIZE, len(file_content) - file_position)

            # Send a part of data to client
            socket.send(file_content[file_position:file_position + remaining_bytes])

            # Update the progress bar
            self.GUI.update_progress(file_position)

            # for data integrity
            time.sleep(0.01)

            # Update file position
            file_position += remaining_bytes

        # Close the progress bar
        self.GUI.close_progress_dialog()

    def get_unique_filename(self, file_name, server_dir):
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



    # Processes commands received from the server
    def fromServer(self, command):
        """
        Processes commands received from the server.

        Parameters:
            command (str): The command received from the server.

        Global Variables Used:
            client_socket: The socket connected to the server.
            file_size (int): Size of the file received from the server.
            server_response (dict): Response received from the server.
            file_contents (str): Contents of the file received from the server.

        Usage:
            fromServer('response')  # Processes 'response' command from the server
        """


        global client_socket        # refer to the global variable 'client_socket'
        global server_response      # refer to the global variable 'server_response'
        global file_size            # refer to the global variable 'file_size '
        global file_contents        # refer to the global variable 'file_contents'
        
        # Receive file
        if command == 'file':
            # File size
            file_size = int(client_socket.recv(BUFFER_SIZE).decode())
            time.sleep(0.1)

            # if server sends 0 file size, file does not exist
            if file_size == 0:
                # Receive a json with 'status' and 'message'
                size = int(client_socket.recv(BUFFER_SIZE).decode())
                data = json.loads(client_socket.recv(size).decode())

                server_response = data
                file_contents = "not found"


            file_contents = self.recvall(client_socket, file_size)

            # Receive a json with 'status' and 'message'
            size = int(client_socket.recv(BUFFER_SIZE).decode())
            data = json.loads(client_socket.recv(size).decode())


            server_response = data
            

        
        # Receive a global or error message 
        elif command == 'response':
            # Receive a json with 'status' and 'message'
            size = int(client_socket.recv(BUFFER_SIZE).decode())
            data = json.loads(client_socket.recv(size).decode())

            server_response = data
            
            print(f"Server: {data['message']}\n", end="")
            self.GUI.log(f"Server: {data['message']}")
            time.sleep(0.1)

        elif command == 'broadcast':
            # Receive a json with 'status' and 'message'
            size = int(client_socket.recv(BUFFER_SIZE).decode())
            data = json.loads(client_socket.recv(size).decode())

            server_response = data
            
            print(f"Server: {data['message']}\n", end="")
            self.GUI.log(f"Server: {data['message']}")
            time.sleep(0.1)
            

    def receive_messages(self):
        """
        Continuously receives and processes messages from the server

        Global Variables Used:
            exit_flag (bool): Flag to control the loop.
            client_socket: The socket connected to the server.
            server_response (dict): Response received from the server.
            file_size (int): Size of the file received from the server.
            file_contents (str): Contents of the file received from the server.

        Usage:
            This function runs in a separate thread to continuously receive and process messages.
            start_receive_thread() function initiates this thread.
        """
        global client_socket        # refer to the global variable 'client_socket'
        global exit_flag            # refer to the global variable 'exit_flag'
        global server_response      # refer to the global variable 'server_response'
        global file_size            # refer to the global variable 'file_size '
        global file_contents        # refer to the global variable 'file_contents'
        
        while not exit_flag:
            try: 
                # Receive message from the server
                size = client_socket.recv(BUFFER_SIZE).decode()
        
                size = int(size)
                data = json.loads(client_socket.recv(size).decode())

                # Receive a json with 'command', 'message'
                command = data['command']

                self.fromServer(command)
        
            except Exception as e: 
                print(f'Error receiving message: {e}')
                break

    def start_receive_thread(self):
        """
        Starts a new thread to continuously receive messages from the server.

        Usage:
            start_receive_thread()  # Initiates a thread for receiving messages
        """

        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()

    # loops while the client is running to send commands to server until the client is running
    """ while True: 
        # Get commands from the user, forwarded to the server
        time.sleep(0.1) 
        # command = input("\nInput Command\n> ") 
        command = self.textbox.get('1.0', tk.END).strip()

        print() 
        
        # use a function to forward this to the server along with the command
        forwardToServer(command) """


class MyGUI():

    def __init__(self):
        self.FILE_CLIENT = FileClient(self)

        self.root = tk.Tk()
        self.root.geometry('650x500')
        self.root.title('File Transfer Application')

        self.label = tk.Label(self.root, text="File Transfer Application", font=('Arial', 18))
        self.label.pack(padx=10, pady=10)

        # Text widget for entering commands
        self.textbox = tk.Text(self.root, height=1, font=('Arial', 16), wrap=tk.NONE)
        self.textbox.pack(padx=10, pady=10)

        # Submit when 'enter' is pressed
        self.textbox.bind("<Return>", self.submit_on_enter)

        self.buttonframe = tk.Frame(self.root)
        self.buttonframe.pack(padx=10, pady=10)

        self.buttonframe.columnconfigure(0, weight=1)  # Ensure that column 0 expands with the frame

        # Button for submitting the command to the server
        self.submit_button = tk.Button(self.buttonframe, text="Submit", font=('Arial', 16), command=self.submit_command) 
        self.submit_button.grid(row=0, column=0, padx=5)  # Place the button in the next column

        self.clearbtn = tk.Button(self.buttonframe, text="Clear", font=('Arial', 16), command=self.clear)
        # self.clearbtn.pack(padx=10, pady=10)
        self.clearbtn.grid(row=0, column=1, padx=5)

        # Text area for logs
        self.log_area = tk.Text(self.root, height = 18, state='disabled')
 
        # Create label
        tk.Label(self.root, text = "Log", font=('Arial', 16)).pack()
        
        self.log_area.pack(padx=10, pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def submit_command(self):
    # Get the content of the Text widget
        command = self.textbox.get('1.0', tk.END).strip()

        # Process the entered command
        self.FILE_CLIENT.forwardToServer(command)

        self.textbox.delete('1.0', tk.END)

    def submit_on_enter(self, event):
        # Check if the text box is focused
        if str(self.root.focus_get()) == str(self.textbox):
            self.submit_command()

    def on_closing(self):
        if messagebox.askyesno(title="Quit?", message="Do you really want to quit?"):
            self.root.destroy()
            self.FILE_CLIENT.forwardToServer('/leave')

    def clear(self):
        self.textbox.delete('1.0', tk.END)

    def log(self, log):
        # Allow editing of the text area
        self.log_area.configure(state='normal')
        
        # Insert the provided log text at the end of the log_area
        self.log_area.insert(tk.END, log + '\n\n')
        
        # Disable editing of the text area
        self.log_area.configure(state='disabled')
        
        # Sroll to the end of the text area
        self.log_area.see(tk.END)

    def show_progress_dialog(self, max_value, title):
        # Create a dialog
        self.progress_dialog = tk.Toplevel(self.root)
        self.progress_dialog.title(title)

        # Prevent interaction with other windows while the progress dialog is open
        self.root.grab_set()
        self.progress_dialog.grab_set()
        self.root.attributes('-disabled', True)
        self.progress_dialog.attributes('-disabled', True)

        # Position the progress dialog relative to the root window
        x = self.root.winfo_x() + self.root.winfo_width() // 2 - 100
        y = self.root.winfo_y() + self.root.winfo_height() // 2 - 50
        self.progress_dialog.geometry(f'+{x}+{y}')

        # Place progress dialog on top of main window
        self.progress_dialog.transient(self.root)

        # Display information about the upload including filename and percentage
        upload_info_label = tk.Label(self.progress_dialog, text=f"{title}. Please wait...", font=('Arial', 12))
        upload_info_label.pack(padx=10, pady=5)

        self.percentage_label = tk.Label(self.progress_dialog, text="0%", font=('Arial', 12))
        self.percentage_label.pack(padx=10, pady=5)

        # Create a progress bar with a determinate mode in the dialog
        self.progress_bar = ttk.Progressbar(self.progress_dialog, orient='horizontal', length=200, mode='determinate', maximum=max_value)
        self.progress_bar.pack(padx=10, pady=10)


    def update_progress(self, value):
        # Get the value of progress bar
        self.progress_bar['value'] = value

        # Calculate and update the percentage completed
        percentage = int((value / self.progress_bar['maximum']) * 100)
        self.percentage_label.config(text=f"{percentage}%")

        # Update the dialog
        self.progress_dialog.update()  

    def close_progress_dialog(self):
        # Release the grab on the root and progress_dialog
        self.root.grab_release()
        self.progress_dialog.grab_release()

        # Enable interaction with the root and progress_dialog windows
        self.root.attributes('-disabled', False)
        self.progress_dialog.attributes('-disabled', False)

        # Close the progress_dialog window
        self.progress_dialog.destroy()

GUI = MyGUI()