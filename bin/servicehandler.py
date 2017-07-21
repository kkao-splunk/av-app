import os
import sys
import requests,json
import boto3

if sys.platform == "win32":
    import msvcrt
    # Binary mode is required for persistent mode on Windows.
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)

from splunk.persistconn.application import PersistentServerConnectionApplication


class EchoHandler(PersistentServerConnectionApplication):
    def __init__(self, command_line, command_arg):
        PersistentServerConnectionApplication.__init__(self)

    def handle(self, in_string):
        r = requests.get('https://127.0.0.1:8089/servicesNS/Nobody/av-app/storage/collections/data/namespace',verify=False,auth=('admin','changeme'))
        r1 = requests.get('https://127.0.0.1:8089/servicesNS/Nobody/av-app/storage/collections/data/token',verify=False,auth=('admin','changeme'))
        r2 = requests.get('https://localhost:8089/services/namespace_endpoint',verify=False,auth=('admin','changeme'))
        token = str(r1.json()[0]['accessId'])
        cluster = str(r.json()[0]['ns'])
        data = 'http://127.0.0.1:8080/avanti/v0.3/ListServices?provider=aws&region=us-west-1&cluster=' + cluster + '&access_token=' + token
        req = requests.get(data).json()
        return {'payload': req,  # Payload of the request.
                'status': 200          # HTTP status code
        }

    def createParams(self, params):
        pass
