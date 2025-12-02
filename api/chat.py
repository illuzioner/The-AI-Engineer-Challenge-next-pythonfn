"""
Vercel serverless function for handling chat requests with OpenAI GPT-4.
This replaces the FastAPI backend for Vercel deployment.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests to /api/chat"""
        try:
            # Check if API key is configured
            if not os.environ.get("OPENAI_API_KEY"):
                self.send_error_response(500, "OPENAI_API_KEY not configured")
                return
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # Parse JSON request
            try:
                request_data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_error_response(400, "Invalid JSON in request body")
                return
            
            # Validate request structure
            if 'messages' not in request_data:
                self.send_error_response(400, "Missing 'messages' field in request")
                return
            
            messages = request_data['messages']
            
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages
            ]
            
            # Add system message at the beginning if not already present
            if not openai_messages or openai_messages[0]["role"] != "system":
                openai_messages.insert(0, {
                    "role": "system",
                    "content": "You are a supportive mental coach."
                })
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4",
                messages=openai_messages
            )
            
            # Prepare response
            reply = response.choices[0].message.content
            response_data = {"reply": reply}
            
            # Send success response
            self.send_success_response(response_data)
            
        except Exception as e:
            # Handle errors
            error_message = f"Error calling OpenAI API: {str(e)}"
            print(f"Error: {error_message}")  # Log for Vercel
            self.send_error_response(500, error_message)
    
    def send_success_response(self, data):
        """Send a successful JSON response"""
        response_json = json.dumps(data)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(response_json.encode('utf-8'))
    
    def send_error_response(self, status_code, message):
        """Send an error JSON response"""
        error_data = {"error": message}
        response_json = json.dumps(error_data)
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(response_json.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

