#!/usr/bin/env python3
import os
import sys
import json
import logging
from flask import Flask, jsonify, request
from datetime import datetime

# Configuración de logging a stdout 
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)

# Configuración desde variables de entorno 
PORT = int(os.environ.get('PORT', 8080))
MESSAGE = os.environ.get('MESSAGE', 'Hello from Flask!')
RELEASE = os.environ.get('RELEASE', 'v0.0.1')

@app.route('/', methods=['GET'])
def home():
    """Endpoint principal que retorna información de la aplicación"""
    logger.info(f"Request received: {request.method} {request.path} from {request.remote_addr}")
    
    response_data = {
        'message': MESSAGE,
        'release': RELEASE,
        'timestamp': datetime.utcnow().isoformat(),
        'method': request.method,
        'path': request.path
    }
    
    logger.info(f"Response sent: {json.dumps({'message': MESSAGE, 'release': RELEASE})}")
    return jsonify(response_data), 200

@app.route('/', methods=['POST'])
def home_post():
    """Endpoint POST para demostración de métodos HTTP"""
    logger.info(f"POST request received from {request.remote_addr}")
    
    return jsonify({
        'error': 'Method not implemented',
        'method': request.method,
        'message': 'This endpoint only accepts GET requests'
    }), 405

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    logger.info("Health check requested")
    return jsonify({'status': 'healthy', 'port': PORT}), 200

@app.errorhandler(404)
def not_found(error):
    """Handler para rutas no encontradas"""
    logger.warning(f"404 error: {request.method} {request.path}")
    return jsonify({'error': 'Not found', 'path': request.path}), 404

if __name__ == '__main__':
    logger.info(f"Starting Flask application on port {PORT}")
    logger.info(f"Configuration: MESSAGE='{MESSAGE}', RELEASE='{RELEASE}'")
    
    # Port binding desde variable de entorno 
    app.run(
        host='127.0.0.1',
        port=PORT,
        debug=False
    )