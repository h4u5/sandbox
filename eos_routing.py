#!/usr/bin/python

import os
from subprocess import Popen, PIPE, STDOUT
import sys
import re
import time

INTERVAL = 60
METRICS = dict(
  msgrecv=0,
  msgsent=0,
  up_down=0,
  state=0,
  pfxrcd=0,
  dict_refrsh=0
)

"""
This is an initial solution to grabbing routing
information for the Arista switches.  Better solutions
include, grabbing it from the GateD API or pulling it from Sysdb
(when it's added).
"""
def main ():

  sys.stdin.close()

  def print_routing(metric, ts, value, tags=""):
    if tags:
      space = " "
    else:
      tags = space = ""
    print "eos.routing.bgp.%s %d %s%s%s" % (metric, ts, value, space, tags)

  """
  June 2013 - EOS 4.10 output format:
  BGP router identifier #.#.#.#, local AS number #####
  Neighbor V AS MsgRcvd MsgSent InQ OutQ Up/Down State PfxRcd
  """
  def parse_output(text):
    ts = int(time.time())  
    for line in output.splitlines():
      line = line.split()
      #grab the ID, local AS tag from the first line
      if line[0] == "BGP":
        #peel off the trailing comma
        id = line[3][:len(line[3])-1]
        local_as = line[7]
      elif line[0] != "Neighbor":
        #ribd isn't offering what we want yet
        if len(line) != 10:
          break
        #grab the AS and neighbor tag for each line
        neighbor = line[0]
        neighbor_as = line[2]
        METRICS["msgrecv"] = line[3]
        METRICS["msgsent"] = line[4]
        #two formats to this? #d##h and HH:MM:SS
        if line[7].find(":"):
          up_down = line[7].split(":")
          METRICS["up_down"] = \
          int(up_down[0])*3600 + int(up_down[1])*60 + int(up_down[2])
        else:
          up_down = re.split('[d,h]', line[7])
          METRICS["up_down"] = 60 * (int(up_down[0])*1440 + int(up_down[1])*60)
        state = line[8]
        #this could be updated to show more values, e.g.
        #active, idle, connect, opensent, openconfirm
        if state == "Estab":
          METRICS["state"] = 1
        else:
          METRICS["state"] = 0
        METRICS["pfxrcd"] = line[9]
        METRICS["dict_refrsh"] = ts
        #print the metrics with the four aforementioned tags
        tags = " id=%s local_as=%s neighbor=%s neighbor_as=%s" \
               % (id, local_as, neighbor, neighbor_as)
        for metric in METRICS:
          print_routing(metric, ts, METRICS[metric], tags)    


  cmd = 'echo "show ip bgp summary" | cliribd'

  while True:
    try:
      p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT, close_fds=True)
    except OSError:
      print >>sts.stderr, "error: OSError when trying Popen(cliribd)"
      return 13 # tcollector doesn't restart
    output = p.stdout.read()
    parse_output(output)

    time.sleep(INTERVAL)
  
if __name__ == '__main__':
  sys.exit(main())
