# P2P Chat System

## Quick Start

### Install and Setup
First install Docker:
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
```
Restart your system or logout/login after installation.

Clone and run the project:
```bash
git clone <repository-url>
cd networkProject
docker-compose up --build
```

### Run Clients
Open three new terminals and run:

Terminal 1:
```bash
docker exec -it peer1 python client.py --server http://stun-server:5000 --username user1 --port 5001 --auto
```

Terminal 2:
```bash
docker exec -it peer2 python client.py --server http://stun-server:5000 --username user2 --port 5002 --auto
```

Terminal 3:
```bash
docker exec -it peer3 python client.py --server http://stun-server:5000 --username user3 --port 5003 --auto
```

### Start Chatting
In each client:
Press 1 to see peer list.
Press 3 to connect to peer.
Select peer number.
Send messages.
Type exit to quit.

### Stop System
```bash
docker-compose down
```

## Troubleshooting
```bash
docker-compose logs -f
docker-compose restart
docker-compose down -v
docker-compose up --build
```

Note: You need 3 terminals for 3 clients.