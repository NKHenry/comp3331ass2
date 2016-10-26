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
    def addEdge(self, dest, cost):
        e = Edge(dest, cost)
        self.edges.append(e)

#processess the config.txt format string and returns a list of edges
def processLinks(data):
    lines = data.split("\n")
    originNode = Node(lines[1], lines[0])
    n = int(lines[2])
    destinations = set()
    #print data
    for i in range(3,n+3):
        info = lines[i].split(" ")
        destinations.add(info[0])
        newNode = Node(info[0], int(info[2]))
        originNode.addEdge(newNode, float(info[1]))
    return (originNode, destinations)

def makeBroadcast(originNode):
    #print "Broadcasting"
    data = str(originNode.port) + "\n"
    data += originNode.id + "\n"
    data += str(len(originNode.edges)) + "\n"
    for edge in originNode.edges:
        data += edge.dest.id + " " + str(edge.cost) + " " + str(edge.dest.port) + "\n"
    data = data[:-1]
    for n in originNode.edges:
        sendPacket(n.dest.port, data)
    t1 = threading.Timer(1, makeBroadcast, [homeNode])
    t1.daemon = True
    t1.start()
    #return data


def sendPacket(port, data):
    hostSocket.sendto(data, ('127.0.0.1', port))

def priorityInsert (dest, dist,queue, distance):
    if len(queue) == 0:
        queue.append(dest)
        return queue
    for i in range(0, len(queue)):
        if distance[queue[i]] > dist:
            queue.insert(i,dest)
            return queue
    queue.append(dest)
    return queue

def performSearch(originNode, nodes):
    print "starting search"
    queue = []
    visited = []
    distance = {originNode.id:0}
    previous = {originNode.id:originNode.id}
    queue.append(originNode.id)
    while len(queue) != 0:
        name = queue.pop(0)
        #print "popped " + str(name)
        i=0
        for n in nodes:
            if n.id == name:
                head = n
                break
            i+=1
        if i == len(nodes):
            continue
        visited.append(head.id)
        for n in head.edges:
             #print "cost is " + str(n.cost) + "existing dist is " + str(distance[head.id])
             dist = n.cost + float(distance[head.id])
             #print str(dist)+ " to "+n.dest.id+" from " + str(head.id)
             if not n.dest.id in distance.keys():
                 #print "new distance is " + str(dist) + " to " + n.dest.id
                 distance[n.dest.id] = dist
                 #print distance[n.dest.id]
                 previous[n.dest.id] = head.id
             elif dist < distance[n.dest.id]:
                 #print "old dist = " + str(distance[n.dest.id]) + "new=" + str(dist)
                 distance[n.dest.id] = dist
                 #print distance[n.dest.id]
                 previous[n.dest.id] = head.id
             if queue.count(n.dest.id) == 0 and visited.count(n.dest.id) == 0:
                 queue = priorityInsert(n.dest.id, dist, queue, distance)
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
    #print "printSearch"
    global nodes
    graph = nodes
    previous, distance = performSearch(originNode, graph)
    for n in nodes:
        path = getPath(originNode.id, str(n.id), previous)
        print "least-cost path to node "+str(n.id)+": "+str(path)+" and the cost is "+str(distance[n.id])
    t2 = threading.Timer(20, printSearch, [originNode])
    t2.daemon = True
    t2.start()

def checkHeartbeat(heartbeat):
    dead = []
    for node in heartbeat.keys():
        if heartbeat[node] == 0:
            dead.append(node)
    return dead

def resetHeartbeat(heartbeat):
    for key in heartbeat.keys():
        heartbeat[key] = 0
    return heartbeat

#################    PROGRAM START #####################################
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

makeBroadcast(homeNode)
#testThread()
nodes = []
removed = []
heartbeat = {}
nodes.append(homeNode)
printSearch(homeNode)
#i=0
while 1:
    try:
        #print "listening"
        broadcast, sender = hostSocket.recvfrom(1024)
        #print "recieved packet"
        #payload = broadcast.split("\n")
        newNode, destinations = processLinks(broadcast)
        destinations.add(newNode.id)

        #if this packet is a forwarded one, add senders edges to destinations
        if newNode.port != sender[1] and newNode.id in heartbeat.keys():
            for n in nodes:
                if n.port == sender[1]:
                    for d in n.edges:
                        destinations.add(d.dest.id)
        existing = False
        for n in nodes:
            if newNode.id == n.id:
                heartbeat[newNode.id] += 1
                existing = True
                break
        if not existing:
            heartbeat[newNode.id] = 0
            nodes.append(newNode)
            heartbeat = resetHeartbeat(heartbeat)
            print str(len(nodes)) + " nodes"
        for n in homeNode.edges:
            if n.dest.id not in destinations and n.dest.port != sender[1]:
                sendPacket(n.dest.port, broadcast) #forward the packet to other nodes
        for key in heartbeat.keys():
            if heartbeat[key] > 10:
                print "Count for " + key + " is " + str(heartbeat[key])
                print payload[1]
                dead = checkHeartbeat(heartbeat)
                for dest in dead:
                    print "deleting " + dest
                    removed.append(dest)
                    del heartbeat[dest]
                    for i in range (0, len(nodes)):
                        if dest == nodes[i].id:
                            lost = nodes.pop(i)
                            print "lost " + lost.id
                            print str(len(nodes)) + " nodes"
                            break
                heartbeat = resetHeartbeat(heartbeat)

    except timeout:
        print "timeout"
        #break
