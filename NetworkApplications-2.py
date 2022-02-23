#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import argparse
import socket
import os
import sys
import struct
import select
import time



#Chrome web server @127.0.0.1:8080/index.html
#linux terminal 'curl 127.0.0.1:8080/index.html.

ICMP_ECHO = 8
ID = 1
port = 8080
ICMP_ECHO_REQUEST = 8
ICMP_TIME_EXCEEDED = 11
MAX_HOPS = 64


def setupArgumentParser() -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description='A collection of Network Applications developed for SCC.203.')
        parser.set_defaults(func=ICMPPing, hostname='lancaster.ac.uk')
        subparsers = parser.add_subparsers(help='sub-command help')
        
        parser_p = subparsers.add_parser('ping', aliases=['p'], help='run ping')
        parser_p.set_defaults(timeout=4)
        parser_p.add_argument('hostname', type=str, help='host to ping towards')
        parser_p.add_argument('--count', '-c', nargs='?', type=int,
                              help='number of times to ping the host before stopping')
        parser_p.add_argument('--timeout', '-t', nargs='?',
                              type=int,
                              help='maximum timeout before considering request lost')
        parser_p.set_defaults(func=ICMPPing)

        parser_t = subparsers.add_parser('traceroute', aliases=['t'],
                                         help='run traceroute')
        parser_t.set_defaults(timeout=4, protocol='icmp')
        parser_t.add_argument('hostname', type=str, help='host to traceroute towards')
        parser_t.add_argument('--timeout', '-t', nargs='?', type=int,
                              help='maximum timeout before considering request lost')
        parser_t.add_argument('--protocol', '-p', nargs='?', type=str,
                              help='protocol to send request with (UDP/ICMP)')
        parser_t.set_defaults(func=Traceroute)

        parser_w = subparsers.add_parser('web', aliases=['w'], help='run web server')
        parser_w.set_defaults(port=8080)
        parser_w.add_argument('--port', '-p', type=int, nargs='?',
                              help='port number to start web server listening on')
        parser_w.set_defaults(func=WebServer)

        parser_x = subparsers.add_parser('proxy', aliases=['x'], help='run proxy')
        parser_x.set_defaults(port=8000)
        parser_x.add_argument('--port', '-p', type=int, nargs='?',
                              help='port number to start web server listening on')
        parser_x.set_defaults(func=Proxy)

        args = parser.parse_args()
        return args


class NetworkApplication:

    def checksum(self,str):
        csum = 0
        countTo = (len(str) / 2) * 2
        count = 0
        while count < countTo:
            thisVal = str[count + 1] * 256 + str[count]
            csum = csum + thisVal
            csum = csum & 0xffffffff
            count = count + 2
        if countTo < len(str):
            csum = csum + str[len(str) - 1].decode()
            csum = csum & 0xffffffff
        csum = (csum >> 16) + (csum & 0xffff)
        csum = csum + (csum >> 16)
        answer = ~csum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer

    def printOneResult(self, destinationAddress: str, packetLength: int, time: float, ttl: int, destinationHostname=''):
        if destinationHostname:
            print("%d bytes from %s (%s): ttl=%d time=%.2f ms" % (packetLength, destinationHostname, destinationAddress, ttl, time))
        else:
            print("%d bytes from %s: ttl=%d time=%.2f ms" % (packetLength, destinationAddress, ttl, time))

    def printAdditionalDetails(self, packetLoss=0.0, minimumDelay=0.0, averageDelay=0.0, maximumDelay=0.0):
        print("%.2f%% packet loss" % (packetLoss))
        if minimumDelay > 0 and averageDelay > 0 and maximumDelay > 0:
            print("rtt min/avg/max = %.2f/%.2f/%.2f ms" % (minimumDelay, averageDelay, maximumDelay))


