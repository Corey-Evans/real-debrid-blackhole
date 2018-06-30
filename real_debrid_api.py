from configparser import ConfigParser
import requests


class RealDebridAPI:
    class UnexpectedResponse(Exception): pass

    base_url = "https://api.real-debrid.com/rest/1.0/"

    def __init__(self):
        config = ConfigParser()
        config.read('config.ini')
        self.authorization_header = {
            'Authorization': "Bearer {}".format(config.get('RealDebrid', 'private_api_token'))
        }

    def _request(self, url, method, headers={}, data=None, expected_http_code=200):
        response = requests.request(
            method=method,
            url=url,
            headers={
                **self.authorization_header,
                **headers
            },
            data=data
        )
        if response.status_code != expected_http_code:
            msg = "{}: {}".format(
                response.status_code,
                url
            )
            try:
                msg = "{}: {}".format(
                    msg,
                    response.json()['error']
                )
            except:
                pass
            raise self.UnexpectedResponse(msg)
        try:
            return response.json()
        except:
            return response.text

    def unrestrict_link(self, url):
        return self._request(
            url="{}unrestrict/link".format(self.base_url),
            method='post',
            data={
                'link': url
            }
        )['download']

    def delete_torrent(self, id):
        self._request(
            url="{}torrents/delete/{}".format(self.base_url, id),
            method='delete',
            expected_http_code=204
        )