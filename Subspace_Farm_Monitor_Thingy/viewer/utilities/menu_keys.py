import os
import sys
from select import select
from threading import Thread
import utilities.conf as c 
import time
import yaml

class KBHit(Thread):
    def __init__(self, layout_update_callback, force_layout_update_callback=None):
        super().__init__()
        self.theme_files = [file for file in os.listdir('themes') if file.endswith('.yaml')]
        self.current_theme_index = 0
        self.default_theme = c.theme #config.get('THEME', 'default')
        self.running = True
        self.layout_update_callback = layout_update_callback
        self.force_layout_update_callback = force_layout_update_callback

        # Non-Windows terminal settings
        if os.name != 'nt':
            import termios
            import atexit
            # Save the terminal settings
            self.fd = sys.stdin.fileno()
            self.old_term = termios.tcgetattr(self.fd)
            self.new_term = termios.tcgetattr(self.fd)

            # New terminal setting unbuffered
            self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)

            # Support normal-terminal reset at exit
            atexit.register(self.set_normal_term)
            
    def set_normal_term(self):
        """Resets to normal terminal. On Windows, this is a no-op."""
        if os.name != 'nt':
            import termios
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)
    def update_theme(self):
        theme_name = self.theme_files[self.current_theme_index].replace('.yaml', '')
        self.apply_theme(theme_name)

    def reset_theme(self):
        self.apply_theme(self.default_theme)

    def apply_theme(self, theme_name):
        theme_file = f'themes/{theme_name}.yaml'
        with open(theme_file) as f:
            c.theme_data = yaml.load(f, Loader=yaml.FullLoader)
            
    def run(self):
        while c.running:
            key = self.getch()
            if key is not None:
                
                #print(f"Key pressed: {key} (ord: {ord(key)})")  # Debug print

                # Process keypresses
                if ord(key) == 32:  # Space key
                    c.paused = not c.paused
                elif ord(key) == ord('+'):
                    
                    theme_list =  [themes for themes in self.theme_files if themes != self.theme_files[self.current_theme_index].replace('.yaml', '')]
                    self.current_theme_index = (self.current_theme_index - 1) % len(theme_list)
                    self.update_theme()
            
                elif ord(key) == ord('-'):
                    theme_list =  [themes for themes in self.theme_files if themes != self.theme_files[self.current_theme_index].replace('.yaml', '')]
                    self.current_theme_index = (self.current_theme_index + 1) % len(theme_list)
                    self.update_theme()            
                elif key == '0':
                    self.reset_theme()
                elif ord(key) in {81, 113}:  # Q or q key
                    print('Toodles!')
                    c.running = False
                    self.set_normal_term()
                
                elif ord(key) == ord('1'):
                    c.view_state = 1
                elif ord(key) == ord('2'):
                    c.view_state = 2
                elif ord(key) == ord('3'):
                    c.view_state = 3
                elif ord(key) == 9:  # Tab key
                    c.view_xtras = not c.view_xtras
                else: 
                    print(f"Key pressed: {key} (ord: {ord(key)})")  # Debug print
                    
                        
                self.layout_update_callback()  # Update the layout immediately
            time.sleep(.01)

    def stop(self):
        self.running = False

    def set_normal_term(self):
        """Resets to normal terminal. On Windows, this is a no-op."""
        if os.name != 'nt':
            import termios
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)

    def kbhit(self):
        """Returns True if keyboard character was hit, False otherwise."""
        if os.name == 'nt':
            return msvcrt.kbhit()
        else:
            dr, _, _ = select([sys.stdin], [], [], 0)
            return dr != []

    def getch(self):
        try:  
            if os.name == 'nt':
                if msvcrt.kbhit():
                    return msvcrt.getch().decode()
            else:
                if self.kbhit():
                    return sys.stdin.read(1)
            return None
        except:
            return None
