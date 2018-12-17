#!/usr/bin/env python3
import subprocess
import os
from bottle import get, run, template, request, static_file
import ipaddress

HERE = os.path.dirname(__file__) or "."
TEMPLATE_PATH = os.path.join(HERE, "templates", "index.html")
TEMPLATE = open(TEMPLATE_PATH).read()
STATIC_FILES = os.path.join(HERE, "static")

def get_mac_from_ip(ip:str, default=None):
    """Return a mac address for the ip or default (None)."""
    lines = subprocess.check_output(["ip", "neighbor"]).split(b"\n")
    ip = ip.encode()
    for line in lines:
        # line example
        # 10.137.2.1 dev eth0 lladdr fe:ff:ff:ff:ff:ff STALE
        entries = line.split()
        if not entries or not entries[0] == ip:
            continue
        for entry in entries:
            if entry.count(b":") == 5: # mac address detected
                return entry.decode()
        raise ValueError("Not MAC address found in {}".format(line))
    return default

def get_request_ip():
    """Return the IP address of the connecing client."""
    # see https://stackoverflow.com/a/31419530
    return request.environ.get('HTTP_X_FORWARDED_FOR') or \
           request.environ.get('REMOTE_ADDR')

def get_request_mac(default=None):
    """Return the requesting client's mac address or default (None)."""
    return get_mac_from_ip(get_request_ip(), default)

def get_network_for_ip(ip, default=None):
    """Return the network for an ip address or default (None)."""
    ip = ipaddress.ip_address(ip)
    lines = subprocess.check_output(["ip", "-4", "route"]).split(b"\n")
    for line in lines:
        # example line
        # 172.18.0.0/16 dev br-29cd0bfdf399  proto kernel  scope link  src 172.18.0.1 
        entries = line.split()
        if not entries or not b"/" in entries[0]:
            continue
        # see https://stackoverflow.com/a/1004527
        network = ipaddress.ip_network(entries[0].decode())
        if ip in network:
            return network
    return default

@get('/')
def index():
    return template(
        TEMPLATE,
        mac=get_request_mac())

@get('/static/<file:path>')
def index(file):
    return static_file(file, root=STATIC_FILES)

def main():
    run(host='localhost', port=8080, debug=True)

if __name__ == "__main__":
    main()

