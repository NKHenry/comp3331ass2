# COMP3331 Assignment 2 by Nathaniel Henry - z3419400

import sys
import time
import os
from socket import *

class Edge:
    def __init__(self, dest, cost):
        self.dest = dest
        self.cost = cost

class Node:
    def __init__(self, id, port):
        self.id = id
        self.port = port
        self.edges = []
    def addEdge(self, dest, cost):
        e = Edge(dest, cost)
        self.edges.append(e)

#processess the config.txt format string and returns a list of edges
def processLinks(originNode, data):
    lines = data.split("\n")
    n = lines[0]
    edges = []
    for i in range(1,n):
        info = lines[i].split(" ")
        newNode = Node(info[0], info[2])
        originNode.addEdge(newNode, double(info[1]))
    return originNode

def getBroadcastPacket(originNode):
    data = originNode.id + "\n"
    data += str(length(originNode.edges)) + "\n"
    for edge in originNode.edges:
        data += edge.dest.id + " " + edge.cost + " " + edge.dest.port + "\n"
    return data


homeId = sys.argv[1]
port = sys.argv[2]
startFile = sys.argv[3]

graph = []
homeNode = Node(homeId, port)

#get neighbours from txt file
f = open(startFile, "r")
data = f.read()
homeNode = processLinks(homeNode, data)

addr = (127.0.0.1, port)
hostSocket = socket(AF_INET, SOCK_DGRAM)
start = time.time()

#while 1:
