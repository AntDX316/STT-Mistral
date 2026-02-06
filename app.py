import asyncio
import base64
import json
import queue
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import requests
import sounddevice as sd
from mistralai import Mistral
from mistralai.extra.realtime import UnknownRealtimeEvent
from mistralai.models import (
    AudioFormat,
    RealtimeTranscriptionError,
    RealtimeTranscriptionSessionCreated,
    TranscriptionStreamDone,
    TranscriptionStreamTextDelta,
)

APP_DIR = Path(__file__).parent
CONFIG_PATH = APP_DIR / "config.json"
API_URL = "https://api.mistral.ai/v1/audio/transcriptions"
MODEL_ID = "voxtral-mini-2602"
REALTIME_MODEL_ID = "voxtral-mini-transcribe-realtime-2602"
SAMPLE_RATE = 16_000


def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_config(data):
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("STT-Mistral")
        self.geometry("820x600")
        self.minsize(740, 560)

        self.config_data = load_config()
        self.file_path = tk.StringVar()
        self.api_key = tk.StringVar(value=self.config_data.get("api_key", ""))
        self.status = tk.StringVar(value="Ready.")

        self._rt_running = False
        self._rt_thread = None
        self._rt_queue = queue.Queue(maxsize=200)
        self._rt_stop = threading.Event()

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(main, text="Voxtral Audio Transcribe", font=("Segoe UI", 16, "bold"))
        header.pack(anchor=tk.W, pady=(0, 4))

        model_header = ttk.Label(
            main,
            text=f"File model: {MODEL_ID} | Realtime model: {REALTIME_MODEL_ID}",
            font=("Segoe UI", 10),
            foreground="gray",
        )
        model_header.pack(anchor=tk.W, pady=(0, 12))

        file_frame = ttk.LabelFrame(main, text="Audio file")
        file_frame.pack(fill=tk.X, pady=6)

        file_entry = ttk.Entry(file_frame, textvariable=self.file_path)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 4), pady=8)

        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side=tk.LEFT, padx=(4, 8), pady=8)

        key_frame = ttk.LabelFrame(main, text="Mistral API key (stored locally)")
        key_frame.pack(fill=tk.X, pady=6)

        key_entry = ttk.Entry(key_frame, textvariable=self.api_key, show="*")
        key_entry.pack(fill=tk.X, padx=8, pady=8)

        options = ttk.LabelFrame(main, text="Realtime microphone")
        options.pack(fill=tk.X, pady=6)
        ttk.Label(options, text="Use your microphone to stream audio in real time.").pack(
            anchor=tk.W, padx=8, pady=6
        )

        action_frame = ttk.Frame(main)
        action_frame.pack(fill=tk.X, pady=6)

        self.transcribe_btn = ttk.Button(action_frame, text="Generate transcript", command=self.start_transcription)
        self.transcribe_btn.pack(side=tk.RIGHT)

        self.rt_start_btn = ttk.Button(action_frame, text="Start realtime", command=self.start_realtime)
        self.rt_start_btn.pack(side=tk.RIGHT, padx=8)

        self.rt_stop_btn = ttk.Button(action_frame, text="Stop realtime", command=self.stop_realtime, state=tk.DISABLED)
        self.rt_stop_btn.pack(side=tk.RIGHT)

        clear_btn = ttk.Button(action_frame, text="Clear", command=self.clear_output)
        clear_btn.pack(side=tk.LEFT)

        output_frame = ttk.LabelFrame(main, text="Transcript")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=6)

        self.output = tk.Text(output_frame, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        status_frame = ttk.Frame(main)
        status_frame.pack(fill=tk.X, pady=(4, 0))

        status_label = ttk.Label(status_frame, textvariable=self.status)
        status_label.pack(side=tk.LEFT)

    def browse_file(self):
        filetypes = [("Audio files", "*.wav *.mp3 *.m4a *.flac *.ogg"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Select audio file", filetypes=filetypes)
        if path:
            self.file_path.set(path)

    def clear_output(self):
        self.output.delete("1.0", tk.END)
        self.status.set("Ready.")

    def start_transcription(self):
        if not self.file_path.get():
            messagebox.showwarning("Missing file", "Please select an audio file.")
            return
        if not self.api_key.get().strip():
            messagebox.showwarning("Missing API key", "Please enter your Mistral API key.")
            return

        self._persist_api_key()
        self.transcribe_btn.config(state=tk.DISABLED)
        self.status.set("Uploading audio...")

        thread = threading.Thread(target=self._transcribe, daemon=True)
        thread.start()

    def _transcribe(self):
        try:
            headers = {"Authorization": f"Bearer {self.api_key.get().strip()}"}
            data = {
                "model": MODEL_ID,
                "diarize": "false",
            }

            with open(self.file_path.get(), "rb") as f:
                files = {"file": (Path(self.file_path.get()).name, f)}
                response = requests.post(API_URL, headers=headers, data=data, files=files, timeout=120)

            if response.status_code != 200:
                raise RuntimeError(response.text)

            payload = response.json()
            text = payload.get("text") or payload.get("transcription") or json.dumps(payload, indent=2)

            self._set_output(text)
            self._set_status("Transcription complete.")
        except Exception as exc:
            self._set_status("Transcription failed.")
            self._show_error(str(exc))
        finally:
            self._enable_button()

    def start_realtime(self):
        if self._rt_running:
            return
        if not self.api_key.get().strip():
            messagebox.showwarning("Missing API key", "Please enter your Mistral API key.")
            return

        self._persist_api_key()
        self._rt_running = True
        self._rt_stop.clear()
        self._rt_queue = queue.Queue(maxsize=200)

        self.rt_start_btn.config(state=tk.DISABLED)
        self.rt_stop_btn.config(state=tk.NORMAL)
        self.transcribe_btn.config(state=tk.DISABLED)
        self._set_status("Starting realtime session...")

        self._rt_thread = threading.Thread(target=self._run_realtime, daemon=True)
        self._rt_thread.start()

    def stop_realtime(self):
        if not self._rt_running:
            return
        self._rt_running = False
        self._rt_stop.set()
        self._set_status("Stopping realtime...")

    def _run_realtime(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._realtime_main())
        except Exception as exc:
            self._show_error(str(exc))
        finally:
            loop.stop()
            loop.close()
            self._rt_running = False
            self._set_status("Realtime stopped.")
            self._enable_realtime_buttons()

    async def _realtime_main(self):
        try:
            client = Mistral(api_key=self.api_key.get().strip())
            audio_format = AudioFormat(encoding="pcm_s16le", sample_rate=SAMPLE_RATE)

            def callback(indata, frames, time_info, status):
                if status:
                    return
                if not self._rt_running:
                    return
                try:
                    self._rt_queue.put_nowait(bytes(indata))
                except queue.Full:
                    pass

            self._set_status("Listening... (realtime)")

            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=int(SAMPLE_RATE * 0.1),
                callback=callback,
            ):
                async for event in client.audio.realtime.transcribe_stream(
                    audio_stream=self._audio_stream_generator(),
                    model=REALTIME_MODEL_ID,
                    audio_format=audio_format,
                ):
                    if not self._rt_running or self._rt_stop.is_set():
                        break

                    if isinstance(event, RealtimeTranscriptionSessionCreated):
                        self._set_status("Connected to Mistral realtime.")
                    elif isinstance(event, TranscriptionStreamTextDelta):
                        delta = event.text
                        if delta:
                            self._append_output(delta)
                    elif isinstance(event, TranscriptionStreamDone):
                        break
                    elif isinstance(event, RealtimeTranscriptionError):
                        raise RuntimeError(event.error)
                    elif isinstance(event, UnknownRealtimeEvent):
                        continue
        except Exception as exc:
            self._show_error(str(exc))
        finally:
            self._rt_running = False

    async def _audio_stream_generator(self):
        while self._rt_running and not self._rt_stop.is_set():
            try:
                chunk = self._rt_queue.get_nowait()
                yield chunk
            except queue.Empty:
                await asyncio.sleep(0.01)

    def _persist_api_key(self):
        self.config_data["api_key"] = self.api_key.get().strip()
        save_config(self.config_data)

    def _set_output(self, text):
        def _update():
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, text)
        self.after(0, _update)

    def _append_output(self, text):
        def _update():
            self.output.insert(tk.END, text)
            self.output.see(tk.END)
        self.after(0, _update)

    def _set_status(self, message):
        self.after(0, lambda: self.status.set(message))

    def _enable_button(self):
        self.after(0, lambda: self.transcribe_btn.config(state=tk.NORMAL))

    def _enable_realtime_buttons(self):
        def _update():
            self.rt_start_btn.config(state=tk.NORMAL)
            self.rt_stop_btn.config(state=tk.DISABLED)
            self.transcribe_btn.config(state=tk.NORMAL)
        self.after(0, _update)

    def _show_error(self, message):
        self.after(0, lambda: messagebox.showerror("Error", message))


if __name__ == "__main__":
    app = App()
    app.mainloop()
