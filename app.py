import json
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import requests

APP_DIR = Path(__file__).parent
CONFIG_PATH = APP_DIR / "config.json"
API_URL = "https://api.mistral.ai/v1/audio/transcriptions"
MODEL_ID = "voxtral-mini-2602"


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
        self.geometry("760x560")
        self.minsize(700, 520)

        self.config_data = load_config()
        self.file_path = tk.StringVar()
        self.api_key = tk.StringVar(value=self.config_data.get("api_key", ""))
        self.diarize = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Ready.")

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(main, text="Voxtral Mini Transcribe 2", font=("Segoe UI", 16, "bold"))
        header.pack(anchor=tk.W, pady=(0, 4))
        
        model_header = ttk.Label(main, text=f"Model: {MODEL_ID}", font=("Segoe UI", 10), foreground="gray")
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

        opts_frame = ttk.LabelFrame(main, text="Options")
        opts_frame.pack(fill=tk.X, pady=6)




        action_frame = ttk.Frame(main)
        action_frame.pack(fill=tk.X, pady=6)

        self.transcribe_btn = ttk.Button(action_frame, text="Generate transcript", command=self.start_transcription)
        self.transcribe_btn.pack(side=tk.RIGHT)

        clear_btn = ttk.Button(action_frame, text="Clear", command=self.clear_output)
        clear_btn.pack(side=tk.RIGHT, padx=8)

        output_frame = ttk.LabelFrame(main, text="Transcript")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=6)

        self.output = tk.Text(output_frame, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        status_frame = ttk.Frame(main)
        status_frame.pack(fill=tk.X, pady=(4, 0))
        
        status_label = ttk.Label(status_frame, textvariable=self.status)
        status_label.pack(side=tk.LEFT)
        
        model_label = ttk.Label(status_frame, text=f"Model: {MODEL_ID}", font=("Segoe UI", 8), foreground="gray")
        model_label.pack(side=tk.RIGHT)

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

        self.config_data["api_key"] = self.api_key.get().strip()
        save_config(self.config_data)

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

            self._update_output(text)
            self._set_status("Transcription complete.")
        except Exception as exc:
            self._set_status("Transcription failed.")
            messagebox.showerror("Error", str(exc))
        finally:
            self._enable_button()

    def _update_output(self, text):
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)

    def _set_status(self, message):
        self.status.set(message)

    def _enable_button(self):
        self.transcribe_btn.config(state=tk.NORMAL)


if __name__ == "__main__":
    app = App()
    app.mainloop()
