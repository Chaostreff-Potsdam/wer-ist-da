#!/usr/bin/env python3
import subprocess
import os
from bottle import get, run, template, request, static_file, post
import ipaddress
import json
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(__file__) or "."
TEMPLATE_PATH = os.path.join(HERE, "templates", "index.html")
TEMPLATE = open(TEMPLATE_PATH).read()
STATIC_FILES = os.path.join(HERE, "static")
PING_TTL = 2
PING_SECONDS = 0.5

# varables
DB_FILE = os.path.join(HERE, "data.json") # file to save user data to
NUMBER_OF_PARALLEL_PINGS = 128

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
                return entry.decode().upper()
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

class DB:
    """Data state of the application kept between restarts."""
    
    DEFAULT = {"devices":[]}
    
    @classmethod
    def load(cls):
        """Load the database."""
        try:
            with open(DB_FILE) as file:
                return json.load(file)
        except FileNotFoundError:
            return cls.DEFAULT
        
    @staticmethod
    def save(data):
        """Save what has come from load."""
        with open(DB_FILE, "w") as file:
            return json.dump(data, file, indent=2)

def ping(ip):
    """Ping an ip address."""
    subprocess.run([
        "ping",
        "-r", # only directly on interfaces
        "-t", str(PING_TTL),
        "-c", "1", # number of pings
#        "-4", # IPv4 only # does not work everywhere
        "-n",
        "-w", str(PING_SECONDS),
        str(ip)],
        stdout=subprocess.DEVNULL # usage errors will still print
    )

def iterate_network_addresses(network_or_ip_address):
    """Iterate over all network addresses.
    
    If the network is not known, it is not used."""
    network = get_network_for_ip(network_or_ip_address)
    if network is None: # filter unused networks
        return
    ip = network.network_address + 1
    while ip in network:
        if ip != network.broadcast_address:
             yield ip
        ip += 1

def ping_network(network_or_ip_address, concurrent_pings=NUMBER_OF_PARALLEL_PINGS):
    """Ping all addresses in a network."""
    ping_pool = ThreadPoolExecutor(NUMBER_OF_PARALLEL_PINGS)
    ping_pool.map(ping, iterate_network_addresses(network_or_ip_address))
    ping_pool.join()

def get_reachable_mac_addresses():
    lines = subprocess.check_output(["ip", "neighbor"]).split(b"\n")
    macs = set()
    for line in lines:
        mac = None
        reachable = False
        for entry in line.split():
            if b":" in entry:
                mac = entry
            elif entry == b"REACHABLE":
                reachable = True
        if mac is None or not reachable:
            continue
        macs.add(mac.decode())
    return macs

@get('/')
def index():
    """Render the welcome template."""
    return template(
        TEMPLATE,
        mac=get_request_mac(),
        data=DB.load(),
        present=get_reachable_mac_addresses())

@post('/')
def index():
    """Save the posted data and render the welcome template."""
    data = DB.load()
    user = {}
    # load user data
    mac = user["mac"] = get_request_mac()
    assert mac is not None, "A MAC address is required but is not know."
    user["name"] = request.forms["name"][:100]
    user["about"] = request.forms["about"][:500]
    user["there"] = "there" in request.forms
    user["away"] = "away" in request.forms
    save = user["there"] or user["away"] # whether to add or remove the entry
    found = False
    for i in range(len(data["devices"]) - 1 , -1, -1):
        if data["devices"][i]["mac"] == mac:
            if save:
                data["devices"][i] = user
            else:
                del data["devices"][i]
            found = True
    if save and not found:
        data["devices"].append(user)
    DB.save(data)
    return template(
        TEMPLATE,
        mac=mac,
        data=data,
        present=get_reachable_mac_addresses(),
        saved=save)

@get('/static/<file:path>')
def index(file):
    return static_file(file, root=STATIC_FILES)

def main():
    run(host='0.0.0.0', port=8080, debug=True)

if __name__ == "__main__":
    main()

