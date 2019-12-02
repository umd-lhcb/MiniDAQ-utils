#!/usr/bin/env python3
#
# License: BSD 2-clause
# Last Change: Sun Dec 01, 2019 at 08:58 PM -0500
# Stolen from: http://lhcbdoc.web.cern.ch/lhcbdoc/pydim/guide/tutorial.html#using-dim-services

import pydim
import sys

from dimbrowser import DimBrowser


class Tee(object):
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()


def menu():
    print("------ DIMBROWSER Example ------")
    print("1. Print all services known by the DNS")
    print("2. Print all servers known by the DNS")
    print("3. Exit")
    print("--------------------------------")


def print_all_services_known_by_dns(dbr):
    """
    dbr.getServices(wildcard) returns the number of services known by the DNS
    dbr.getNextService() can be called after this call
    """
    nb_services_known_by_DNS = dbr.getServices("*")
    print(("There are {0} services known by the DNS".format(nb_services_known_by_DNS)))
    for i in range(nb_services_known_by_DNS):
        # getNextService().next() returns a tuple
        service_tuple = next(dbr.getNextService())
        print(
            "Service {0} : Type of service = {1} name = {2}, format = {3}".format(
                i + 1, service_tuple[0], service_tuple[1], service_tuple[2]
            ))
    print("")


def print_all_servers_known_by_dns(dbr):
    """
    dbr.getServers() returns the number of servers known by the DNS
    dbr.getNextServer() can be called after this call
    """
    nb_servers_known_by_DNS = dbr.getServers()
    print(("There are {0} servers known by the DNS".format(nb_servers_known_by_DNS)))
    for i in range(nb_servers_known_by_DNS):
        # getNextServer().next() returns a tuple
        server_tuple = next(dbr.getNextServer())
        print(
            "Server {0}, name = {1}, Node name = {2}".format(
                i + 1, server_tuple[0], server_tuple[1]
            ))
    print("")


def print_all_services_provided_by_server(dbr):
    """
    dbr.getServerServices("TimeService-server") returns the number of services
    provided by the TimeService-server.
    dbr.getNextServerService() can be called after this call
    """
    nb_services_on_server = dbr.getServerServices("TimeService-server")
    for i in range(nb_services_on_server):
        # getNextServerServices().next() returns a tuple
        service_server_tuple = next(dbr.getNextServerService())
        print(
            "Service {0} Type of service {1}, service name = {2}, format = {3}".format(
                i + 1,
                service_server_tuple[0],
                service_server_tuple[1],
                service_server_tuple[2],
            ))
    print("")


def print_all_clients_connected_to_server(dbr):
    """
    dbr.getServerClients("TimeService-server") returns the number of clients
    connected to the server
    dbr.getNextServerClient() can be called after this call
    """
    # getNextServerClient() is a generator that generates a tuple or None if no
    # Clients are found this is another way to use the getNext*** functions
    for client_tuple in dbr.getNextServerClient():
        if client_tuple is not None:
            print(
                "Client name = {0}, node name = {1}".format(
                    client_tuple[0], client_tuple[1]
                ))
    print("")


if __name__ == "__main__":
    # If a filename is provided from the command line, write screen printouts to
    # that file as well:
    try:
        f = open(sys.argv[1], 'w')
        sys.stdout = Tee(sys.stdout, f)
    except Exception:
        pass

    # Check if DIM_DNS_NODE variable has been set
    if not pydim.dis_get_dns_node():
        print("No Dim DNS node found. Please set the environment variable DIM_DNS_NODE")
        sys.exit(1)

    exited = False

    print("Instanciating dimbrowser...")
    # dimbrowser has to be instantiated
    dbr = DimBrowser()

    while not exited:
        menu()
        choice = input("Choice : ")
        if choice == "1":
            print_all_services_known_by_dns(dbr)
        elif choice == "2":
            print_all_servers_known_by_dns(dbr)
        elif choice == "3":
            exited = True
        else:
            print("Wrong input !")

    del dbr
    print("Goodbye")
