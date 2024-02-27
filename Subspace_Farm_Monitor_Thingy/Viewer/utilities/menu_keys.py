import os
import sys
from select import select
from threading import Thread
import utilities.conf as c 
import signal

# Windows-specific imports
if os.name == 'nt':
    import msvcrt


class KBHit(Thread):
    def __init__(self, layout_update_callback):
        super().__init__()
        self.running = True
        self.layout_update_callback = layout_update_callback

        # Non-Windows terminal settings
        if os.name != 'nt':
            import termios
            import atexit
            # Save the terminal settings
            self.fd = sys.stdin.fileno()
            self.old_term = termios.tcgetattr(self.fd)
            self.new_term = termios.tcgetattr(self.fd)

            # New terminal setting unbuffered
            self.new_term[3] = (self.new_term[3] & ~
                                termios.ICANON & ~termios.ECHO)
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)

            # Support normal-terminal reset at exit
            atexit.register(self.set_normal_term)

    def run(self):
        while True:
            key = self.getch()
            if key is not None:
                # ESC key
                if ord(key) == 32:
                    c.show_logging = not c.show_logging
                    self.layout_update_callback()
                elif ord(key) == 81 or ord(key) == 113 or ord(key) == 27:
                    print('Toodles!')
                    if os.name == 'nt':
                        os._exit(0)
                    else:
                        os.kill(os.getpid(), signal.SIGINT)
                    self.layout_update_callback()

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
        """Returns a keyboard character if available, otherwise None."""
        if os.name == 'nt':
            if msvcrt.kbhit():
                return msvcrt.getch().decode()
        else:
            if self.kbhit():
                return sys.stdin.read(1)
        return None
