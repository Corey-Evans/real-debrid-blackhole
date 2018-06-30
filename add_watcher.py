import time
import os
import traceback
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from configparser import ConfigParser
from pushover_sender import PushoverSender
from real_debrid_api import RealDebridAPI


class BlackHoleHandler(FileSystemEventHandler):
    def on_created(self, event):
        try:
            if event.is_directory or all([
                    not event.src_path.endswith('.torrent'),
                    not event.src_path.endswith('.magnet')
            ]):
                return False
            PushoverSender().send('Torrent found in blackhole directory: {}'.format(
                event.src_path
            ))
            if event.src_path.endswith('.torrent'):
                RealDebridAddAPI().add_torrent(event.src_path)
            if event.src_path.endswith('.magnet'):
                RealDebridAddAPI().add_magnet(event.src_path)
            try:
                os.remove(event.src_path)
            except Exception as e:
                PushoverSender().send('Deletion of Local torrent FAILED: {}, Exception: {}, Traceback: {}'.format(
                    event.src_path,
                    e,
                    traceback.print_exc()
                ))
        except RealDebridAddAPI.UnexpectedResponse as e:
            PushoverSender().send(e)
        except Exception as e:
            PushoverSender().send('Unknown error: {}, Traceback: {}'.format(
                e,
                traceback.print_exc()
            ))

class RealDebridAddAPI(RealDebridAPI):
    def torrent_slot_available(self):
        url = "{}torrents/activeCount".format(self.base_url)
        response_data = self._request(
            url=url,
            method='get'
        )
        return response_data['nb'] < response_data['limit']

    def _wait_for_slot(self):
        while not self.torrent_slot_available():
            delay_minutes = 5
            time.sleep(delay_minutes * 60)

    def add_torrent(self, torrent_file_path):
        self._wait_for_slot()
        torrent_id = self._request(
            url="{}torrents/addTorrent".format(self.base_url),
            method='put',
            headers={'content-type': 'application/x-bittorrent'},
            data=open(torrent_file_path, 'rb').read(),
            expected_http_code=201
        )['id']
        self.select_all_files(torrent_id)

    def add_magnet(self, magnet_file_path):
        self._wait_for_slot()
        torrent_id = self._request(
            url="{}torrents/addMagnet".format(self.base_url),
            method='post',
            data={'magnet': open(magnet_file_path, 'rb').read()},
            expected_http_code=201
        )['id']
        self.select_all_files(torrent_id)

    def select_all_files(self, torrent_id):
        self._request(
            url="{}torrents/selectFiles/{}".format(
                self.base_url,
                torrent_id
            ),
            method='post',
            data={'files': 'all'},
            expected_http_code=204
        )

if __name__ == "__main__":
    config = ConfigParser()
    config.read('config.ini')
    event_handler = BlackHoleHandler()
    observer = Observer()
    observer.schedule(
        event_handler,
        path=config.get('BlackHole', 'WatchDirectory'),
        recursive=True
    )
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
