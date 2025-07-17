from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import json
import schedule
import time
import threading

load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

def scrape_hacker_news_task():
    page = 1  
    url = f'http://news.ycombinator.com/?p={page}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []
    for item in soup.select('.athing'):
        title = item.select_one('.titleline > a').text
        url = item.select_one('.titleline > a')['href']
        articles.append({'title': title, 'url': url})
    with open('data.json', 'w') as f:
        json.dump(articles, f)
    print(f"Scraped data saved at {time.ctime()}")

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/api/auth', methods=['POST'])
def auth():
    code = request.json.get('code')
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    payload = {
        'client_id': os.getenv('GITHUB_CLIENT_ID'),
        'client_secret': os.getenv('GITHUB_CLIENT_SECRET'),
        'code': code,
        'redirect_uri': os.getenv('REDIRECT_URI', 'https://rohit-assignment-alpha.vercel.app/')
    }
    headers = {'Accept': 'application/json'}
    response = requests.post('https://github.com/login/oauth/access_token', data=payload, headers=headers)
    token_data = response.json()
    if 'access_token' in token_data:
        user_response = requests.get('https://api.github.com/user', headers={
            'Authorization': f'Bearer {token_data["access_token"]}',
            'Accept': 'application/json'
        })
        user_data = user_response.json()
        return jsonify({'user': {'name': user_data.get('login')}})
    return jsonify({'error': 'Authentication failed'}), 401

@app.route('/api/scrape')
def scrape_hacker_news():
    page = request.args.get('page', 1, type=int)
    url = f'http://news.ycombinator.com/?p={page}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []
    for item in soup.select('.athing'):
        title = item.select_one('.titleline > a').text
        url = item.select_one('.titleline > a')['href']
        articles.append({'title': title, 'url': url})
    with open('data.json', 'w') as f:
        json.dump(articles, f)
    return jsonify(articles)

@app.route('/api/data')
def get_data():
    with open('data.json', 'r') as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == '__main__':
    
    schedule.every(1).minutes.do(scrape_hacker_news_task)

    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Start the Flask server
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
