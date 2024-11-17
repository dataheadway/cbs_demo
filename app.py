from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Verification Token
VERIFY_TOKEN = "my_secure_token_123"

# Your Instagram App credentials (use environment variables for security)
CLIENT_ID =  "1195291211766740"
CLIENT_SECRET =  "846bb5ad2615bc90f0402d76a4b60bec"
REDIRECT_URI = "https://cbs-beta.vercel.app/instagram/callback"
GRAPH_API_URL = "https://graph.facebook.com/v17.0"
ACCESS_TOKEN = None  # Initialize to None

# Welcome route
@app.route('/')
def welcome():
    return "Welcome to CBS", 200

# Handle webhook verification (GET request)
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("WEBHOOK VERIFIED")
            return challenge, 200
        else:
            return "Forbidden", 403

# Handle webhook events (POST request)
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.get_json()

    if data and data.get('object') == 'instagram':
        for entry in data.get('entry', []):
            for messaging in entry.get('messaging', []):
                if 'message' in messaging:
                    sender_id = messaging['sender']['id']
                    message_text = messaging['message'].get('text', '')

                    # Log the incoming message
                    print(f'Received message from {sender_id}: {message_text}')

                    # Example: Send an automated response back
                    send_instagram_message(sender_id, "Thank you for your message!")

    return "EVENT RECEIVED", 200

# OAuth Redirect URL for Instagram
@app.route('/instagram/callback', methods=['GET'])
def instagram_callback():
    code = request.args.get('code')

    if code:
        access_token_url = 'https://api.instagram.com/oauth/access_token'
        payload = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'code': code
        }

        try:
            response = requests.post(access_token_url, data=payload)
            response_data = response.json()

            if 'access_token' in response_data:
                global ACCESS_TOKEN  # Declare ACCESS_TOKEN as global
                ACCESS_TOKEN = response_data['access_token']
                user_id = response_data['user_id']
                print(f"Access Token: {ACCESS_TOKEN}, User ID: {user_id}")
                return "Instagram login successful! Access Token obtained.", 200
            else:
                print(f"Failed to obtain access token: {response_data}")  # Log error details
                return f"Failed to obtain access token: {response_data} + {CLIENT_SECRET}", 400
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return "An error occurred while exchanging code for access token.", 500
    else:
        return "Authorization code not provided", 400

def send_instagram_message(recipient_id, message_text):
    """
    Sends a message to a user on Instagram using the Instagram Graph API.
    """
    url = f"{GRAPH_API_URL}/me/messages"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        },
        "messaging_type": "RESPONSE"
    }
    params = {
        "access_token": ACCESS_TOKEN
    }

    try:
        response = requests.post(url, json=payload, params=params, headers=headers)
        response_data = response.json()
        if response.status_code == 200:
            print(f"Message sent successfully: {response_data}")
        else:
            print(f"Failed to send message: {response_data}")
    except Exception as e:
        print(f"An error occurred while sending message: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
