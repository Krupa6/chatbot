import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from flask import Flask, request, jsonify, send_from_directory, Response
import json
import time

app = Flask(__name__)

# HTML content for the interface
HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindCare - Mental Health Support</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f7fa;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #3498db;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }
        h1 {
            margin: 0;
            font-size: 28px;
        }
        .chat-container {
            background-color: white;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            padding: 20px;
            height: 500px;
            display: flex;
            flex-direction: column;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            margin-bottom: 20px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 20px;
            max-width: 80%;
        }
        .user-message {
            background-color: #e8f4fd;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }
        .bot-message {
            background-color: #f0f2f5;
            margin-right: auto;
            border-bottom-left-radius: 5px;
        }
        .message-input {
            display: flex;
            gap: 10px;
        }
        #user-input {
            flex: 1;
            padding: 12px;
            border-radius: 20px;
            border: 1px solid #ddd;
            font-size: 16px;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 0 20px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #2980b9;
        }
        .thinking {
            display: none;
            font-style: italic;
            color: #888;
            margin: 5px 0;
        }
        .crisis-resources {
            margin-top: 20px;
            padding: 15px;
            background-color: #fff8e1;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
        }
        .crisis-resources h3 {
            margin-top: 0;
            color: #e65100;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>MindCare</h1>
            <p>A supportive space to discuss your thoughts and feelings</p>
        </header>
        
        <div class="chat-container">
            <div class="chat-messages" id="chat-messages">
                <div class="message bot-message">
                    Hi there! I'm MindCare, a supportive space for you to talk about your feelings and mental health. 
                    I'm here to listen and provide support, though I should mention I'm not a licensed therapist or a replacement for professional help. 
                    What would you like to talk about today? How have you been feeling recently?
                </div>
            </div>
            
            <div class="thinking" id="thinking">MindCare is thinking...</div>
            
            <div class="message-input">
                <input type="text" id="user-input" placeholder="Type your message here..." autocomplete="off">
                <button id="send-button">Send</button>
            </div>
        </div>
        
        <div class="crisis-resources">
            <h3>Crisis Resources</h3>
            <p>If you're experiencing a mental health crisis or having thoughts of self-harm:</p>
            <ul>
                <li>National Suicide Prevention Lifeline: 988 or 1-800-273-8255</li>
                <li>Crisis Text Line: Text HOME to 741741</li>
                <li>SAMHSA's National Helpline: 1-800-662-4357</li>
            </ul>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const chatMessages = document.getElementById('chat-messages');
            const userInput = document.getElementById('user-input');
            const sendButton = document.getElementById('send-button');
            const thinkingIndicator = document.getElementById('thinking');
            
            // Function to add a new message to the chat
            function addMessage(text, isUser) {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message');
                messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
                messageDiv.textContent = text;
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            // Function to handle sending a message
            function sendMessage() {
                const text = userInput.value.trim();
                if (!text) return;
                
                // Add user message to chat
                addMessage(text, true);
                userInput.value = '';
                
                // Show thinking indicator
                thinkingIndicator.style.display = 'block';
                
                // Send message to server
                fetch('/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: text }),
                })
                .then(response => response.json())
                .then(data => {
                    // Hide thinking indicator
                    thinkingIndicator.style.display = 'none';
                    
                    // Add bot response to chat
                    addMessage(data.response, false);
                })
                .catch(error => {
                    thinkingIndicator.style.display = 'none';
                    addMessage('Sorry, there was an error communicating with the server. Please try again.', false);
                    console.error('Error:', error);
                });
            }
            
            // Event listeners
            sendButton.addEventListener('click', sendMessage);
            userInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        });
    </script>
</body>
</html>"""

def setup_gemini_api():
    """Setup and configure the Gemini API."""
    # Replace with your actual API key
    api_key = "AIzaSyCRVgcfdrW1Rwo5N_0CWOvfn387M0UATeE"  
    if not api_key:
        print("Error: API key not set.")
        exit(1)
        
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        },
        generation_config={
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 2048,
        }
    )

# Store active chat sessions
chat_sessions = {}

@app.route('/')
def index():
    """Serve the main HTML page."""
    return Response(HTML_CONTENT, mimetype='text/html')

@app.route('/send_message', methods=['POST'])
def send_message():
    """Handle message sending from the web interface."""
    data = request.json
    message = data.get('message', '')
    session_id = request.cookies.get('session_id', 'default')
    
    # Get or create chat session
    if session_id not in chat_sessions:
        model = setup_gemini_api()
        chat = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": ["I'd like to talk about my mental health."]
                },
                {
                    "role": "model",
                    "parts": [
                        "Hi there! I'm MindCare, a supportive space for you to talk about your feelings and mental health. "
                        "I'm here to listen and provide support, though I should mention I'm not a licensed therapist or a replacement for professional help. "
                        "What would you like to talk about today? How have you been feeling recently?"
                    ]
                }
            ]
        )
        chat_sessions[session_id] = chat
    else:
        chat = chat_sessions[session_id]
    
    try:
        # Add a small delay to simulate thinking (optional)
        time.sleep(0.5)
        
        # Send message to Gemini API
        response = chat.send_message(message)
        return jsonify({"response": response.text})
        
    except Exception as e:
        print(f"Error communicating with Gemini API: {str(e)}")
        return jsonify({"response": "Sorry, I encountered an error. Let's try again. What's on your mind?"}), 500

if __name__ == "__main__":
    print("Starting MindCare web server on http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True)