import urllib3
import requests

__author__ = 'aindrias'
http = urllib3.PoolManager()

def load_vk_posts(offset):
    print("hello you " + str(offset))
    requests.Request()

if __name__ == '__main__':
    load_vk_posts(2)