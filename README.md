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
Open two new terminals and run:

Terminal 1:
```bash
docker exec -it peer1 python client.py --server http://stun-server:5000 --username ali --port 6001 --auto
```

Terminal 2:
```bash
docker exec -it peer2 python client.py --server http://stun-server:5000 --username reza --port 6002 --auto
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

or you can use these commands to register or get the list of peers or one peer

```bash
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "ali", "ip": "192.168.1.101", "port": 7001}'

  curl http://localhost:5000/peers

  curl "http://localhost:5000/peerinfo?username=ali"
```