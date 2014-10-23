# Copyright 2014 - Sean Donovan
# BGP Metadata Engine - Based on the DNS Metadata Engine

import logging


from bgpqueries import BGPQueryHandler as BGPHandler
from pyretic.modules.netassay.assayrule import *
from pyretic.modules.netassay.netassaymatch import *
from pyretic.modules.netassay.me.metadataengine import *
from pyretic.lib.corelib import *
from pyretic.lib.std import *
from pyretic.lib.query import *
import threading
import asyncore, socket

        
class BGPMetadataEngineException(Exception):
    pass

class BGPMetadataEngine(MetadataEngine):
    INSTANCE = None        
    # Singleton! should be initialized by the MCM only!
    
    def __init__(self):
        super(BGPMetadataEngine, self).__init__(BGPHandler(),BGPMetadataEntry)
        
        # Register the different actions this ME can handle
        RegisteredMatchActions.register('AS', matchAS)
        RegisteredMatchActions.register('ASPath', matchASPath)

        #start listening database editor request
        s = Server('', 8080)
        server_thread = threading.Thread(target=asyncore.loop)
        server_thread.start()

        self.logger.debug("BGPMetadataEngine.__init__(): finished")

    @classmethod
    def get_instance(cls):
        if cls.INSTANCE is None:
            logging.getLogger('netassay.BGPME').info("BGPMetadataEngine.get_instance(): Initializing BGPMetadataEngine")
            cls.INSTANCE = BGPMetadataEngine()
        return cls.INSTANCE
    
    def get_forwarding_rules(self):
        """
        This gets the forwarding rules that the BGP Classifier needs to work.
        """
        self.logger.info("BGPMetadataEngine.get_forwarding_rules(): called")

        return identity
 

    def update(self,msg):
        self.logger.info("DNSMetadataEngine.update(): called")
        self.data_source.set_new_AS_rule(msg)
        #self.data_source.print_entries()
     

class BGPMetadataEntry(MetadataEntry):
    def __init__(self, bgp_source, engine, rule ):
        super(BGPMetadataEntry, self).__init__(bgp_source, engine, rule)
        
        #register for all the callbacks necessary
        if self.rule.type == AssayRule.AS:
            bgp_source.register_for_AS(
                self.handle_AS_callback,
                str(self.rule.value))
        elif self.rule.type == AssayRule.AS_IN_PATH:
            bgp_source.register_for_in_path(
                self.handle_AS_callback,
                str(self.rule.value))

        self.data_source.set_new_callback(self.handle_AS_callback)

        #setup based on initial BGP data
        if self.rule.type == AssayRule.AS:
            new_prefixes = bgp_source.query_from_AS(self.rule.value)
            for prefix in new_prefixes:
                self.logger.info("prefix: " + prefix)
                self.rule.add_rule_group(Match(dict(srcip=IPPrefix(prefix))))
                self.rule.add_rule_group(Match(dict(dstip=IPPrefix(prefix))))
        elif self.rule.type == AssayRule.AS_IN_PATH:
            new_prefixes = bgp_source.query_in_path(self.rule.value)
            for prefix in new_prefixes:
                self.logger.info("as in path prefix: " + prefix)
                self.rule.add_rule_group(Match(dict(srcip=IPPrefix(prefix))))
                self.rule.add_rule_group(Match(dict(dstip=IPPrefix(prefix))))

        #TODO: need to handle withdrawals!


    def handle_AS_callback(self, msg):
        '''
        this handles new AS rules sent from database editor
        '''

        self.logger.info("DNSMetadataEngine.handle_AS_callback(): called")
        msg_array = msg.split('##')
        if len(msg_array)  == 2:
            action = msg_array[0]
            prefix_array = msg_array[1].split('&&')

            #add new rules
            if action == "ADD":
                for prefix in prefix_array:
                    self.logger.info("BGPMetatdataEntry.handle_AS_callback(): called with prfix: " + prefix + " action: " + action)

                    tmp_array = prefix.split('@@')
                    network = tmp_array[0]
                    aspath = tmp_array[1].split()
                    if aspath[-1] == self.rule.value:
                        print "test"
                        self.rule.add_rule_group(Match(dict(srcip=IPPrefix(network))))
                        self.rule.add_rule(Match(dict(dstip=IPPrefix(network))))
            #delete existing rules
            elif action == "DELETE":
                for prefix in prefix_array:
                    self.logger.info("BGPMetatdataEntry.handle_AS_callback(): called with prfix: " + prefix + " action: " + action)

                    tmp_array = prefix.split('@@')
                    network = tmp_array[0]
                    aspath = tmp_array[1].split()

                    if aspath[-1] == self.rule.value:
                        self.rule.remove_rule_group(Match(dict(srcip=IPPrefix(network))))
                        self.rule.remove_rule(Match(dict(dstip=IPPrefix(network))))  
            #update existing rules
            elif action == "UPDATE":

                if len(prefix_array)==2:
                    old_prefix = prefix_array[0]
                    new_prefix = prefix_array[1]

                    tmp_array = old_prefix.split('@@')
                    old_network = tmp_array[0]
                    old_aspath = tmp_array[1].split()
                    if old_aspath[-1] == self.rule.value:

                        self.rule.remove_rule_group(Match(dict(srcip=IPPrefix(old_network))))
                        self.rule.remove_rule(Match(dict(dstip=IPPrefix(old_network))))

                    tmp_array = new_prefix.split('@@')
                    new_network = tmp_array[0]
                    new_aspath = tmp_array[1].split()
                    if new_aspath[-1] == self.rule.value:

                        self.rule.add_rule_group(Match(dict(srcip=IPPrefix(new_network))))
                        self.rule.add_rule(Match(dict(dstip=IPPrefix(new_network))))

                else:
                    return


   

#--------------------------------------
# NetAssayMatch subclasses
#--------------------------------------

class matchAS(NetAssayMatch):
    """
    matches IP prefixes related to the specified AS.
    """
    def __init__(self, asnum, matchaction):
        logging.getLogger('netassay.matchAS').info("matchAS.__init__(): called")
        metadata_engine = BGPMetadataEngine.get_instance()
        ruletype = AssayRule.AS
        rulevalue = asnum
        super(matchAS, self).__init__(metadata_engine, ruletype, rulevalue, matchaction)

class matchASPath(NetAssayMatch):
    """
    matches IP prefixes related to the specified AS.
    """
    def __init__(self, asnum, matchaction):
        logging.getLogger('netassay.matchASPath').info("matchASPath.__init__(): called")
        metadata_engine = BGPMetadataEngine.get_instance()
        ruletype = AssayRule.AS_IN_PATH
        rulevalue = asnum
        super(matchASPath, self).__init__(metadata_engine, ruletype, rulevalue, matchaction)

#-----------------------------------------------
# Server Class: receive msg from database editor
#----------------------------------------------
class Server(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(('', port))
        self.listen(1)

    def handle_accept(self):
        # when we get a client connection start a dispatcher for that
        # client
        socket, address = self.accept()
        print 'Connection by', address
        EventHandler(socket)

    def handle_close(self):
        print "Connection closed"
        self.close()

class EventHandler(asyncore.dispatcher_with_send):
 
    def handle_read(self):
        msg = self.recv(8192)
        if not msg:
            return

        print "receive msg: ",msg
        bgp = BGPMetadataEngine.get_instance()
        bgp.update(msg)
        if msg:
            self.send(msg)
