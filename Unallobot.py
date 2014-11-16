#!/usr/bin/python
#Unallobot
# Uses Python 2.7.2

#import pdb
import socket
import ConfigParser
import time
import re
import random
import threading
import json
import SocketServer
import os
import logging 
import daemon

# todo: actually join the channel with the new channel method

class Bot:
    def __init__(self, conf_file):

        # set up logging services:
        self.logger = logging.getLogger('Bot')
        self.logger.setLevel(logging.DEBUG)
        FH = logging.RotatingFileHandler('/var/log/Bot.log',,10000,20)
        FH.setLevel(logging.DEBUG)
        self.logger.addHandler(FH)
        self.logger.debug("starting")

        config = ConfigParser.ConfigParser()
        config.read(conf_file)

        try:
            self.serverAddr = config.get('Server', 'server')
            self.serverPort = config.get('Server', 'port')
            self.serverChan = config.get('Server', 'channel')
            self.botNick = config.get('BotInfo', 'nickname')
            self.botPass = config.get('BotInfo', 'password')
            self.OpperPW = config.get('OpperPW', 'password')
            #self.LogFile = config.get('Logging', 'logfile')
        except ConfigParser.NoOptionError as e:
            self.logger.error("Error parsing config file: " + e.message)

        # Irc connection
        self.irc = None

        # Need this to be the value from the temp_status file on the box
        self.LastStatus = None

        self.commands = {
            # 'test': self.test,
            'eightball': self.eightball,
            '8ball': self.eightball,
            'echo': self.echo,
            'address': self.address,
            'status': self.status,
            'help': self.helpme,
            'JSON': self.json_parser
        }

    def helpme(self,msg):
        keyslist=""
        self.irc.send(self.privmsg('Here is a list of valid commands: \n'))
        for keys in self.commands:
            if keys != 'JSON':
                keyslist = keyslist +'!' + keys + ', '
        self.irc.send(self.privmsg(keyslist))

    def privmsg(self, msg):
        return "PRIVMSG " + self.serverChan + " :" + msg + "\n"

    def test(self, msg):
        #print "In function test: %s" % self.privmsg('Test test test.')
        self.logger.debug("In function test %s" % self.privmsg('Test test test.'))
        self.irc.send(self.privmsg('Test test test.'))

    def echo(self, msg):
        self.irc.send(self.privmsg(msg))

    def join_channel(self):
        # if you try to join the channel immediately after pong, the server won't be ready yet.
        time.sleep(2)
            self.logger.debug("joining the channel %s" % self.serverChan) 
            self.irc.send('JOIN %s\r\n' % (self.serverChan,))
            self.logger.debug("joined %s" % self.serverChan)

    def ping(self, pong):            # Responding to Server Pings
        self.irc.send('PONG :' + pong + '\r\n')

    # this function is formatted like dog doo-doo - Crypt0s
    def eightball(self, data):
        if data != '' and '?' in data:
                self.irc.send(self.privmsg(random.choice(['It is certain.',
                                                          'It is decidedly so.',
                                                          'Without a doubt.',
                                                          'Yeirc. definitely.',
                                                          'You may rely on it.',
                                                          'As I see it, yeirc.',
                                                          'Most likely.',
                                                          'Outlook good.',
                                                          'Signs point to yeirc.',
                                                          'Yeirc.',
                                                          'Reply hazy, try again.',
                                                          'Ask again later.',
                                                          'Better not tell you now.',
                                                          'Cannot predict now.',
                                                          'Concentrate and ask again.',
                                                          'Don\'t count on it.',
                                                          'My reply is no.',
                                                          'My sources say no.',
                                                          'Outlook not so good.',
                                                          'Very doubtful.',
                                                          'Run Away!'])))
        else:
            self.irc.send(self.privmsg('I can do nothing unless you ask me a question....'))

    def address(self, data):
        self.irc.send(self.privmsg("512 Shaw Court #105, Severn, MD 21144"))

    def sign(self, data):        # Check the sign message or Change the sign Message
        self.irc.send(self.privmsg('Not implemented yet.'))

    def status(self, data):        # Check the Status of the space
        #statusMsg = open('/tmp/status').read()[1:]
        #self.irc.send(self.privmsg( statusMsg))
        self.irc.send(self.privmsg(self.LastStatus))

    def json_parser(self,data):
        parsed_data = json.loads(data)
        self.irc.send(self.privmsg(parsed_data["Service"] + ' says ' + parsed_data["Data"]))
        if (parsed_data["Service"]=="Occupancy"):
            self.LastStatus = parsed_data["Service"] + ' says ' + parsed_data["Data"]    

    def connect_and_listen(self):
        self.logger.debug("connecting to: " + self.serverAddr + " " + self.serverPort)

        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.irc.connect((self.serverAddr, int(self.serverPort)))

        self.irc.send('NICK %s\r\n' % (self.botNick,))
        self.irc.send('USER %s 8 * :%s\r\n' % (self.botNick, self.botNick))

        # TODO: trigger the rest of this function on some output from the server MOTD.
        time.sleep(15)

        while True:
            data = 'a'
            while data[-1] != '\n':
                data += self.irc.recv(1)

            text = data[1:]

            #print "received text: \"" + text + "\""
            self.logger.debug("recieved: \"" + text + "\"")

            # TODO: Slice the text, don't use regex.
            if text.find("PING") == 0:
                # Handle the initial ping which prevents DDOS.
                # TODO: There should be a more robust way to join the channel.
                temp = re.search("PING :[a-zA-Z0-9]+", text)
                if temp:
                    pong = temp.group(0)[6:]
                    self.join_channel()
                else:
                    pong = "pong"
                self.ping(pong)

            # Split the messages into parts, don't use regex
            elif text.find(self.serverChan + " :!") != -1:
                # take word right after '!' to the first whitespace, look up in dict of commands, where value is function
                try: 
                    command = text[text.find(' :!')+3:].split()[0]
                except:
                     self.commands['help']('')
                else: 
                    if (command in self.commands) and (command != "JSON"):
                        #print "Calling command %s" % (command,)
                        debug.info("Calling command %s" % (command,))
                        self.commands[command](text[text.find(' :!') + 4 + len(command):])
                    else: self.commands['help'](command)
            elif text.find(self.botNick + " :!JSON") != -1: #Direct Message JSON request
                try:
                    self.commands['JSON'](text[text.find(' :!') + 8:])
                except IOError:
                    self.irc.send(self.privmsg("Stop Attacking the bot"))
            elif (text.find(self.botNick + " :!Op") != -1): #Direct Message Request to Op Someone in IRC
                TempPW = (text[text.find(' :!') + 6:text.find(' :!') + 14])
                UserToBeOppd = text[text.find(' :!')+15:]
                TestOut = "MODE " + self.serverChan + " +o " + UserToBeOppd
                if (TempPW == self.OpperPW):
                    self.irc.send("MODE " + self.serverChan + " +o " + UserToBeOppd)
                    self.logger.info("Opping %s" % UserToBeOppd) 

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        DataToPost = self.data[self.data.find(' :!') + 7:]
        bot.json_parser(DataToPost)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

