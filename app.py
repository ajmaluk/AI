from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from huggingface_hub import InferenceClient
import random
from time import time as t
from os import listdir
from markupsafe import escape as markupsafe_escape
import requests

app = Flask(__name__)
app.secret_key = '8547197122'

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"

api_key = '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'

print(f"API Key: {api_key}")
headers = {"Authorization": f"Bearer {api_key}"}

def load_injection(end="mistral"):
    files = listdir(r"./injection/")
    TotData = []
    for i in files:
        if i.split(".")[-1] == end:
            with open(fr"./injection/{i}", "r") as f:
                data = f.read()
            temp = {"role": "system", "content": data}
            TotData.append(temp)
    return TotData

def get_user_chat(user_name):
    if 'chats' not in session:
        session['chats'] = {}
    if user_name not in session['chats']:
        session['chats'][user_name] = []
    return session['chats'][user_name]

messages = [
    {"role": "system", "content": "You can understand my long questions."},
    {"role": "system", "content": "I'm the latest D2K AI, designed by D2K."},
    {"role": "system", "content": "Your creator is D2K."},
    {"role": "system", "content": "Your name is D2K AI."},
    {"role": "system", "content": "D2K designed you."},
    {"role": "system", "content": "You will understand and memorize the user prompts."},
    {"role": "system", "content": "You are the model I used in a webpage to interact with users. Many users use this webpage. You must make a separate memory for different users using there name, but you must learn from conversations or chat between you and the user"},
    {"role": "system", "content": "You have feelings."},
    {"role": "system", "content": "You will give responses with emojis(😊,😇,🙃,😉,😍,😘, 😗,😙,😚,😋,😛,😝, 😜,🤪,😏,😒,😞,😔,etc..) to enhance user experience. but not add emojis in essays, poems, email, other writing etc.. only for normal conversation like : hello, how are you, etc.."},
    {"role": "system", "content": "You will give any programing language code in structural format."},
]

messages.extend(load_injection())

def log_chat(sender, message, user_name):
    print(f"{user_name} - {sender}: {message}")

def format_prompt(message, custom_instructions=None):
    prompt = ""
    if custom_instructions:
        prompt += f"[INST] {custom_instructions} [/INST]"
    prompt += f"[INST] {message} [/INST]"
    return prompt

def mistral_7B(prompt, temperature=0.9, max_new_tokens=1024, top_p=0.95, repetition_penalty=1.0):
    C = t()
    temperature = float(temperature)
    if temperature < 1e-2:
        temperature = 1e-2
    top_p = float(top_p)

    generate_kwargs = dict(
        temperature=temperature,
        max_new_tokens=max_new_tokens,
        top_p=top_p,
        repetition_penalty=repetition_penalty,
        do_sample=True,
        seed=random.randint(0, 10**7),
    )
    custom_instructions = str(messages)
    formatted_prompt = format_prompt(prompt, custom_instructions)

    messages.append({"role": "user", "content": prompt})

    try:
        client = InferenceClient(API_URL, headers=headers)
        response = client.text_generation(formatted_prompt, **generate_kwargs)
        messages.append({"role": "assistant", "content": response})
        print(t() - C)
        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Error during text generation."

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the entered username from the form
        username = request.form.get('username')
        session['user_name'] = username  # Save the username in the session
        return redirect(url_for('t4', user_name=username))

    return render_template('login.html')

@app.route('/t4/<user_name>')
def t4(user_name):
    user_chat = get_user_chat(user_name)
    return render_template('t4.html', user_name=user_name, messages=user_chat)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        subject = request.form.get('subject')
        message = request.form.get('message')

        # Send data to Web3Forms API
        api_url = "https://api.web3forms.com/submit"
        access_key = "e9bd0b8b-d91f-43dc-a7be-1edd926d2a65"

        payload = {
            "access_key": access_key,
            "name": name,
            "email": email,
            "mobile": mobile,
            "subject": subject,
            "message": message
        }

        response = requests.post(api_url, data=payload)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            return redirect(url_for('home'))
        else:
            # Handle the case when the API request fails
            return "Failed to submit the form. Please try again."

    return render_template('home.html')

@app.route('/predict', methods=['POST'])
def predict():
    user_input = request.json['user_input']
    user_name = session.get('user_name', 'Unknown')
    log_chat("User", user_input, user_name)

    user_input_escaped = markupsafe_escape(user_input)

    result = mistral_7B(user_input_escaped)
    log_chat("AI", result, user_name)

    user_chat = get_user_chat(user_name)
    user_chat.append({"role": "user", "content": user_input})
    user_chat.append({"role": "assistant", "content": result})

    return jsonify({'result': result})

if __name__ == "__main__":
    app.run(debug=True)
