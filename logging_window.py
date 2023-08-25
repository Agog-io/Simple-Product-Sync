import datetime
import queue
import logging
import signal
import time
import math
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter.constants import DISABLED
from tkinter import ttk, VERTICAL, HORIZONTAL, N, S, E, W

logger = logging.getLogger(__name__)
global Third
Third = None

class QueueHandler(logging.Handler):
    """Class to send logging records to a queue

    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    """
    # Example from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    # (https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget) is not thread safe!
    # See https://stackoverflow.com/questions/43909849/tkinter-python-crashes-on-new-thread-trying-to-log-on-main-thread

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class ConsoleUi:
    """Poll messages from a logging queue and display them in a scrolled text widget"""

    def __init__(self, frame):
        self.frame = frame
        # Create a ScrolledText wdiget
        self.scrolled_text = ScrolledText(frame, state='disabled', height=12)
        self.scrolled_text.grid(row=0, column=0, sticky=(N, S, W, E))
        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)
        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        self.queue_handler.setFormatter(formatter)
        logger.addHandler(self.queue_handler)
        # Start polling messages from the queue
        self.frame.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)


class FormUi:

    def __init__(self, frame , source ):
        self.frame = frame
        # Create a combobbox to select the logging level
        # values = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        # self.level = tk.StringVar()
        # ttk.Label(self.frame, text='Level:').grid(column=0, row=0, sticky=W)
        # self.combobox = ttk.Combobox(
        #     self.frame,
        #     textvariable=self.level,
        #     width=25,
        #     state='readonly',
        #     values=values
        # )
        # self.combobox.current(0)
        # self.combobox.grid(column=1, row=0, sticky=(W, E))
        # # Create a text field to enter a message
        # self.message = tk.StringVar()
        # ttk.Label(self.frame, text='Message:').grid(column=0, row=1, sticky=W)
        # ttk.Entry(self.frame, textvariable=self.message, width=25).grid(column=1, row=1, sticky=(W, E))
        # Add a button to log the message
        global button
        button = ttk.Button(self.frame, text='Αρχή ' + source, command=windowHelpers.callableFunct)
        button.grid(column=1, row=2, sticky=W)

    def submit_message(self):
        # Get the logging level numeric value
        lvl = getattr(logging, self.level.get())
        logger.log(lvl, self.message.get())


class ThirdUi:

    def __init__(self, frame):
        self.frame = frame
        # ttk.Label(self.frame, text='This is just an example of a third frame').grid(column=0, row=1, sticky=W)
        self.label = ttk.Label(self.frame, text='Εδώ θα φανεί η πορεία του import')
        self.label.grid(column=0, row=4, sticky=W)
        self.pb = ttk.Progressbar(
            self.frame,
            orient='horizontal',
            mode='determinate',
            length=280
        )
        self.countInDb = 0
        self.countNow = 0
        self.started = 0
        self.lastTime = 0
        self.prog = 0
        self.pb.grid(column=0, row=0, padx=10, pady=20)
    
    def progress(self):
        self.lastTime = time.time()
        diftime = self.lastTime - self.started
        diftime = float("{:.2f}".format(diftime))
        if self.countNow == 0 :
            return
        forone = diftime / self.countNow
        rem = self.countInDb - self.countNow
        secsToGo = int(rem * forone)
        timeThen = self.lastTime + secsToGo
        dt_object = datetime.datetime.fromtimestamp(timeThen)
        dt_object = dt_object.replace(second=0, microsecond=0)

        prog = ( int(self.countNow)  / int(self.countInDb) ) * 100
        prog = float("{:.2f}".format(prog))
        self.prog = prog
        self.pb['value'] = prog
        self.label['text'] = str(self.countNow) + " / " + str(self.countInDb) + ' εχουν ενημερωθεί ('+str(self.prog)+'%)' + ' , απομένουν '+ str(datetime.timedelta(seconds=secsToGo)) + ' (περίπου στις '+ str(dt_object) +'), εχουν περάσει '+ str(datetime.timedelta(seconds=math.ceil(diftime)))




class App:

    def __init__(self, root , source ):
        # global Third
        self.root = root
        root.title('Logging Handler')
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        # Create the panes and frames
        vertical_pane = ttk.PanedWindow(self.root, orient=VERTICAL)
        vertical_pane.grid(row=0, column=0, sticky="nsew")
        horizontal_pane = ttk.PanedWindow(vertical_pane, orient=HORIZONTAL)
        vertical_pane.add(horizontal_pane)
        form_frame = ttk.Labelframe(horizontal_pane, text="Δράσεις")
        form_frame.columnconfigure(1, weight=1)
        horizontal_pane.add(form_frame, weight=1)
        console_frame = ttk.Labelframe(horizontal_pane, text="Console")
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        horizontal_pane.add(console_frame, weight=1)
        third_frame = ttk.Labelframe(vertical_pane, text="Πορεία")
        vertical_pane.add(third_frame, weight=1)
        # Initialize all frames
        self.form = FormUi(form_frame , source )
        self.console = ConsoleUi(console_frame)
        self.third = ThirdUi(third_frame)
        
        # Third = self.third
        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.root.bind('<Control-q>', self.quit)
        signal.signal(signal.SIGINT, self.quit)

    def quit(self, *args):
        importProcInst.stop()
        self.root.destroy()



class ImportProc(threading.Thread):
    def __init__(self , source , start , stop , init ):
        super().__init__()
        
        self._start_funct = start
        self._source = source
        self._stop_func = stop
        self._init_func = init
        self._stop_event = threading.Event()

    def run(self):
        logger.debug('import Started')
        self._start_funct()
    
    def init(self):
        logger.debug('Init Import Started')
        self._init_func(self._source)

    def stop(self):
        self._stop_func()
        self._stop_event.set()

class windowHelpers():

    def getThirdUi():
        global Third
        return Third
    
    def initLog(source  , importFunct , stopFunct , start):
        
        logging.basicConfig(level=logging.DEBUG)
        root = tk.Tk()
        app = App(root , source )
        # global func_init
        # func_init = importFunct
        # global func_stop
        # func_stop = stopFunct
        global importProcInst
        global Third
        Third = app.third
        importProcInst = ImportProc(source , importFunct , stopFunct, start )
        
        
        app.root.mainloop()

    def callableFunct():
        # global clock
        # clock = Clock()
        # clock.start()
        button['state'] = DISABLED
        # func_init()
        importProcInst.init()
        importProcInst.start()
        
    def importFunctDemo():
        logger.debug('Doin Stuff started')

    def logIntoWindow(stuff , ind = False):
        if ind:
            level = logging.ERROR
            logger.log(level , stuff)
        else:
            level = logging.INFO
            logger.log(level , stuff)