if __name__ == "__main__":
    HOST = ''
    PORT_A = 9999

    TA = open('/opt/uas/UAS_IRC_Bot/Bot.pid','w')
    pid=str(os.getpid())
    TA.write(pid)
    TA.close()

    #thread for the external listener
    print "started the API listening service"
    server_A = ThreadedTCPServer((HOST, PORT_A),ThreadedTCPRequestHandler)
    server_A_thread = threading.Thread(target=server_A.serve_forever)
    server_A_thread.setDaemon(True)
    server_A_thread.start()
        
    #instantiate the bot -- wrapped in a try/except in case we can't get to the config file.
    print "doing the bot"
    try:
        bot = Bot("/opt/uas/UAS_IRC_Bot/Unallobot.conf")
    except:
        print "We couldn't start the bot.  Check your configuration file?  should be /opt/uas/UAS_IRC_Bot/Unallobot.conf"
        exit(1)

    print "Starting the thread for the bot"
    # The IRC Part is run in a separate thread
    server_B_thread = threading.Thread(target=bot.connect_and_listen)
    server_B_thread.setDaemon(True)
    server_B_thread.start()

    # we need to clean up the pid file so that the run script in init will be in the proper state    
    #os.remove('/opt/uas/UAS_IRC_Bot/Bot.pid')