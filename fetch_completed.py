import glob
import shutil
import traceback
import urllib.parse
from configparser import ConfigParser

import os

import time
import wget
from pyunpack import Archive
from tendo import singleton

from pushover_sender import PushoverSender
from real_debrid_api import RealDebridAPI

class FileFetcher:

    def __init__(self):
        config = ConfigParser()
        config.read('config.ini')
        self.destination_directory=config.get('Downloader', 'destination_directory')

    def download(self, url, torrent_name):
        torrent_name = urllib.parse.unquote(urllib.parse.unquote(torrent_name))
        tmp_dir_name = "/tmp/{}".format(torrent_name)
        try:
            shutil.rmtree(tmp_dir_name)
        except: pass
        os.mkdir(tmp_dir_name)
        PushoverSender().send('Download from RealDebrid started: {}'.format(url))
        tmp_file_path = wget.download(url, tmp_dir_name)
        if tmp_file_path.endswith('.rar'):
            try:
                Archive(filename=tmp_file_path).extractall(tmp_dir_name)
                extracted = True
            except self.ExtractionFailed as e:
                extracted = False
                PushoverSender().send('RAR extraction FAILED: {}, Exception {}, Traceback: {}'.format(
                    tmp_file_path,
                    e,
                    traceback.print_exc()
                ))
            try:
                if extracted:
                    os.remove(tmp_file_path)
            except:
                PushoverSender().send('Deleting RAR FAILED: {}, Exception {}, Traceback: {}'.format(
                    tmp_file_path,
                    e,
                    traceback.print_exc()
                ))
        destination_path = "{}/{}".format(
            self.destination_directory,
            torrent_name
        )

        for found_file in glob.iglob(glob.escape(tmp_dir_name) + '/**/*', recursive=True):
            os.rename(found_file, urllib.parse.unquote(urllib.parse.unquote(
                found_file
            )))

        os.rename(tmp_dir_name, destination_path)
        return destination_path

class RealDebridCompletedAPI(RealDebridAPI):
    class SplitLinks(Exception): pass

    def list_torrents(self):
        unrestrict_links = []
        for torrent in self._request(
            url="{}torrents".format(self.base_url),
            method='get',
            data={
                'filter': 'downloaded'
            }
        ):
            if torrent['status'] != 'downloaded' or torrent['progress'] != 100:
                continue
            if len(torrent['links']) > 1:
                raise self.SplitLinks()
            unrestrict_links.append(
                (
                    torrent['id'],
                    torrent['filename'],
                    self.unrestrict_link(torrent['links'][0])
                )
            )
        return unrestrict_links

    def process(self):
        try:
            for id, torrent_name, url in self.list_torrents():
                try:
                    destination_path = FileFetcher().download(url, torrent_name)
                    PushoverSender().send('Torrent downloaded from RealDebrid: {}'.format(
                        destination_path
                    ))
                except Exception as e:
                    PushoverSender().send('Download FAILED: {}, Exception {}, Traceback: {}'.format(
                        url,
                        e,
                        traceback.print_exc()
                    ))
                    continue
                try:
                    self.delete_torrent(id)
                    PushoverSender().send('Torrent deleted from RealDebrid: {}'.format(
                        destination_path
                    ))
                except Exception as e:
                    PushoverSender().send('Deleting torrent FAILED: {}, Exception {}, Traceback: {}'.format(
                        url,
                        e,
                        traceback.print_exc()
                    ))
                    continue


        except self.SplitLinks:
            PushoverSender().send("Split links are not supported.")
        except RealDebridCompletedAPI.UnexpectedResponse as e:
            PushoverSender().send(e)
        except Exception as e:
            PushoverSender().send('Unknown error: {}, Traceback: {}'.format(
                e,
                traceback.print_exc()
            ))


if __name__ == "__main__":
    me = singleton.SingleInstance() # Prevent multiple instances of the script from running at once
    RealDebridCompletedAPI().process()