class ICMPPing(NetworkApplication):

    def receiveOnePing(self, icmpSocket, destinationAddress,time_Sent, ID, timeout):
        # 1. Wait for the socket to receive a reply
        # 2. Once received, record time of receipt, otherwise, handle a timeout
        # 3. Compare the time of receipt to time of sending, producing the total network delay
        # 4. Unpack the packet header for useful information, including the ID
        # 5. Check that the ID matches between the request and reply
        # 6. Return total network delay

        #timeLft = Time remaining till timeout
        timeLft = timeout

        #Start waiting for socket to send a reply back
        
        while True:          

            #Header we are unpacking
            receivedPacket, address = icmpSocket.recvfrom(1024)
            icmpHeader = receivedPacket[20:28]
            timeofArrival = time.time()


            #Picking exactly what we need from the header and assining it to variables.
            type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

            

            

            #Packet ID matches?
            if ID == packetID:
                
                #Assigning the size of the packet in bytes to a variable so I can find the sieze of it for debugging.
                #bytesInD = struct.calcsize("d")
                #print(bytesInD," Size of packet")


                #Measuring total network delay.
                totalnetDelay = timeofArrival - time_Sent

                
                return totalnetDelay
            else: 
                print("The ID's don't match")

                timeLft = timeofArrival - time_Sent

                if timeLft <= 0:

                    return
                    
                pass

    def sendOnePing(self, icmpSocket, destinationAddress, ID):
        # 1. Build ICMP header
        # 2. Checksum ICMP packet using given function
        # 3. Insert checksum into packet
        # 4. Send packet using socket
        # 5. Record time of sending


        #Dummy header.
        mychecksum = 0


        #Creating dummy ICMP header
        #struct -- Interpret strings as packed binary data.
        header = struct.pack("bbHHh", ICMP_ECHO, 0, mychecksum, ID, 1)

        data = struct.pack("d",time.time())


        #Calculating the checksum for dummy header.
        mychecksum = self.checksum(header + data)

        #htons -- stores the bytes in the right order.
        mychecksum = socket.htons(mychecksum) 

        #Creating the packet using the header and data.
        header = struct.pack("bbHHh", ICMP_ECHO, 0, mychecksum, ID, 1)
        packet = header + data

        #Sending the packet.
        icmpSocket.sendto(packet,(destinationAddress,0))

        #Recording the time of sending so it can be used in another method.
        sendTime = time.time() 
        return sendTime 

        pass

    def doOnePing(self, destinationAddress, timeout = 4):
        # 1. Create ICMP socket
        # 2. Call sendOnePing function
        # 3. Call receiveOnePing function
        # 4. Close ICMP socket
        # 5. Return total network delay

        #Create ICMP socket.
        icmp = socket.getprotobyname("icmp")

        #Create socket.
        icmpSocket = socket.socket(socket.AF_INET,socket.SOCK_RAW, icmp)

   
        #Here is where all the functions are called so we can workout the total delay.
        time_Sent = self.sendOnePing(icmpSocket,destinationAddress,ID)
        delay = self.receiveOnePing(icmpSocket,ID,time_Sent,timeout,destinationAddress)
        icmpSocket.close()

        return delay

        pass

    def __init__(self, args):
        lostpacket = 0
        totalpackets = 0
        packetloss = 0
        delays = []
        sumofdelays = None
        print('Ping to: %s...' % (args.hostname))
        try:
            # 1. Look up hostname, resolving it to an IP address
            destination = socket.gethostbyname(args.hostname)
            # 2. Call doOnePing function, approximately every second
            for x in range(5):
                delay = self.doOnePing(destination,timeout = 1)
                #Multiplying by 1000 so we can see the answer in ms.
                delay = delay * 1000
                time.sleep(1)
                if delay:
                #Using the print one result with the IP, packet length (size), delay (in ms), and a static of ttl = 200.
                    self.printOneResult(destination,8,delay,200) 
                    totalpackets = totalpackets + 1
                    delays.insert(x,delay)
                if delay > 100.0:
                    print("packet lost")
                    lostpacket = lostpacket + 1
        except socket.gaierror:
            print("Error")
        packetloss = (lostpacket / totalpackets)* 100
        sumofdelays = sum(delays)
        averageDelay = sumofdelays / len(delays) 
        self.printAdditionalDetails(packetloss,min(delays),max(delays),averageDelay)
        # 3. Print out the returned delay (and other relevant details) using the printOneResult method
        # 4. Continue this process until stopped
        
            


