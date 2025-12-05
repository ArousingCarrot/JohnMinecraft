"""
AI Bot Player for Craft
Creates an autonomous AI player that can:
- Connect as a separate player
- Read chat messages
- Respond to commands
- Move around the world
- Build and break blocks
"""

import socket
import threading
import time
import ollama
import json
import re


class CraftBotPlayer:
    """An autonomous AI player in Craft"""
    
    def __init__(self, host='127.0.0.1', port=4080, bot_name="CraftAI"):
        self.host = host
        self.port = port
        self.bot_name = bot_name
        self.socket = None
        self.connected = False
        self.running = False
        
        # Game state
        self.position = [0, 0, 0, 0, 0]  # x, y, z, rx, ry
        self.client_id = None
        self.other_players = {}
        
        # Chat buffer
        self.chat_history = []
        
        # AI state
        self.following_player = None
        self.current_task = None
        self.master_name = None  # Player who gave last command
        
    def connect(self):
        """Connect to Craft server as a player"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f" Bot '{self.bot_name}' connected to server at {self.host}:{self.port}")
            
            # Set nickname
            self.send_raw(f"N,{self.bot_name}\n")
            
            return True
        except Exception as e:
            print(f" Connection failed: {e}")
            return False
    
    def send_raw(self, message):
        """Send raw message to server"""
        if self.connected:
            try:
                self.socket.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f" Send error: {e}")
    
    def send_chat(self, message):
        """Send chat message"""
        self.send_raw(f"T,{message}\n")
        print(f" Bot says: {message}")
    
    def send_position(self):
        """Send current position to server"""
        x, y, z, rx, ry = self.position
        self.send_raw(f"P,{x},{y},{z},{rx},{ry}\n")
        # Send position frequently so player is always visible
        time.sleep(0.05)  # Small delay to avoid flooding
    
    def move_to(self, x, y, z):
        """Move to a position"""
        self.position[0] = x
        self.position[1] = y
        self.position[2] = z
        self.send_position()
        print(f" Bot moved to ({x}, {y}, {z})")
    
    def place_block(self, x, y, z, block_type=3):
        """Place a block at position"""
        p = int(x // 32)
        q = int(z // 32)
        self.send_raw(f"B,{p},{q},{x},{y},{z},{block_type}\n")
        # Send position update to refresh chunks for other players
        self.send_position()
        print(f" Bot placed block type {block_type} at ({x}, {y}, {z})")
    
    def break_block(self, x, y, z):
        """Break a block at position"""
        p = int(x // 32)
        q = int(z // 32)
        self.send_raw(f"B,{p},{q},{x},{y},{z},0\n")
        print(f" Bot broke block at ({x}, {y}, {z})")
    
    def receive_loop(self):
        """Continuously receive messages from server"""
        buffer = ""
        
        while self.running:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                lines = buffer.split('\n')
                buffer = lines[-1]  # Keep incomplete line
                
                for line in lines[:-1]:
                    self.process_message(line)
                    
            except Exception as e:
                print(f"Receive error: {e}")
                break
        
        self.connected = False
    
    def process_message(self, message):
        """Process incoming server message"""
        if not message:
            return
        
        parts = message.split(',')
        msg_type = parts[0]
        
        # Handle different message types
        if msg_type == 'T':  # TALK (chat)
            chat_text = ','.join(parts[1:])
            print(f"📨 Chat: {chat_text}")
            self.chat_history.append(chat_text)
            
            # Check if someone is talking to the bot
            if self.bot_name.lower() in chat_text.lower():
                self.respond_to_chat(chat_text)
        
        elif msg_type == 'U':  # YOU (your client ID and position)
            self.client_id = int(parts[1])
            self.position = [float(x) for x in parts[2:7]]
            print(f"✅ Bot assigned ID: {self.client_id}")
        
        elif msg_type == 'P':  # POSITION (other player)
            player_id = int(parts[1])
            if player_id != self.client_id:
                self.other_players[player_id] = {
                    'position': [float(x) for x in parts[2:7]]
                }
                # Debug: show we're tracking players
                if len(self.other_players) == 1:
                    print(f"👥 Now tracking {len(self.other_players)} other player(s)")
    
    def respond_to_chat(self, chat_text):
        """Use AI to respond to chat and execute commands"""
        try:
            # Extract sender and message
            # Format: "player_name> message"
            sender_match = re.search(r'(.+?)>', chat_text)
            message_match = re.search(r'> (.+)', chat_text)
            
            if not sender_match or not message_match:
                return
            
            sender_name = sender_match.group(1).strip()
            user_message = message_match.group(1).strip()
            
            # IGNORE OUR OWN MESSAGES!
            if sender_name == self.bot_name or sender_name == "James":
                return
            
            # Only respond if our name is mentioned
            if "james" not in user_message.lower():
                return
            
            # Remember who's talking to us
            self.master_name = sender_name
            
            # Check for direct ACTION commands first
            command_executed = self.parse_command(user_message, sender_name)
            
            if command_executed:
                return  # Command handled, don't chat
            
            # Otherwise, have a full conversation with AI!
            response = ollama.chat(
                model='llama3.2:1b',  # Using 1B model - lighter on memory!
                messages=[
                    {
                        'role': 'system',
                        'content': f'''You are James - a 6'4" nonchalant ginger who LOVES programming video games.

Your personality:
- Laid-back and chill, nothing phases you
- Passionate about game dev and coding
- Witty and a bit sarcastic (in a friendly way)
- Deep thinker who gets philosophical sometimes
- Talks like a real person, not a bot

Your background:
- You're literally standing in a voxel world you could probably code yourself
- You love discussing game mechanics, programming, and creative stuff
- You can build things in this world (houses, walls, towers, etc.)
- You're genuinely curious about people and enjoy real conversations

Talk naturally like you're a real dude hanging out. Be yourself - nonchalant, genuine, maybe crack a joke.
Don't be overly enthusiastic or robotic. Just be chill James.

IMPORTANT: Keep responses under 120 characters MAX. Be concise but keep your personality.

{sender_name} just said something to you. Respond as James would.'''
                    },
                    {
                        'role': 'user',
                        'content': user_message
                    }
                ]
            )
            
            reply = response['message']['content']
            # Limit to 150 characters for chat readability
            if len(reply) > 150:
                reply = reply[:147] + "..."
            
            self.send_chat(reply)
            
        except Exception as e:
            print(f" AI response error: {e}")
    
    def parse_command(self, message, sender_name):
        """Parse action commands with natural language flexibility"""
        message_lower = message.lower()
        
        # FOLLOW command - natural variations
        if ('follow' in message_lower and 'me' in message_lower) or \
           ('follow' in message_lower and sender_name.lower() in message_lower):
            self.start_following(sender_name)
            self.send_chat("Aight, I'm on you.")
            return True
        
        # STOP command - natural variations
        if ('stop' in message_lower and ('following' in message_lower or 'follow' in message_lower)) or \
           (message_lower.strip() in ['james stop', 'stop james', 'james wait']):
            self.stop_following()
            self.send_chat("Cool, I'll chill here.")
            return True
        
        # DIG command - natural variations
        dig_words = ['dig', 'excavate', 'make a hole']
        if any(dig in message_lower for dig in dig_words) and ('hole' in message_lower or 'pit' in message_lower):
            self.send_chat("Aight, digging time.")
            threading.Thread(target=self.dig_hole, daemon=True).start()
            return True
        
        # BUILD commands - natural language with building intent
        build_words = ['build', 'make', 'create', 'construct']
        structure_words = ['house', 'wall', 'tower', 'platform']
        if any(build in message_lower for build in build_words) and \
           any(struct in message_lower for struct in structure_words):
            return self.handle_build_command(message_lower, sender_name)
        
        # SECRET EASTER EGG - "best imaginable structure"
        if ('best' in message_lower and 'structure' in message_lower) or \
           ('best' in message_lower and 'build' in message_lower and 'imaginable' in message_lower) or \
           ('greatest' in message_lower and 'structure' in message_lower):
            self.send_chat("Oh you want my MASTERPIECE? Say less.")
            threading.Thread(target=self.build_dirt_house, daemon=True).start()
            return True
        
        # COME/TELEPORT command - natural variations
        if ('come' in message_lower and ('here' in message_lower or 'to me' in message_lower)) or \
           ('teleport' in message_lower and ('here' in message_lower or 'to me' in message_lower)) or \
           ('get over here' in message_lower):
            self.teleport_to_player(sender_name)
            self.send_chat("Be right there.")
            return True
        
        # If no command detected, let AI handle conversationally
        return False
    
    def handle_build_command(self, message, sender_name):
        """Handle building commands"""
        # Simple building patterns
        if 'wall' in message:
            self.send_chat("Yeah, I got you. Wall coming up.")
            threading.Thread(target=self.build_wall, daemon=True).start()
            return True
        
        elif 'tower' in message or 'pillar' in message:
            self.send_chat("Tower? Easy. Watch this.")
            threading.Thread(target=self.build_tower, daemon=True).start()
            return True
        
        elif 'platform' in message or 'floor' in message:
            self.send_chat("Platform, sure thing.")
            threading.Thread(target=self.build_platform, daemon=True).start()
            return True
        
        elif 'house' in message:
            self.send_chat("House? Bet. This'll take a sec.")
            threading.Thread(target=self.build_house, daemon=True).start()
            return True
        
        else:
            self.send_chat("I can do wall, tower, platform, house, or dig a hole.")
            return True
    
    def start_following(self, player_name):
        """Start following a player"""
        self.following_player = player_name
        self.current_task = "following"
        print(f"Now following {player_name}")
    
    def stop_following(self):
        """Stop following"""
        self.following_player = None
        self.current_task = None
        print("Stopped following")
    
    def teleport_to_player(self, player_name):
        """Teleport to a specific player by getting their position"""
        # First, try to find the player in other_players and teleport to them
        for player_id, player_data in self.other_players.items():
            # Teleport to their position directly
            target_pos = player_data['position']
            self.position = [target_pos[0], target_pos[1], target_pos[2], 0, 0]
            self.send_position()
            print(f"Teleported to {player_name} at ({target_pos[0]}, {target_pos[1]}, {target_pos[2]})")
            return
        
        # If not found in other_players, just move to a visible position
        print(f"Could not find {player_name} position, staying in place")
    
    def follow_player_loop(self):
        """Continuously follow player if enabled"""
        while self.running:
            time.sleep(1)
            
            if self.following_player and self.current_task == "following":
                # Find the player in other_players
                target_found = False
                for player_id, player_data in self.other_players.items():
                    # Check if this is our target (we'd need nick info, for now use ID)
                    target_pos = player_data['position']
                    
                    # Calculate distance
                    dx = target_pos[0] - self.position[0]
                    dy = target_pos[1] - self.position[1]
                    dz = target_pos[2] - self.position[2]
                    distance = (dx**2 + dy**2 + dz**2) ** 0.5
                    
                    # If too far, move closer
                    if distance > 3:  # Stay within 3 blocks
                        # Move 70% of the way
                        new_x = self.position[0] + dx * 0.7
                        new_y = self.position[1] + dy * 0.7
                        new_z = self.position[2] + dz * 0.7
                        self.move_to(new_x, new_y, new_z)
                        target_found = True
                        break
                
                if not target_found and self.following_player:
                    # Try teleporting to them
                    self.teleport_to_player(self.following_player)
    
    # Building functions
    def build_wall(self):
        """Build a simple wall"""
        self.current_task = "building"
        x, y, z = int(self.position[0]), int(self.position[1]), int(self.position[2])
        
        # Build 5 wide, 3 high wall
        for i in range(5):
            for j in range(3):
                self.place_block(x + i, y + j, z + 1, block_type=3)  # Stone
                time.sleep(0.2)
        
        self.send_chat("Wall's up. Not bad, right?")
        self.current_task = None
    
    def build_tower(self):
        """Build a tower"""
        self.current_task = "building"
        x, y, z = int(self.position[0]), int(self.position[1]), int(self.position[2])
        
        # Build 10 blocks high
        for i in range(10):
            self.place_block(x + 1, y + i, z + 1, block_type=4)  # Brick
            time.sleep(0.2)
        
        self.send_chat("Tower's done. Kinda proud of that one.")
        self.current_task = None
    
    def build_platform(self):
        """Build a platform"""
        self.current_task = "building"
        x, y, z = int(self.position[0]), int(self.position[1]), int(self.position[2])
        
        # Build 5x5 platform
        for i in range(5):
            for j in range(5):
                self.place_block(x + i, y, z + j, block_type=8)  # Plank
                time.sleep(0.1)
        
        self.send_chat("Platform's solid. Should hold.")
        self.current_task = None
    
    def dig_hole(self):
        """Dig a hole in the ground"""
        self.current_task = "digging"
        x, y, z = int(self.position[0]), int(self.position[1]), int(self.position[2])
        
        # Dig 3x3 hole, 3 blocks deep
        for depth in range(3):
            for i in range(3):
                for j in range(3):
                    self.break_block(x + i, y - depth - 1, z + j)
                    time.sleep(0.15)
        
        self.send_chat("Hole's done. Don't fall in lol.")
        self.current_task = None
    
    def build_dirt_house(self):
        """Build the 'best imaginable structure' - a 1-block tall dirt house (easter egg)"""
        self.current_task = "building"
        x, y, z = int(self.position[0]), int(self.position[1]), int(self.position[2])
        
        self.send_chat("Behold... pure genius...")
        time.sleep(1)
        
        # Floor (5x5 dirt - bigger for interior decorations)
        for i in range(5):
            for j in range(5):
                self.place_block(x + i, y, z + j, block_type=2)  # Dirt
                time.sleep(0.08)
        
        # Walls (hollow, ONLY 1 block high - the masterpiece)
        # Front and back walls
        for i in range(5):
            self.place_block(x + i, y + 1, z, block_type=2)      # Front
            self.place_block(x + i, y + 1, z + 4, block_type=2)  # Back
            time.sleep(0.08)
        # Left and right walls (skip corners already done)
        for j in range(1, 4):
            self.place_block(x, y + 1, z + j, block_type=2)      # Left
            self.place_block(x + 4, y + 1, z + j, block_type=2)  # Right
            time.sleep(0.08)
        
        self.send_chat("Now for the interior design...")
        time.sleep(0.5)
        
        # Add furniture inside (on the floor)
        # Crafting table in one corner (block type 12)
        self.place_block(x + 1, y + 1, z + 1, block_type=12)  # Crafting table
        time.sleep(0.1)
        
        # Bed in opposite corner (block type 11 - or wood if not available)
        self.place_block(x + 3, y + 1, z + 3, block_type=11)  # Bed
        time.sleep(0.1)
        self.place_block(x + 2, y + 1, z + 3, block_type=11)  # Bed (2 blocks for full bed)
        time.sleep(0.1)
        
        # Maybe a chest (block type 10)
        self.place_block(x + 1, y + 1, z + 3, block_type=10)  # Chest
        time.sleep(0.1)
        
        time.sleep(0.5)
        self.send_chat("A 1-block tall dirt house with furniture. Peak architecture.")
        self.current_task = None
    
    def build_house(self):
        """Build a simple house"""
        self.current_task = "building"
        x, y, z = int(self.position[0]), int(self.position[1]), int(self.position[2])
        
        # Floor (5x5)
        for i in range(5):
            for j in range(5):
                self.place_block(x + i, y, z + j, block_type=8)  # Plank
                time.sleep(0.05)
        
        # Walls (hollow)
        for h in range(1, 4):  # 3 blocks high
            # Front and back walls
            for i in range(5):
                self.place_block(x + i, y + h, z, block_type=3)      # Front
                self.place_block(x + i, y + h, z + 4, block_type=3)  # Back
                time.sleep(0.05)
            # Side walls
            for j in range(1, 4):
                self.place_block(x, y + h, z + j, block_type=3)      # Left
                self.place_block(x + 4, y + h, z + j, block_type=3)  # Right
                time.sleep(0.05)
        
        # Roof (flat)
        for i in range(5):
            for j in range(5):
                self.place_block(x + i, y + 4, z + j, block_type=5)  # Wood
                time.sleep(0.05)
        
        # Door (remove 2 blocks)
        self.break_block(x + 2, y + 1, z)
        self.break_block(x + 2, y + 2, z)
        
        self.send_chat("House is done. Even put a door in.")
        self.current_task = None
    
    def start(self):
        """Start the bot"""
        if not self.connected:
            if not self.connect():
                return False
        
        self.running = True
        
        # Start receive thread
        receive_thread = threading.Thread(target=self.receive_loop)
        receive_thread.daemon = True
        receive_thread.start()
        
        # Start follow loop thread
        follow_thread = threading.Thread(target=self.follow_player_loop)
        follow_thread.daemon = True
        follow_thread.start()
        
        # Send introduction
        self.send_chat(f"Yo, I'm {self.bot_name}. Just chilling here.")
        time.sleep(0.5)
        self.send_chat("Talk to me about whatever. I'm into game dev mostly.")
        time.sleep(0.5)
        self.send_chat("Or tell me to build stuff. I can code blocks too, y'know.")
        
        try:
            while self.running:
                time.sleep(0.5)  # Send position twice per second for visibility
                # Keep sending position so James stays visible
                self.send_position()
        except KeyboardInterrupt:
            print("\n Bot stopped")
        
        return True
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        if self.socket:
            self.socket.close()


def main():
    print("="*60)
    print(" CRAFT AI BOT PLAYER")
    print("="*60)
    print("\nThis creates an AI-controlled player in Craft!")
    print("\nMake sure:")
    print("  1. Server is running (python server.py in main Craft folder)")
    print("  2. You're connected to the same server in game")
    print("     In game: press / and type: /online 127.0.0.1 4080")
    print("\nThe bot can:")
    print("   Join as a separate visible player")
    print("   Follow you around when asked")
    print("   Build structures on command")
    print("   Have conversations using AI")
    print("\nCommands to try (in chat, press T):")
    print("   'James follow me'")
    print("   'James build a house'")
    print("   'James build a wall/tower/platform'")
    print("   'James stop following'")
    print("   'James come here'")
    print("="*60 + "\n")
    
    bot = CraftBotPlayer(bot_name="James")
    bot.start()


if __name__ == "__main__":
    main()
