import os
import requests
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# Gemini API configuration
API_KEY = "AIzaSyCYuXMTQIXPE06TTjSev4Fhpq7tnh7EJgY"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-8b:generateContent?key={API_KEY}"

# HTML Content
HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Talkie Pie - Mental Health Support</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f5f7fa; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        header { background-color: #3498db; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        h1 { margin: 0; font-size: 28px; }
        .chat-container { background-color: white; border-radius: 0 0 8px 8px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); padding: 20px; height: 500px; display: flex; flex-direction: column; }
        .chat-messages { flex: 1; overflow-y: auto; padding: 10px; margin-bottom: 20px; }
        .message { margin-bottom: 15px; padding: 10px 15px; border-radius: 20px; max-width: 80%; }
        .user-message { background-color: #e8f4fd; margin-left: auto; border-bottom-right-radius: 5px; }
        .bot-message { background-color: #f0f2f5; margin-right: auto; border-bottom-left-radius: 5px; white-space: pre-wrap; }
        .message-input { display: flex; gap: 10px; }
        #user-input { flex: 1; padding: 12px; border-radius: 20px; border: 1px solid #ddd; font-size: 16px; }
        button { background-color: #3498db; color: white; border: none; border-radius: 20px; padding: 0 20px; cursor: pointer; font-size: 16px; transition: background-color 0.3s; }
        button:hover { background-color: #2980b9; }
        .thinking { display: none; font-style: italic; color: #888; margin: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Talkie Pie 🐼</h1>
            <p>A supportive space to discuss your thoughts and feelings 🧘‍♀️</p>
        </header>

        <div class="chat-container">
            <div class="chat-messages" id="chat-messages">
                <div class="message bot-message">
                    Hi there! I'm Talkie Pie 💙 How do you feel today? 😊
                </div>
            </div>

            <div class="thinking" id="thinking">thinking...</div>

            <div class="message-input">
                <input type="text" id="user-input" placeholder="Type your message here..." autocomplete="off" />
                <button id="send-button">Send</button>
            </div>
        </div>

    <script>
        document.addEventListener('DOMContentLoaded', function () {
            const chatMessages = document.getElementById('chat-messages');
            const userInput = document.getElementById('user-input');
            const sendButton = document.getElementById('send-button');
            const thinkingIndicator = document.getElementById('thinking');

            function addMessage(text, isUser) {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message');
                messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
                messageDiv.textContent = text;
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            function sendMessage() {
                const text = userInput.value.trim();
                if (!text) return;
                addMessage(text, true);
                userInput.value = '';
                thinkingIndicator.style.display = 'block';

                fetch('/send_message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text }),
                })
                .then(response => response.json())
                .then(data => {
                    thinkingIndicator.style.display = 'none';
                    addMessage(data.response, false);
                })
                .catch(error => {
                    thinkingIndicator.style.display = 'none';
                    addMessage('Sorry, there was an error communicating with the server. Please try again.', false);
                    console.error('Error:', error);
                });
            }

            sendButton.addEventListener('click', sendMessage);
            userInput.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return Response(HTML_CONTENT, mimetype='text/html')

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    message = data.get('message', '')

    prompt = f"Please respond in 3 to 4 friendly and supportive short lines with appropriate emojis based on this message: {message}"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload, timeout=10)
        response.raise_for_status()
        response_json = response.json()

        generated_text = response_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if not generated_text:
            generated_text = "Sorry, I couldn't generate a response. Please try again."

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        generated_text = "Sorry, there was an error communicating with the AI service."

    return jsonify({"response": generated_text})

if __name__ == "__main__":
    print("Starting Talkie Pie web server on http://127.0.0.1:5000")
    app.run(debug=True)
