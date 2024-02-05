import time
import conf as c
import sys

def main():
    while True:

                    try:
                        
                      with open(c.node_log_file, 'r', encoding = "utf-16") as file:
                        while True:
                            line = file.readline()
                            line_plain = line # .decode()                          
                            if line == "\r\n" or line == "\n" or line == "":
                                continue
                            
                            elif "peers), best: " in line_plain:
                                c.peers = line_plain.split()[6][+1:]
                                c.best_block = line_plain.split()[9]
                                c.finalized = line_plain.split()[12]
                                c.ul = line_plain.split()[15]
                                c.dl = line_plain.split()[17]
                                
                                
                    except:
                        print("Error > " + str(sys.exc_info()[0]))
                        print('Exception: Retrying in 5 minutes ') # Set correct after testing
                        time.sleep(5)  #  before I tweak exceptions