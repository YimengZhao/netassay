
################################################################################
# The Frenetic Project                                                         #
# frenetic@frenetic-lang.org                                                   #
################################################################################
# Licensed to the Frenetic Project by one or more contributors. See the        #
# NOTICES file distributed with this work for additional information           #
# regarding copyright and ownership. The Frenetic Project licenses this        #
# file to you under the following license.                                     #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided the following conditions are met:       #
# - Redistributions of source code must retain the above copyright             #
#   notice, this list of conditions and the following disclaimer.              #
# - Redistributions in binary form must reproduce the above copyright          #
#   notice, this list of conditions and the following disclaimer in            #
#   the documentation or other materials provided with the distribution.       #
# - The names of the copyright holds and contributors may not be used to       #
#   endorse or promote products derived from this work without specific        #
#   prior written permission.                                                  #
#                                                                              #
# Unless required by applicable law or agreed to in writing, software          #
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT    #
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the     #
# LICENSE file distributed with this work for specific language governing      #
# permissions and limitations under the License.                               #
################################################################################

############################################################################################################################
# TO TEST EXAMPLE                                                                                                          #
# -------------------------------------------------------------------                                                      #
# start mininet:  sudo mn --switch ovsk --controller remote --mac --topo linear,3                                          #
# run controller: pox.py --no-cli pyretic/examples/hub.py                                                                  #
# start xterms:   xterm h1 h2 h3                                                                                           #
# start tcpdump:  in each xterm,                                                                                           #
# > IFACE=`ifconfig | head -n 1 | awk '{print $1}'`; tcpdump -XX -vvv -t -n -i $IFACE not ether proto 0x88cc > $IFACE.dump #
# test:           run h1 ping -c 2 h3, examine tcpdumps and confirm that h2 does not see packets on second go around       #
############################################################################################################################

from frenetic.lib import *

def learning_switch_logic(network,ls):
    
    host_to_outport = {}
    for pkt in query_unique(network, all_packets, fields=['switch', 'srcmac']):

        host_p = match(switch=pkt['switch'], dstmac=pkt['srcmac'])

        ## ONLY NEEDED TO KEEP THE POLICY FROM BLOWING UP FROM REDUNDANT RESTRICTS
        if host_to_outport.get((pkt['switch'], pkt['srcmac'])) == pkt['inport']:
            continue

        host_to_outport[(pkt['switch'], pkt['srcmac'])] = pkt['inport']

        ls_pol = ls.get() 
        ls_pol -= host_p    # Don't do our old action.
        ls_pol |= host_p & fwd(pkt['inport'])  # Do this instead.
        ls.set(ls_pol)

def learning_switch(network):
    return DynamicPolicy(network,learning_switch_logic,network.flood)


def example(network):
    network.install_policy_func(learning_switch)
        
main = example


