import utilities.conf as c
import time
import getch
    
def main():
        import keyboard
        while True:
                key = getch.getch() 
                if key == b' ':
                        c.show_logging = not c.show_logging
                
                time.sleep(.4)

       
        
        
        
        
        
