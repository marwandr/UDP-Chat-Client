# Unreliable Chat Client

## Overview
This project implements an unreliable chat client that connects to a server to send and receive messages. The client uses error-checking algorithms such as checksum and sequencing to ensure message integrity. It also supports various protocol commands to manipulate connections, including setting burst values, delay, and bit flips.

## Features
- **Checksum for Error Checking**: Adds and verifies checksums to detect message corruption.
- **Sequencing**: Ensures that messages are received in the correct order.
- **Protocol Commands**: Supports commands for manipulating connections, including setting drop rate, flip rate, burst value, and delay.
- **User Management**: Allows users to log in with a unique username, checks for username availability, and lists online users.

## Requirements
- Python 3.x
- `socket` library (standard library)
- `threading` library (standard library)
- `math` library (standard library)
- `time` library (standard library)
- `re` library (standard library)
- `queue` library (standard library)
- `binascii` library (standard library)

## Usage  
(Currently there is no server file made yet, I will still add this to ensure the client can be ran.)  
1. **Running the Client**:
   - Ensure the server is running and accessible.
   - Run the client script: `python chat_client.py`.

2. **Logging In**:
   - Enter a unique username when prompted.
   - If the username is in use or contains disallowed characters, you will be prompted to enter a different username.

3. **Sending Messages**:
   - To send a message to a user: `@username message`
   - To see who is online: `!who`
   - To reset the server values: `!reset`
   - To get the value of a setting: `!get SETTING_NAME`
   - To set the value of a setting: `!set SETTING_NAME value`

4. **Quitting**:
   - To quit the client: `!quit`

## Error Handling
- **Checksum Errors**: If a message fails checksum verification, an error message is sent back to the sender.
- **Unknown Commands**: If an unknown command is received, an appropriate error message is displayed.

## Commands
- `!quit`: Quit the chat client.
- `!who`: List all online users.
- `!reset`: Reset server settings.
- `!get [SETTING]`: Get the value of a server setting.
- `!set [SETTING] [VALUE]`: Set the value of a server setting. Valid settings include `DROP`, `FLIP`, `BURST`, `DELAY`, `BURST-LEN`, and `DELAY-LEN`.

## Protocol
- **HELLO-FROM username**: Login request.
- **HELLO username**: Login acknowledgment.
- **IN-USE**: Username already in use.
- **BUSY**: Server is full.
- **SEND username message**: Send a message to a user.
- **DELIVERY username message**: Deliver a message to the client.
- **ERROR**: Indicate an error in message delivery.
- **ACK**: Acknowledge receipt of a message.
- **LIST**: Request list of online users.
- **LIST-OK user1,user2,...**: List of online users.
- **SET parameter value**: Set server parameter.
- **SET-OK**: Acknowledge setting change.
- **GET parameter**: Get server parameter value.
- **VALUE parameter value**: Return server parameter value.

## Implementation Details
- **Checksum**: Calculated by dividing the message into 4 parts, summing the binary values, and flipping the bits of the result.
- **Sequencing**: Uses sequence numbers to ensure messages are processed in the correct order.
- **Multithreading**: Uses separate threads for sending and receiving messages to handle concurrency.
- **Error Handling**: Checks for message integrity using checksums and sequence numbers, and handles various protocol errors.

## License
This project is licensed under the Apache 2.0 License.
