#!/usr/bin/env python

import flask
import logging
import requests
import configparser
import pixiv

config = configparser.ConfigParser()
config.sections()
config.read('linebot_yomao.conf')
requests_kwargs = None

WEBHOOK_PORT = int(config['Default']['webhook_port'])
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_URL_PATH = config['Default']['webhook_path']

pixiv.pixiv_username = config['Default']['pixiv_username']
pixiv.pixiv_password = config['Default']['pixiv_password']

if config.has_option('Default', 'requests_kwargs'):
	requests_kwargs = config['Default']['requests_kwargs'].replace('\n', '')
	requests_kwargs = eval(requests_kwargs)

p = pixiv.pixiv_crewler(**requests_kwargs)

LINE_ENDPOINT = "https://trialbot-api.line.me"

HEADERS = {
	"X-Line-ChannelID": config['Default']['channel_id'],
	"X-Line-ChannelSecret": config['Default']['channel_secret'],
	"X-Line-Trusted-User-With-ACL": config['Default']['mid']
}

app = flask.Flask(__name__)
app.config.from_object(__name__)
app.logger.setLevel(logging.DEBUG)

def send_text(to, text):
	content = {
		"contentType": 1,
		"toType": 1,
		"text": text
	}
	events(to, content)

def send_picture(to, img):
	content = {
		"contentType": 2,
		"toType": 1,
		"originalContentUrl": img["origin"],
		"previewImageUrl": img["thumb"]
	}
	events(to, content)

def events(to, content):
	app.logger.info(content)
	data = {
		"to": to,
		"toChannel": "1383378250",
		"eventType": "138311608800106203",
		"content": content
	}
	r = requests.post(LINE_ENDPOINT + "/v1/events", json=data, headers=HEADERS)
	app.logger.info(r.text)

def parse_message(text):
	arr = text.split(' ')
	if arr[0] == '/yomao':
		return arr[1:]
	else:
		return ''

@app.route('/')
def index():
	return ''

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
	json_string = flask.request.json
	app.logger.info(json_string)
	app.logger.info(flask.request.headers)
	update = json_string['result'][0]
	if update["eventType"] == "138311609100106403":
		send_text([update["from"]], '')
	elif update["eventType"] == "138311609000106303":
		text = update['content']['text']
		keywords = parse_message(text)
		if keywords and len(keywords) > 0:
			image = p.get_image(keywords)
			send_picture([update['content']['from']], image)
	return ''

app.run(host=WEBHOOK_LISTEN, port=WEBHOOK_PORT, debug=True)
