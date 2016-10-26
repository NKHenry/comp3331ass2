# COMP3331 Assignment 2 by Nathaniel Henry - z3419400

import sys
import time
#from threading import Timer
#import Timer
import threading
import os
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
def processLinks(originNode, data):
    #lines = data.split("\n")
    n = int(data[0])
    destinations = []
    #print data
    for i in range(1,n+1):
        info = data[i].split(" ")
        destinations.append(info[0])
        newNode = Node(info[0], int(info[2]))
        originNode.addEdge(newNode, float(info[1]))
    return (originNode, destinations)

def makeBroadcast(originNode):
    #print "Broadcasting"
    data = originNode.id + "\n"
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
    #for n in originNode.edges:
        #print "sending to " + n.dest.id
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
        print "popped " + str(name)
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
        #print previous[curr]
        path = previous[curr] + path
        curr = previous[curr]
        #print path
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

homeId = sys.argv[1]
port = int(sys.argv[2])
startFile = sys.argv[3]

homeNode = Node(homeId, port)

#get neighbours from txt file
f = open(startFile, "r")
string = f.read()
data = string.split("\n")
homeNode, destinations = processLinks(homeNode, data)

#bind socket

hostSocket = socket(AF_INET, SOCK_DGRAM)
hostSocket.bind(('127.0.0.1', port))
hostSocket.settimeout(8)

makeBroadcast(homeNode)
#testThread()
nodes = []
nodes.append(homeNode)
printSearch(homeNode)
#i=0
while 1:
    try:
        broadcast, sender = hostSocket.recvfrom(1024)
        #print "recieved packet"
        payload = broadcast.split("\n")
        newNode = Node(payload[0], sender[1])
        newData = payload[1:]
        #print "newData length = " + str(len(newData))
        newNode, destinations = processLinks(newNode, newData)
        destinations.append(newNode.id)
        existing = False
        for n in nodes:
            if payload[0] == n.id:
                existing = True
                continue
        if not existing:
            nodes.append(newNode)
            print str(len(nodes)) + " nodes"
        for n in homeNode.edges:
            if destinations.count(n.dest.id) == 0 and n.dest.port != sender[1]:
                #print "forwarding packet to " + n.dest.id
                sendPacket(n.dest.port, broadcast) #forward the packet to other nodes
        #print str(len(nodes)) + " nodes"
        #i+=1
        #time.sleep(1)
    except timeout:
        print "timeout"
        #break