class Traceroute(NetworkApplication):  

    def receiveOnePing(self, icmpSocket, destinationAddress,time_Sent, ID, timeout):
        # 1. Wait for the socket to receive a reply
        # 2. Once received, record time of receipt, otherwise, handle a timeout
        # 3. Compare the time of receipt to time of sending, producing the total network delay
        # 4. Unpack the packet header for useful information, including the ID
        # 5. Check that the ID matches between the request and reply
        # 6. Return total network delay

        #timeLft = Time remaining till timeout
        timeLft = timeout

        #Start waiting for socket to send a reply back
        
        while True:          

            #Header we are unpacking
            receivedPacket, address = icmpSocket.recvfrom(1024)
            icmpHeader = receivedPacket[20:28]
            timeofArrival = time.time()


            #Picking exactly what we need from the header and assining it to variables.
            type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

            

            

            #Packet ID matches?
            if ID == packetID:
                
                #Assigning the size of the packet in bytes to a variable so I can find the sieze of it for debugging.
                #bytesInD = struct.calcsize("d")
                #print(bytesInD," Size of packet")


                #Measuring total network delay.
                totalnetDelay = timeofArrival - time_Sent

                
                return totalnetDelay
            else: 
                print("The ID's don't match")

                timeLft = timeofArrival - time_Sent

                if timeLft <= 0:

                    return
                    
                pass

    def sendOnePing(self, icmpSocket, destinationAddress, ID):
        # 1. Build ICMP header
        # 2. Checksum ICMP packet using given function
        # 3. Insert checksum into packet
        # 4. Send packet using socket
        # 5. Record time of sending


        #Dummy header.
        mychecksum = 0


        #Creating dummy ICMP header
        #struct -- Interpret strings as packed binary data.
        header = struct.pack("bbHHh", ICMP_ECHO, 0, mychecksum, ID, 1)

        data = struct.pack("d",time.time())


        #Calculating the checksum for dummy header.
        mychecksum = self.checksum(header + data)

        #htons -- stores the bytes in the right order.
        mychecksum = socket.htons(mychecksum) 

        #Creating the packet using the header and data.
        header = struct.pack("bbHHh", ICMP_ECHO, 0, mychecksum, ID, 1)
        packet = header + data

        #Sending the packet.
        icmpSocket.sendto(packet,(destinationAddress,0))

        #Recording the time of sending so it can be used in another method.
        sendTime = time.time() 
        return sendTime 


    def doOnePing(self, destinationAddress, timeout = 4):
        # 1. Create ICMP socket
        # 2. Call sendOnePing function
        # 3. Call receiveOnePing function
        # 4. Close ICMP socket
        # 5. Return total network delay

        #Create ICMP socket.
        icmp = socket.getprotobyname("icmp")

        #Create socket.
        icmpSocket = socket.socket(socket.AF_INET,socket.SOCK_RAW, icmp)

   
        #Here is where all the functions are called so we can workout the total delay.
        time_Sent = self.sendOnePing(icmpSocket,destinationAddress,ID)
        delay = self.receiveOnePing(icmpSocket,ID,time_Sent,timeout,destinationAddress)
        icmpSocket.close()

        return delay

    pass

    def single_traceroute(self,dest, ttl, timeout, time_left):
        icmp = socket.getprotobyname("icmp")
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        raw_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
        raw_socket.settimeout(timeout)

        try:
            my_checksum = 0
            my_id = os.getpid() & 0xFFFF  # Return the current process id

            # Make a dummy header with a 0 checksum
            header = struct.pack("BBHHH", ICMP_ECHO_REQUEST, 0, my_checksum, my_id, 1)
            data = struct.pack("d", time.time())
            # Calculate the checksum on the data and the dummy header.
            my_checksum = self.checksum(header + data)
            packet = header + data
            raw_socket.sendto(packet, (dest, 0))
            time_sent = time.time()

            started_select = time.time()
            what_ready = select.select([raw_socket], [], [], time_left)
            time_in_select = time.time() - started_select
            if what_ready[0] == []:  # Timeout
                print("%d   Timeout: Socket not ready" % ttl)
                return time_left - (time.time() - started_select)

            time_left = time_left - time_in_select
            if time_left <= 0:  # Timeout
                print("%d   Timeout: No time left" % ttl)
                return time_left

            time_received = time.time()
            rec_packet, addr = raw_socket.recvfrom(1024)
            icmp_header = rec_packet[20:28]
            icmp_type, code, checksum, packetID, sequence = struct.unpack(
                "bbHHh", icmp_header)

            if icmp_type == ICMP_TIME_EXCEEDED:  # TTL is 0
                addr_name = socket.gethostbyaddr(addr[0])

                print("%d   %s (%s)  %.2f ms" % (ttl, addr_name, addr[0],
                                                (time_received - time_sent)
                                                * 1000))
                return time_left
            elif icmp_type == ICMP_ECHO:  # Final destination replied
                # Get time_sent
                byte = struct.calcsize("d")
                time_sent = struct.unpack("d", rec_packet[28:28 + byte])[0]
                addr_name = socket.gethostbyaddr(addr[0])

                print("%d   %s (%s)  %.2f ms" % (ttl, addr_name, addr[0],
                                                (time_received - time_sent)
                                                * 1000))
                return -1
            else:  # Handle other icmp_type
                print("%d   icmp_type: %s   %s (%s)  %.2f ms" % (
                ttl, icmp_type, addr_name, addr[0],
                 (time_received - time_sent) * 1000))
            return time_left
        finally:  # Close socket every time
            raw_socket.close()
    
            

        pass
        
    def __init__(self, args):
        print('Traceroute to: %s...' % (args.hostname))
        ip = socket.gethostbyname(args.hostname)
        type = -1
        TTL = 0
        ip = socket.gethostbyname(args.hostname)
        timeout = 1
        time_left = 1
        try:
            while True:
                for i in range(1,5):
                    TTL = TTL + 1
                    icmp = socket.getprotobyname("icmp")
                    icmpSocket = socket.socket(socket.AF_INET,socket.SOCK_RAW,icmp)
                    icmpSocket.setsockopt(socket.IPPROTO_IP,socket.IP_TTL,TTL)
                    delay = self.doOnePing(ip,timeout = 1)
                    delay = delay * 1000
                    current_IP = icmpSocket.recvfrom(1024)
                    icmpHeader_IP = current_IP[20:28]
                    time.sleep(1)
                    #self.printOneResult(currentIP,8,delay,TTL)
                    self.single_traceroute(ip,TTL,1,time_left)
        except socket.gaierror:
            print("Incorrect host")
        if (type == 0):
            sys.exit()

