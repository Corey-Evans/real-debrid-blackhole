from configparser import ConfigParser

import requests


class PushoverSender:
    def __init__(self):
        config = ConfigParser()
        config.read('config.ini')
        self.app_token = config.get('Pushover', 'app_token')
        try:
            self.user_key = config.get('Pushover', 'user_key')
        except:
            self.user_key = None

    def send(self, message='Message from RealDebrid BlackHole'):
        print(message)
        try:
            if self.user_key:
                pass
                requests.post(
                    url='https://api.pushover.net/1/messages.json',
                    data={
                        'token': self.app_token,
                        'user': self.user_key,
                        'message': message
                    }
                )
        except Exception:
            print('Failed to send previous notification.')
