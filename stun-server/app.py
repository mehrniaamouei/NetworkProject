#Mehrnia Amouei 40213020
#Please read the README file
from flask import Flask, request, jsonify
import redis
import json
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

PEERS_KEY = 'p2p:peers'

def get_redis():
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=3
        )
        r.ping()
        logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return r
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        return None

@app.route('/register', methods=['POST'])
def register_peer():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        required_fields = ['username', 'ip', 'port']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Field '{field}' is required"
                }), 400
        
        username = data['username']
        ip = data['ip']
        port = data['port']
        
        r = get_redis()
        if not r:
            return jsonify({
                "status": "error",
                "message": "Database connection error"
            }), 500
        
        peer_info = {
            "username": username,
            "ip": ip,
            "port": int(port),
            "last_seen": datetime.now().isoformat(),
            "status": "online"
        }
        
        r.hset(PEERS_KEY, username, json.dumps(peer_info))
        r.expire(PEERS_KEY, 3600)
        
        logger.info(f"User '{username}' registered: {ip}:{port}")
        
        return jsonify({
            "status": "success",
            "message": "Registration successful",
            "peer": peer_info
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route('/peers', methods=['GET'])
def get_peers():
    try:
        r = get_redis()
        if not r:
            return jsonify({
                "status": "error",
                "message": "Database connection error"
            }), 500
        
        all_peers = r.hgetall(PEERS_KEY)
        
        current_time = datetime.now()
        active_peers = []
        
        for username, peer_data in all_peers.items():
            try:
                peer_info = json.loads(peer_data)
                last_seen = datetime.fromisoformat(peer_info['last_seen'])
                
                if (current_time - last_seen).total_seconds() < 300:
                    active_peers.append(peer_info)
                else:
                    r.hdel(PEERS_KEY, username)
                    logger.info(f"Removed old user: {username}")
                    
            except json.JSONDecodeError:
                logger.error(f"Error processing user data: {username}")
                continue
        
        return jsonify({
            "status": "success",
            "count": len(active_peers),
            "peers": active_peers
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting peers: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route('/peerinfo', methods=['GET'])
def get_peer_info():
    try:
        username = request.args.get('username')
        
        if not username:
            return jsonify({
                "status": "error",
                "message": "Username parameter is required"
            }), 400
        
        r = get_redis()
        if not r:
            return jsonify({
                "status": "error",
                "message": "Database connection error"
            }), 500
        
        peer_data = r.hget(PEERS_KEY, username)
        
        if not peer_data:
            return jsonify({
                "status": "error",
                "message": f"User '{username}' not found"
            }), 404
        
        peer_info = json.loads(peer_data)
        
        return jsonify({
            "status": "success",
            "peer": peer_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting peer info: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route('/unregister', methods=['POST'])
def unregister_peer():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data:
            return jsonify({
                "status": "error",
                "message": "Username parameter is required"
            }), 400
        
        username = data['username']
        
        r = get_redis()
        if not r:
            return jsonify({
                "status": "error",
                "message": "Database connection error"
            }), 500
        
        deleted = r.hdel(PEERS_KEY, username)
        
        if deleted > 0:
            logger.info(f"User removed: {username}")
            return jsonify({
                "status": "success",
                "message": f"User '{username}' removed"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": f"User '{username}' not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error removing user: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    try:
        r = get_redis()
        redis_status = "connected" if r else "disconnected"
        
        return jsonify({
            "status": "healthy",
            "service": "P2P STUN Server",
            "redis": redis_status,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/')
def index():
    return jsonify({
        "service": "P2P STUN Server",
        "endpoints": {
            "register": "POST /register",
            "peers": "GET /peers",
            "peerinfo": "GET /peerinfo?username=<username>",
            "unregister": "POST /unregister",
            "health": "GET /health"
        }
    })

if __name__ == '__main__':
    logger.info("Starting STUN Server...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )