import socket
import threading
import math
import time
import re
import queue
import binascii

# An unreliable chat client, which connects to a server and sends messages through
# to other users of the client. It has implemented error checking algorithms such as
# the checksum and sequencing.

# It follows a protocol wherein values for manipulating the connections are also implemented
# Such as setting a burst value, delay or bit flips.

SERVER_ADDRESS = "127.0.0.1"
SERVER_PORT = 5382

running = True
acknowledged = 0
bad_user = False
receiving = {}
messages = {}
before = {}
message_queue = queue.Queue()

def add_checksum(message):
    try:
        message = bin(int(binascii.hexlify(message.encode()),16))
        message = message[2:]
        k = len(message)/4
        k = math.ceil(k)

        c1 = message[0:k]
        c2 = message[k:2*k]
        c3 = message[2*k:3*k]
        c4 = message[3*k:4*k]
        Sum = bin(int(c1, 2)+int(c2, 2)+int(c3, 2)+int(c4, 2))[2:]
        if(len(Sum) > k):
            x = len(Sum)-k
            Sum = bin(int(Sum[0:x], 2)+int(Sum[x:], 2))[2:]
        if(len(Sum) < k):
            Sum = '0'*(k-len(Sum))+Sum

        checksum = ''
        for i in Sum:
            if(i == '1'):
                checksum += '0'
            else:
                checksum += '1'
        checksum = "*"+checksum
        return checksum
    except Exception as e:
        return "error"

def check_checksum(message):
    try:
        regex = re.search(r'^(.*)\*(\d+)\*(\d+)$', message) # get the regex
        message = regex.group(1)
        i = 0
        while i < 2:
            message = message[1:]
            if message[0] == " ":
                i += 1
        message = message[1:]
        message = bin(int(binascii.hexlify(message.encode()),16))
        message = message[2:]
        expectedsum = regex.group(2)
        k = len(message)/4
        k = math.ceil(k)

        c1 = message[0:k]
        c2 = message[k:2*k]
        c3 = message[2*k:3*k]
        c4 = message[3*k:4*k]
        receivedsum = bin(int(c1, 2)+int(c2, 2)+int(c3, 2)+int(c4, 2))[2:]
        if(len(receivedsum) > k):
            x = len(receivedsum)-k
            receivedsum = bin(int(receivedsum[0:x], 2)+int(receivedsum[x:], 2))[2:]
        if(len(receivedsum) < k):
            receivedsum = '0'*(k-len(receivedsum))+receivedsum

        receivedchecksum = ''
        for i in receivedsum:
            if(i == '1'):
                receivedchecksum += '0'
            else:
                receivedchecksum += '1'
        return int(receivedchecksum) == int(expectedsum)
    except Exception as e:
        return False

def getInput(sock):                                 # Function for getting input
    theInput = input()
    if theInput == "!quit":                         # If the input is !quit we're quitting
        global running
        running = False                             # Stop thread
        sock.close()                                # Close socket
        exit()                                      # Exit
    else:
        return theInput

def log_in():
    while True:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print('Welcome to Chat Client. Enter your login:')
        USERNAME = getInput(client)
        mistake = True
        while mistake:
            mistake = False
            m = f"HELLO-FROM {USERNAME}\n"

            disallowedCharacters = "!@#$%^&*"

            if any(disallowedCharacter in USERNAME for disallowedCharacter in disallowedCharacters):
                print(f"Cannot log in as {USERNAME}. That username contains disallowed characters.\n")
                break

            client.sendto(m.encode("utf-8"), (SERVER_ADDRESS, SERVER_PORT))
            data, _ = client.recvfrom(1240)
            try:
                data = data.decode('utf-8')
            except:
                continue
            if "IN-USE\n" in data:
                print(f"Cannot log in as {USERNAME}. That username is already in use.\n")
            elif "BUSY" in data:
                print("Cannot log in. The server is full!\n")
                client.close()
                exit()
            elif f"HELLO {USERNAME}\n" in data:
                print(f"Successfully logged in as {USERNAME}!\n")
                return client
            elif "BAD-RQST-HDR" in data:
                print("Error: Unknown issue in previous message header.\n")
            elif "BAD-DEST-USER" in data:
                print("The destination user does not exist\n")
            elif "SEND-OK" in data:
                print("The message was sent successfully")
            else:
                mistake = True

def sendPackets(client, packet_size):
    while True:
        global acknowledged
        global bad_user
        global message_queue
        message1 = message_queue.get(True)
        message = message1[1:]
        user = message.split()[0]
        message = message[len(user)+1:]
        while True:
            acknowledged = 0
            sequence_number_o = 0                       # outgoing sequence number to check for packets
            packets = (len(message) / packet_size)
            packets = math.ceil(packets)
            packets = int(packets)
            for i in range(packets):
                b = i*packet_size
                e = (i+1)*packet_size
                packet = message[b:e]
                checksum = add_checksum(packet)
                if checksum == "error":
                    continue
                packet = "SEND " + user + " " + packet + checksum + "*" + str(sequence_number_o) + "\n"
                client.sendto(packet.encode("utf-8"), (SERVER_ADDRESS, SERVER_PORT))
                sequence_number_o += 1
                if bad_user == True:
                    break
            time.sleep(1)
            if acknowledged >= (packets):
                break
        bad_user = False

