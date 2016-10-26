# COMP3331 Assignment 2 by Nathaniel Henry - z3419400

import sys
import time
#from threading import Timer
#import Timer
import threading
import os
#import Set
from collections import deque
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
    def __eq__(self, other):
        if self.id == other.id:
            return True
        else:
            return False
    def addEdge(self, dest, cost):
        e = Edge(dest, cost)
        self.edges.append(e)

#processess the config.txt format string and returns a list of edges
def processLinks(data):
    lines = data.split("\n")
    originNode = Node(lines[1], lines[0])
    n = int(lines[2])
    destinations = set()
    for i in range(3,n+3):
        info = lines[i].split(" ")
        destinations.add(info[0])
        newNode = Node(info[0], int(info[2]))
        originNode.addEdge(newNode, float(info[1]))
    return (originNode, destinations)

def makeBroadcast(originNode):
    #print "Broadcasting"
    global broadcasted
    broadcasted = []
    data = str(originNode.port) + "\n"
    data += originNode.id + "\n"
    data += str(len(originNode.edges)) + "\n"
    for edge in originNode.edges:
        data += edge.dest.id+" "+str(edge.cost)+" "+str(edge.dest.port)+"\n"
    data = data[:-1]
    for n in originNode.edges:
        sendPacket(n.dest.port, data)
    t1 = threading.Timer(1, makeBroadcast, [homeNode])
    t1.daemon = True
    t1.start()


def sendPacket(port, data):
    hostSocket.sendto(data, ('127.0.0.1', port))


def performSearch(originNode, nodes):
    print "starting search"
    queue = []
    visited = []
    distance = {originNode.id:0}
    previous = {originNode.id:originNode.id}
    queue.append(originNode.id)
    while len(queue) != 0:
        min = -1
        for n in queue: #selective pop from queue
            if min == -1:
                min = distance[n]
                name = n
            elif distance[n] < min:
                name = n
        i=0
        queue.remove(name)
        for n in nodes: #get actual node data from nodes list
            if n.id == name:
                head = n
                break
            i+=1
        if i == len(nodes): #if destination isn't in active nodes
            continue
        visited.append(head.id)
        for n in head.edges:
             dist = n.cost + float(distance[head.id])
             if not n.dest.id in distance.keys():  #first time seeing node
                 distance[n.dest.id] = dist
                 previous[n.dest.id] = head.id
             elif dist < distance[n.dest.id]: #if we've found better path
                 distance[n.dest.id] = dist
                 previous[n.dest.id] = head.id
             #if queue.count(n.dest.id) == 0 and visited.count(n.dest.id) == 0:
             if n.dest.id not in queue and n.dest.id not in visited:
                 queue.append(n.dest.id)
    return (previous, distance)

def getPath(start, dest, previous):
    path = str(dest)
    curr = dest
    while previous[curr] != start:
        path = previous[curr] + path
        curr = previous[curr]
    path = start + path
    return path

def printSearch(originNode):
    global nodes
    graph = nodes
    previous, distance = performSearch(originNode, graph)
    for n in nodes:
        path = getPath(originNode.id, str(n.id), previous)
        print "least-cost path to node "+str(n.id)+": "+str(path)+" and the cost is "+str(distance[n.id])
    t2 = threading.Timer(20, printSearch, [originNode])
    t2.daemon = True
    t2.start()

def checkHeartbeat():
    dead = []
    global heartbeat
    global nodes
    beats = heartbeat
    newNodes = nodes

    for node in beats.keys():
        if beats[node] == 0:
            dead.append(node)

    for n in newNodes:
        if n.id in dead:
            print "lost " + n.id
            del beats[n.id]
            newNodes.remove(n)
    heartbeat = resetHeartbeat(beats)
    nodes = newNodes
    t3 = threading.Timer(5, checkHeartbeat, [])
    t3.daemon = True
    t3.start()

def resetHeartbeat(heartbeat):
    for key in heartbeat.keys():
        heartbeat[key] = 0
    return heartbeat

#################   MAIN PROGRAM START #####################################
homeId = sys.argv[1]
port = int(sys.argv[2])
startFile = sys.argv[3]

homeNode = Node(homeId, port)

#get neighbours from txt file and create home node
f = open(startFile, "r")
data = f.read()
data = str(port) + "\n" + homeId + "\n" + data
homeNode, destinations = processLinks(data)


#bind socket
hostSocket = socket(AF_INET, SOCK_DGRAM)
hostSocket.bind(('127.0.0.1', port))
hostSocket.settimeout(8)


nodes = [] #list of routers it has received from
nodes.append(homeNode)
broadcasted = [] #keeps track of id's of received packets, reset every sec
heartbeat = {} #will test for dead routers

makeBroadcast(homeNode) #start broadcasting thread
printSearch(homeNode) #start searching thread
checkHeartbeat() #start heartbeat thread

while 1:
    try:
        broadcast, sender = hostSocket.recvfrom(1024)
        newNode, destinations = processLinks(broadcast)
        destinations.add(newNode.id) #won't forward to these destinations

        #if this packet is a forwarded one, add senders edges to destinations
        if newNode.port != sender[1] and newNode.id in heartbeat.keys():
            for n in nodes:
                if n.port == sender[1]:
                    for d in n.edges:
                        destinations.add(d.dest.id)
        existing = False
        for n in nodes:
            if newNode.id == n.id:
                try:
                    heartbeat[newNode.id] += 1
                except KeyError:
                    pass
                existing = True
                break
        if not existing:
            try:
                heartbeat[newNode.id] = 0
            except KeyError:
                pass
            nodes.append(newNode)
            heartbeat = resetHeartbeat(heartbeat)
            print str(len(nodes)) + " nodes"

        for n in homeNode.edges: #forward packets
            if n.dest.id not in destinations and n.dest.port != sender[1] and newNode.id not in broadcasted:
                sendPacket(n.dest.port, broadcast) #forward the packet
        broadcasted.append(newNode.id)
    except timeout:
        print "timeout"
        #break
