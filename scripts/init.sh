cat > scripts/init.sh << 'EOF'
#!/bin/bash

echo "Starting P2P Chat System with Docker"
echo "====================================="

if ! command -v docker &> /dev/null; then
    echo "Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed"
    exit 1
fi

echo "Building images..."
docker-compose build

echo "Starting system..."
docker-compose up -d

echo ""
echo "System is running!"
echo ""
echo "Service status:"
echo "---------------"
docker-compose ps
echo ""
echo "Management commands:"
echo "-------------------"
echo "View logs:         docker-compose logs"
echo "Follow logs:       docker-compose logs -f"
echo "Stop system:       docker-compose down"
echo "Stop with volumes: docker-compose down -v"
echo "Access peer:       docker exec -it peer1 sh"
echo "Test server:       curl http://localhost:5000/health"
echo "Get peers:         curl http://localhost:5000/peers"
echo ""
echo "URLs:"
echo "-----"
echo "STUN Server: http://localhost:5000"
echo "Redis:       localhost:6379"
echo ""
echo "Clients:"
echo "--------"
echo "1. peer1 - user1:5001"
echo "2. peer2 - user2:5002"
echo "3. peer3 - user3:5003"
EOF

chmod +x scripts/init.sh