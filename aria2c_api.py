import xmlrpc.client
from configparser import ConfigParser


class Aria2cAPI(object):
    class DownloadFailed(Exception): pass
    def __init__(self):
        self.config = ConfigParser()
        self.config.read('config.ini')
        self.server = xmlrpc.client.ServerProxy(
            self.config.get('Aria2c', 'url'),
            allow_none=True
        )
        self.secret_tocken = self.config.get('Aria2c', 'secret_tocken')

    def add(self, url, destination):
        return self.server.aria2.addUri(
            "token:{}".format(self.secret_tocken),
            [url],
            {
                "dir": destination
            }
        )

    def is_complete(self, gid):
        status = self.server.aria2.tellStatus(
            "token:{}".format(self.secret_tocken),
            gid
        )
        if status['status'] in ['error', 'removed']:
            raise self.DownloadFailed('Status is {}.'.format(status))
        return (status['status'] == 'complete', status['files'][0]['path'])