def checkError(data, expected_sequence_number):
    global receiving
    global messages
    user = data.split()[1]
    splitdata = ' '.join(data.split()[:1])
    data = data[len(splitdata)+1:-1] # get rid of DELIVERY and the newline, leaving only the message itself
    regex = re.search(r'^(.*)\*(\d+)\*(\d+)$', data[len(user)+1:]) # get the regex
    if not regex:
        print("oops")
        return 'e'
    sequence_number = regex.group(3) # get the sequence number
    message = regex.group(1) # get the actual message
    try:
        if int(sequence_number) == 0:
            messages.update({user:message})
            receiving[user] += 1
            return int(sequence_number)
        elif int(sequence_number) == int(expected_sequence_number):
            currently = messages[user]
            new = currently+message
            messages.update({user:new})
            receiving[user] += 1
            return int(sequence_number)
    except:
        return 'e'
    else:
        return 'e'

def receive(client):
    global running
    global acknowledged
    global receiving
    global messages
    global bad_user
    while running:
        try:
            data, _ = client.recvfrom(1240)
            try:
                data = data.decode("utf-8")
            except:
                continue
            dataArray = data.split()
            if dataArray[0] == "DELIVERY":      # Message handling
                if dataArray[2] == "ERROR":
                    acknowledged = 0
                elif dataArray[2] == "ACK":
                    try:
                        if len(dataArray) == 3:
                            acknowledged += 1
                        elif acknowledged == int(dataArray[3]):
                            acknowledged += 1
                    except:
                        pass
                else:
                    user = dataArray[1]
                    if check_checksum(data) == False:
                        client.sendto(f"SEND {user} ERROR\n".encode('utf-8'), (SERVER_ADDRESS, SERVER_PORT))
                        pass
                    else:
                        if user not in receiving:
                            receiving[user] = 0
                            messages[user] = ""
                        check = checkError(data, receiving[user])
                        if check == 'e':
                            receiving.pop(user)
                            messages.pop(user)
                        else:
                            client.sendto(f"SEND {user} ACK\n".encode('utf-8'), (SERVER_ADDRESS, SERVER_PORT))
                            print(f"From {user}: {messages[user]}")
                continue
            elif data == "BAD-RQST-HDR\n":
                print("Error: Unknown issue in previous message header.\n")
                continue
            elif data == "BAD-RQST-BODY\n":
                print("Error: Unknown issue in previous message body.\n")
                continue
            elif data == "BAD-DEST-USER\n":
                print("The destination user does not exist\n")
                bad_user = True
                continue
            elif data == "SEND-OK\n":
                try:
                    bad_user = False
                except:
                    pass
                continue
            elif data == "SET-OK\n":
                print("The values have been reset")
                continue
            elif dataArray[0] == "VALUE":
                if len(dataArray) == 3:
                    print(f"The value of {dataArray[1]} is {dataArray[2]}")
                else:
                    print(f"The value of {dataArray[1]} is {dataArray[2]} {dataArray[3]}")
            elif dataArray[0] == "LIST-OK":      # If the server returns LIST-OK it means we have received a list
                allUsers = data.split(" ")[1].split(",")    
                print(f"There are {len(allUsers)} online:\n")
                for i in allUsers:
                    print(f"- {i.strip()}\n")    # Print users
                continue
            else:
                continue
        except:
            continue

def send(client):
    global running
    global acknowledged
    global bad_user
    global message_queue
    s1 = threading.Thread(target=sendPackets, args=(client,1240,))
    s1.start()
    while running:
            message = getInput(client)
            words = message.split()
            if message[0] == "@":
                message_queue.put(message)
            elif words[0] == "!who":
                client.sendto("LIST\n".encode('utf-8'), (SERVER_ADDRESS, SERVER_PORT))
            elif words[0] == "!reset":
                client.sendto("RESET\n".encode('utf-8'), (SERVER_ADDRESS, SERVER_PORT))
            elif words[0] == "!get" and len(words) == 2:
                client.sendto(f"GET {words[1].upper()}\n".encode('utf-8'), (SERVER_ADDRESS, SERVER_PORT))
            elif words[0] == "!set":
                if len(words) < 3:
                    print("Not a valid value")
                elif words[1] == "DROP":
                    if float(words[2]) > 0 and float(words[2]) < 1:
                        client.sendto(f"SET DROP {words[2]}\n".encode('utf-8'), (SERVER_ADDRESS, SERVER_PORT))
                    else:
                        print("Not a valid value")
                elif words[1] == "FLIP":
                    if float(words[2]) > 0 and float(words[2]) < 1:
                        client.sendto(f"SET FLIP {words[2]}\n".encode('utf-8'), (SERVER_ADDRESS, SERVER_PORT))
                    else:
                        print("Not a valid value") 
                elif words[1] == "BURST":    
                    if float(words[2]) > 0 and float(words[2]) < 1:
                        client.sendto(f"SET BURST {words[2]}\n".encode('utf-8'), (SERVER_ADDRESS, SERVER_PORT))
                    else:
                        print("Not a valid value")
                elif words[1] == "DELAY":
                    if float(words[2]) > 0 and float(words[2]) < 1:
                        client.sendto(f"SET DELAY {words[2]}\n".encode('utf-8'), (SERVER_ADDRESS, SERVER_PORT))
                    else:
                        print("Not a valid value")
                elif words[1] == "BURST-LEN":
                    if len(words) >= 4:
                        client.sendto(f"SET BURST-LEN {words[2]} {words[3]}\n".encode('utf-8'), (SERVER_ADDRESS, SERVER_PORT))
                    else:
                        print("Not a valid value")
                elif words[1] == "DELAY-LEN":
                    if len(words) >= 4:
                        client.sendto(f"SET DELAY-LEN {words[2]} {words[3]}\n".encode('utf-8'), (SERVER_ADDRESS, SERVER_PORT))
                    else:
                        print("Not a valid value")
def main():
    s = log_in()
    t = threading.Thread(target=receive, args=(s,))
    t.start()
    send(s)
    
if __name__ == "__main__":
    main()
