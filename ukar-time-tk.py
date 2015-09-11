#!/usr/bin/python3
import tkinter as tk, tkinter.font as tf
import sys, wave, time
from collections import deque
import pyaudio

if len(sys.argv) < 3:
    print("Usage: ukar-time audiofile.wav lyricsfile.syl > times.txt")
    sys.exit(-1)

class MyApp(tk.Frame):
    def __init__(self, audiofile, lyricsfile):
        tk.Frame.__init__(self, padx=10, pady=10)
        self.exited = False
        win = self.master
        win.title('uKar timing')
        win.geometry('400x150')
        win.bind_all("<Key>", self.keypress)
        win.protocol("WM_DELETE_WINDOW", self.exit)

        # Grid
        self.grid(sticky=tk.N+tk.S+tk.E+tk.W)
        top=self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, pad=10)
        self.rowconfigure(2, weight=1)

        # Widgets
        self.playpause = tk.Button(self, text='Play', command = self.play)
        self.playpause.grid(row=0, sticky=tk.N+tk.W)
        self.slider = tk.Scale(self, from_=0, to=1, resolution=0.0001, orient=tk.HORIZONTAL, showvalue = False)
        self.slider.bind("<Button-1>", self.sliderDrag)
        self.slider.bind("<ButtonRelease-1>", self.sliderSeek)
        self.slider.grid(row=1, sticky=tk.N+tk.E+tk.W)
        self.sliderUpd = True
        self.lyr = tk.Text(self, bg="black", fg = "white", undo = False, state = tk.DISABLED,
           font=tf.Font(family = "Arial", size=18)
        )
        self.lyr.tag_config("red", foreground="red")
        self.lyr.grid(row=2, sticky=tk.N+tk.S+tk.E+tk.W)

        # Sound stream
        self.wav = wave.open(audiofile, 'rb')
        self.pa = pyaudio.PyAudio()
        self.strm = self.pa.open(format=self.pa.get_format_from_width(self.wav.getsampwidth()),
            channels=self.wav.getnchannels(),
            rate=self.wav.getframerate(),
            frames_per_buffer = self.wav.getframerate()//100,
            output=True,
            start=False,
            stream_callback=self.__wave_callback)
        self.strmTime = self.strm.get_time()
        self.bps = self.wav.getsampwidth() * self.wav.getnchannels()
        self.dacTimes = deque()
        self.curPos = 0

        # Read lyrics
        self.lyrdata = []
        with open(lyricsfile, "rt") as f:
            for line in f:
                newline=""
                syl = [0]
                x = 0
                while x < len(line):
                    if line[x] == "-":
                        syl.append(len(newline))
                    else:
                        if line[x] == "\\": x += 1
                        newline += line[x]
                    x += 1
                if len(syl) == 1: continue
                #if len(newline) > 0 and syl[-1] != len(newline): syl.append(len(newline))
                self.lyrdata.append((newline, syl))

        self.lyrline = 0
        self.lyrseg = 0
        if len(self.lyrdata) > 0:
            self._setlyrics(self.lyrdata[self.lyrline][0])

    def sliderDrag(self, ev):
        self.sliderUpd = False

    def sliderSeek(self, ev):
        self.wav.setpos(int(self.slider.get()*self.wav.getnframes()))
        self.sliderUpd = True

    def _setlyrics(self, text):
        self.lyr.configure(state=tk.NORMAL)
        self.lyr.delete("1.0", tk.END)
        self.lyr.insert("1.0", text)
        self.lyr.configure(state=tk.DISABLED)
        self.focus_set()

    def __stream_finish(self):
        self.pause()

    def __wave_callback(self, in_data, frame_count, time_info, status):
        self.dacTimes.append((time_info['output_buffer_dac_time'], self.wav.tell()))
        curTime = time_info['current_time']
        while len(self.dacTimes) and self.dacTimes[0][0] >= curTime:
            self.curPos = self.dacTimes.popleft()[1]

        if self.sliderUpd: self.slider.set(self.curPos/self.wav.getnframes())
        data = self.wav.readframes(frame_count)
        status = pyaudio.paContinue
        if len(data)<frame_count*self.bps:
            status = pyaudio.paComplete
            self.master.after(5, self.__stream_finish)

        return (data, status)

    def play(self):
        self.strm.start_stream()
        self.playpause.configure(text="Pause", command=self.pause)

    def pause(self):
        self.strm.stop_stream()
        self.playpause.configure(text="Play", command=self.play)
        
    def keypress(self, event):
        tim = self.curPos*100//self.wav.getframerate()
        print("%i:%02i:%02i.%02i" % (tim//360000, tim//6000 % 60, tim // 100 % 60, tim % 100))
        sys.stdout.flush()
        self.lyrseg += 1
        if self.lyrseg == len(self.lyrdata[self.lyrline][1]):
            self.lyrseg = 0
            self.lyrline += 1
            self._setlyrics(self.lyrdata[self.lyrline][0])
        else:
            self.lyr.configure(state=tk.NORMAL)
            self.lyr.tag_add("red", "1.0", "1.%i" % self.lyrdata[self.lyrline][1][self.lyrseg])
            self.lyr.configure(state=tk.DISABLED)

    def exit(self, ev = None):
        if self.exited: return
        self.exited = True
        self.strm.close()
        self.master.destroy()
        self.pa.terminate()
        self.wav.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.exit()
        return False

with MyApp(sys.argv[1], sys.argv[2]) as app: app.mainloop()