class WebServer(NetworkApplication):

    def handleRequest(self, tcpSocket):
        # 1. Receive request message from the client on connection socket
        # 2. Extract the path of the requested object from the message (second part of the HTTP header)
        # 3. Read the corresponding file from disk
        # 4. Store in temporary buffer
        # 5. Send the correct HTTP response error
        # 6. Send the content of the file to the socket
        # 7. Close the connection socket

        msge = tcpSocket.recv(port)

        file_Name = msge.split()[1]

        #Assigning tempbuffer as an empty variable for now.
        temp_Buffer = None
        try:
            #Exception returned if file can't be opened
            file_from_disk = open(file_Name[1:], "r") 
            
            temp_Buffer = file_from_disk.read() #Reading file and storing it.
            file_from_disk.close
            
        except FileNotFoundError:
            #Seperating the header from message body using \r\n\r\n
            hdr = "HTTP/1.1 404 Not Found.\r\n\r\n" 
            tcpSocket.send(hdr.encode())

        if (temp_Buffer != None):
            #Response header.
            hdr = "HTTP/1.1 200 OK.\r\n\r\n" 
            tcpSocket.send(hdr.encode())

            i = 0
            #Response body.
            while(i < len(temp_Buffer)): 
                tcpSocket.send(temp_Buffer[i].encode())
                i += 1

            tcpSocket.close()

       
        pass

    def __init__(self, args):
        print('Web Server starting on port: %i...' % (args.port))
        # 1. Create server socket
        # 2. Bind the server socket to server address and server port
        # 3. Continuously listen for connections to server socket
        # 4. When a connection is accepted, call handleRequest function, passing new connection socket (see https://docs.python.org/3/library/socket.html#socket.socket.accept)
        # 5. Close server socket
    
        server_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #Allows the use of the same port.
        server_Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

        #Address is not needed here.
        server_Socket.bind(('',args.port))
        server_Socket.listen(1)

        while True:
            
            try:
                tcpSocket, addr = server_Socket.accept()
                self.handleRequest(tcpSocket)

            except KeyboardInterrupt:
                print('Server terminated.')
                tcpSocket.close()
                return

        server_Socket.close()




class Proxy(NetworkApplication):

    def __init__(self, args):
        print('Web Proxy starting on port: %i...' % (args.port))


if __name__ == "__main__":
    args = setupArgumentParser()
    args.func(args)
