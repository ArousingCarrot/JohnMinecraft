"""
Craft Server - Python 3 Compatible
Minimal implementation for James to work properly
"""

import socket
import threading
import time
from datetime import datetime

HOST = '0.0.0.0'
PORT = 4080

# Protocol constants
AUTHENTICATE = 'A'
BLOCK = 'B'
CHUNK = 'C'
DISCONNECT = 'D'
KEY = 'K'
LIGHT = 'L'
NICK = 'N'
POSITION = 'P'
REDRAW = 'R'
SIGN = 'S'
TALK = 'T'
TIME = 'E'
VERSION = 'V'
YOU = 'U'

SPAWN_POINT = (0, 0, 0, 0, 0)


class Client:
    """Represents a connected client"""
    
    def __init__(self, conn, addr, client_id):
        self.conn = conn
        self.addr = addr
        self.client_id = client_id
        self.nick = f"guest{client_id}"
        self.position = list(SPAWN_POINT)
        self.running = True
        
    def send(self, *args):
        """Send message to client"""
        try:
            message = ','.join(map(str, args)) + '\n'
            self.conn.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"❌ Send error to client {self.client_id}: {e}")
    
    def receive_line(self):
        """Receive one line from client"""
        buffer = b''
        while self.running:
            try:
                chunk = self.conn.recv(1)
                if not chunk:
                    return None
                if chunk == b'\n':
                    return buffer.decode('utf-8')
                buffer += chunk
            except:
                return None
        return None


class CraftServer:
    """Craft game server"""
    
    def __init__(self):
        self.clients = []
        self.client_id_counter = 1
        self.running = False
        self.blocks = {}  # Store placed blocks
        
    def start(self):
        """Start the server"""
        self.running = True
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(5)
        
        print("="*60)
        print("CRAFT SERVER (Python 3)")
        print("="*60)
        print(f"Listening on {HOST}:{PORT}")
        print("Ready for connections!")
        print("="*60 + "\n")
        
        try:
            while self.running:
                conn, addr = server.accept()
                client = Client(conn, addr, self.client_id_counter)
                self.client_id_counter += 1
                self.clients.append(client)
                
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client,)
                )
                thread.daemon = True
                thread.start()
                
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
        finally:
            server.close()
    
    def handle_client(self, client):
        """Handle individual client connection"""
        print(f"Client {client.client_id} ({client.addr}) connected")
        
        # Send initial messages
        client.send(YOU, client.client_id, *client.position)
        client.send(TIME, int(time.time()), 600)
        client.send(TALK, f"Welcome to Craft!")
        
        # Announce to others
        self.broadcast(TALK, f"{client.nick} joined the game", exclude=client)
        
        # Send other players' positions
        for other in self.clients:
            if other != client:
                client.send(POSITION, other.client_id, *other.position)
        
        # Handle messages
        try:
            while client.running:
                line = client.receive_line()
                if not line:
                    break
                
                self.process_message(client, line)
                
        except Exception as e:
            print(f"Error with client {client.client_id}: {e}")
        finally:
            self.disconnect_client(client)
    
    def process_message(self, client, message):
        """Process a message from client"""
        if not message:
            return
        
        parts = message.split(',')
        msg_type = parts[0]
        
        try:
            if msg_type == NICK:  # Nickname
                if len(parts) > 1:
                    old_nick = client.nick
                    client.nick = parts[1]
                    print(f"Client {client.client_id}: {old_nick} -> {client.nick}")
                    self.broadcast(TALK, f"{old_nick} is now known as {client.nick}")
            
            elif msg_type == POSITION:  # Position update
                if len(parts) >= 6:
                    client.position = [float(x) for x in parts[1:6]]
                    # Broadcast to other clients
                    self.broadcast(POSITION, client.client_id, *client.position, exclude=client)
            
            elif msg_type == TALK:  # Chat message
                if len(parts) > 1:
                    text = ','.join(parts[1:])
                    
                    # Check if it's a command
                    if text.startswith('/'):
                        self.handle_command(client, text)
                    else:
                        # Broadcast chat
                        chat_msg = f"{client.nick}> {text}"
                        print(f"{chat_msg}")
                        self.broadcast(TALK, chat_msg)
            
            elif msg_type == BLOCK:  # Block placement/breaking
                if len(parts) >= 7:
                    p, q, x, y, z, w = parts[1:7]
                    block_key = (int(x), int(y), int(z))
                    
                    if int(w) == 0:
                        # Break block
                        if block_key in self.blocks:
                            del self.blocks[block_key]
                        print(f"{client.nick} broke block at {block_key}")
                    else:
                        # Place block
                        self.blocks[block_key] = int(w)
                        print(f"{client.nick} placed block type {w} at {block_key}")
                    
                    # Broadcast to all clients
                    self.broadcast(BLOCK, *parts[1:7])
        
        except Exception as e:
            print(f"Error processing message from {client.client_id}: {e}")
    
    def handle_command(self, client, command):
        """Handle slash commands"""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == '/list':
            players = ', '.join(c.nick for c in self.clients)
            client.send(TALK, f"Players: {players}")
        
        elif cmd == '/goto' and len(parts) > 1:
            target_nick = parts[1]
            for other in self.clients:
                if other.nick == target_nick:
                    client.position = list(other.position)
                    client.send(POSITION, client.client_id, *client.position)
                    client.send(TALK, f"Teleported to {target_nick}")
                    return
            client.send(TALK, f"Player '{target_nick}' not found")
        
        elif cmd == '/spawn':
            client.position = list(SPAWN_POINT)
            client.send(POSITION, client.client_id, *client.position)
            client.send(TALK, "Teleported to spawn")
        
        else:
            client.send(TALK, f"Unknown command: {cmd}")
    
    def broadcast(self, msg_type, *args, exclude=None):
        """Broadcast message to all clients"""
        for client in self.clients:
            if client != exclude:
                client.send(msg_type, *args)
    
    def disconnect_client(self, client):
        """Handle client disconnect"""
        if client in self.clients:
            self.clients.remove(client)
        client.conn.close()
        print(f"Client {client.client_id} ({client.nick}) disconnected")
        self.broadcast(TALK, f"{client.nick} left the game")


def main():
    server = CraftServer()
    server.start()


if __name__ == "__main__":
    main()
