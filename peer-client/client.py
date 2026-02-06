import requests
import json
import socket
import sys
import os
import time
import threading
import select
from datetime import datetime

class TCPManager:
    def __init__(self, client_instance):
        self.client = client_instance
        self.tcp_server = None
        self.active_connections = {}
        self.running = True
        self.server_thread = None
        
    def start_tcp_server(self, port):
        try:
            self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_server.bind(('0.0.0.0', port))
            self.tcp_server.listen(5)
            self.tcp_server.settimeout(1.0)
            
            print(f"TCP Server started on port {port}")
            
            self.server_thread = threading.Thread(target=self._accept_connections)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Failed to start TCP server: {e}")
            return False
    
    def _accept_connections(self):
        while self.running:
            try:
                readable, _, _ = select.select([self.tcp_server], [], [], 1.0)
                if self.tcp_server in readable:
                    client_socket, client_address = self.tcp_server.accept()
                    
                    try:
                        username_data = client_socket.recv(1024).decode('utf-8').strip()
                        if username_data.startswith("USER:"):
                            username = username_data.split(":")[1]
                            
                            self.active_connections[username] = {
                                'socket': client_socket,
                                'address': client_address,
                                'connected_at': datetime.now()
                            }
                            
                            print(f"Connected to {username} from {client_address}")
                            
                            thread = threading.Thread(
                                target=self._receive_messages,
                                args=(client_socket, username)
                            )
                            thread.daemon = True
                            thread.start()
                            
                    except Exception as e:
                        print(f"Error accepting connection: {e}")
                        client_socket.close()
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}")
    def _receive_messages(self, sock, username):
        try:
            sock.settimeout(1.0)  # 1 second timeout
            while self.running:
                try:
                    data = sock.recv(4096)
                    if not data:
                        print(f"\n{username} closed connection")
                        break
                        
                    message = data.decode('utf-8')
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"\n[{timestamp}] {username}: {message}")
                    print("Your message: ", end="", flush=True)
                    
                except socket.timeout:
                    continue  # Timeout is normal, just continue
                except ConnectionResetError:
                    print(f"\n{username} reset connection")
                    break
                except Exception as e:
                    print(f"\nError receiving from {username}: {e}")
                    break
                    
        except Exception as e:
            print(f"Thread error: {e}")
        finally:
            try:
                sock.close()
            except:
                pass
            if username in self.active_connections:
                del self.active_connections[username]
            print(f"\n{username} disconnected")
            
    def connect_to_peer(self, ip, port, my_username):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((ip, port))
            
            # Enable keepalive
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            sock.send(f"USER:{my_username}".encode('utf-8'))
            
            self.active_connections[ip] = {
                'socket': sock,
                'address': (ip, port),
                'connected_at': datetime.now()
            }
            
            print(f"Connected to {ip}:{port}")
            
            thread = threading.Thread(
                target=self._receive_messages,
                args=(sock, f"{ip}:{port}")
            )
            thread.daemon = True
            thread.start()
            
            return sock
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return None
    
    def send_message(self, sock, message):
        try:
            sock.send(message.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Send failed: {e}")
            return False
    
    def stop(self):
        self.running = False
        if self.tcp_server:
            self.tcp_server.close()
        for conn in self.active_connections.values():
            conn['socket'].close()
        self.active_connections.clear()

class P2PClient:
    def __init__(self, server_url=None):
        self.stun_server = server_url or os.getenv('STUN_SERVER', 'http://stun-server:5000')
        self.username = None
        self.ip = None
        self.port = None
        self.running = True
        self.tcp_manager = None
        
        print("=" * 60)
        print("P2P Chat Client")
        print("=" * 60)
    
    def get_container_ip(self):
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except:
            return "172.20.0.x"
    
    def register(self, username, port):
        try:
            self.username = username
            self.port = port
            self.ip = self.get_container_ip()
            
            print(f"Registering with:")
            print(f"  Username: {username}")
            print(f"  IP: {self.ip}")
            print(f"  Port: {port}")
            
            data = {
                "username": username,
                "ip": self.ip,
                "port": port
            }
            
            response = requests.post(
                f"{self.stun_server}/register",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"Success: {result['message']}")
                
                self.tcp_manager = TCPManager(self)
                if self.tcp_manager.start_tcp_server(port):
                    print(f"TCP server ready on port {port}")
                else:
                    print("Warning: TCP server failed to start")
                
                return True
            else:
                error = response.json().get('message', 'Unknown error')
                print(f"Error: {error}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"Cannot connect to server: {self.stun_server}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def get_peers(self):
        try:
            response = requests.get(
                f"{self.stun_server}/peers",
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                peers = result.get('peers', [])
                
                peers = [p for p in peers if p['username'] != self.username]
                
                if peers:
                    print(f"\nOnline peers ({len(peers)}):")
                    print("-" * 50)
                    for i, peer in enumerate(peers, 1):
                        status = peer.get('status', 'unknown')
                        print(f"{i}. {peer['username']} - {peer['ip']}:{peer['port']} ({status})")
                    print("-" * 50)
                else:
                    print("\nNo online peers")
                
                return peers
            else:
                print("Error getting peers list")
                return []
                
        except requests.exceptions.ConnectionError:
            print("Cannot connect to server")
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_peer_info(self, username):
        try:
            params = {'username': username}
            response = requests.get(
                f"{self.stun_server}/peerinfo",
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('peer')
            else:
                print(f"User '{username}' not found")
                return None
                
        except requests.exceptions.ConnectionError:
            print("Cannot connect to server")
            return None
    
    def connect_to_peer_direct(self):
        if not self.tcp_manager:
            print("TCP manager not initialized")
            return
        
        peers = self.get_peers()
        if not peers:
            return
        
        try:
            choice = input("Select peer number to connect: ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(peers):
                peer = peers[idx]
                print(f"Connecting to {peer['username']} at {peer['ip']}:{peer['port']}...")
                
                sock = self.tcp_manager.connect_to_peer(
                    peer['ip'], 
                    peer['port'], 
                    self.username
                )
                
                if sock:
                    self.chat_with_peer(sock, peer['username'])
                else:
                    print("Connection failed")
            else:
                print("Invalid selection")
                
        except ValueError:
            print("Please enter a number")
        except Exception as e:
            print(f"Error: {e}")
    
    def chat_with_peer(self, sock, peer_username):
        print(f"\n--- Chat with {peer_username} ---")
        print("Type 'exit' to end chat")
        print("-" * 30)
        
        try:
            while self.running:
                try:
                    message = input("Your message: ").strip()
                    
                    if message.lower() == 'exit':
                        print("Ending chat...")
                        break
                    
                    if message:
                        sock.send(message.encode('utf-8'))
                        print(f"You: {message}")
                        
                except (BrokenPipeError, ConnectionResetError):
                    print("Connection lost!")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    break
                    
        except KeyboardInterrupt:
            print("\nChat interrupted")
        except Exception as e:
            print(f"Chat error: {e}")
    
    def test_server(self):
        try:
            response = requests.get(f"{self.stun_server}/health", timeout=5)
            if response.status_code == 200:
                print("STUN server is available")
                return True
            else:
                print("STUN server not responding")
                return False
        except:
            print(f"Cannot connect to server: {self.stun_server}")
            return False
    
    def unregister(self):
        try:
            if not self.username:
                print("You are not registered")
                return False
            
            data = {"username": self.username}
            response = requests.post(
                f"{self.stun_server}/unregister",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                print("Successfully unregistered")
                
                if self.tcp_manager:
                    self.tcp_manager.stop()
                
                self.username = None
                return True
            else:
                error = response.json().get('message', 'Unknown error')
                print(f"Error: {error}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("Cannot connect to server")
            return False
    
    def auto_register(self, username, port):
        print(f"Auto-registering as '{username}'...")
        
        max_retries = 10
        for i in range(max_retries):
            if self.test_server():
                if self.register(username, port):
                    return True
            else:
                print(f"Attempt {i+1}/{max_retries} - waiting for server...")
                time.sleep(2)
        
        print("Auto-registration failed")
        return False
    
    def interactive_mode(self):
        while self.running:
            print("\n" + "=" * 50)
            print("Main Menu:")
            print("1. Get peers list")
            print("2. Get peer info")
            print("3. Connect to peer (P2P Chat)")
            print("4. Test server connection")
            print("5. Unregister")
            print("0. Exit")
            print("=" * 50)
            
            try:
                choice = input("Your choice: ").strip()
                
                if choice == "1":
                    if not self.username:
                        print("Please register first")
                        continue
                    self.get_peers()
                    
                elif choice == "2":
                    if not self.username:
                        print("Please register first")
                        continue
                    target = input("Username: ").strip()
                    if target:
                        info = self.get_peer_info(target)
                        if info:
                            print(f"\nInfo for {target}:")
                            for k, v in info.items():
                                print(f"  {k}: {v}")
                
                elif choice == "3":
                    if not self.username:
                        print("Please register first")
                        continue
                    self.connect_to_peer_direct()
                    
                elif choice == "4":
                    self.test_server()
                    
                elif choice == "5":
                    self.unregister()
                    
                elif choice == "0":
                    print("\nGoodbye!")
                    self.running = False
                    break
                    
                else:
                    print("Invalid choice")
                    
            except KeyboardInterrupt:
                print("\nSIGINT received - exiting...")
                self.running = False
                break
            except EOFError:
                print("\nEOF received - exiting...")
                self.running = False
                break

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='P2P Chat Client')
    parser.add_argument('--server', default=None, help='STUN server address')
    parser.add_argument('--username', help='Username for auto-registration')
    parser.add_argument('--port', type=int, default=5001, help='Port number')
    parser.add_argument('--auto', action='store_true', help='Auto mode')
    
    args = parser.parse_args()
    
    client = P2PClient(args.server)
    
    if args.auto and args.username:
        if client.auto_register(args.username, args.port):
            client.interactive_mode()
        else:
            print("Auto mode failed")
            sys.exit(1)
    else:
        client.interactive_mode()
    
    if client.username:
        client.unregister()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped")
        sys.exit(0)