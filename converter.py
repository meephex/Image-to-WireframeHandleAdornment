import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageSequence
import base64
import json
import os
import math
import uuid
import struct
import threading
import urllib.request
import io

class ImageToLuaConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Image to wireframehandleadornment")
        self.root.geometry("700x750")
        self.root.configure(padx=20, pady=20)
        
        self.current_image = None
        self.is_processing = False

        controls_frame = tk.Frame(root)
        controls_frame.pack(fill="x", pady=(0, 10))

        tk.Button(controls_frame, text="Select Image File", command=self.select_file, width=18).pack(side="left", padx=(0, 10))
        tk.Button(controls_frame, text="Paste from Clipboard", command=self.paste_clipboard, width=18).pack(side="left")

        url_frame = tk.Frame(root)
        url_frame.pack(fill="x", pady=(0, 10))

        tk.Label(url_frame, text="URL:").pack(side="left", padx=(0, 5))
        self.url_entry = tk.Entry(url_frame)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.url_entry.insert(0, "https://...image.png")
        
        def start_url_thread():
            if self.is_processing: return
            self.is_processing = True
            self.set_buttons_state("disabled")
            threading.Thread(target=self.load_from_url, daemon=True).start()
            
        tk.Button(url_frame, text="Load URL", command=start_url_thread, width=12).pack(side="left")

        res_frame = tk.Frame(root)
        res_frame.pack(fill="x", pady=5)
        
        tk.Label(res_frame, text="Width:").pack(side="left", padx=(0, 5))
        self.width_entry = tk.Entry(res_frame, width=5)
        self.width_entry.insert(0, "64")
        self.width_entry.pack(side="left", padx=(0, 15))

        tk.Label(res_frame, text="Height:").pack(side="left", padx=(0, 5))
        self.height_entry = tk.Entry(res_frame, width=5)
        self.height_entry.insert(0, "64")
        self.height_entry.pack(side="left", padx=(0, 15))
        
        tk.Label(res_frame, text="Max Colors:").pack(side="left", padx=(0, 5))
        self.colors_entry = tk.Entry(res_frame, width=5)
        self.colors_entry.insert(0, "128")
        self.colors_entry.pack(side="left", padx=(0, 15))

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", pady=5)
        
        self.btn_raw = tk.Button(btn_frame, text="Convert (Raw Luau)", command=lambda: self.start_thread(self.convert_raw), bg="lightblue", font=("Arial", 10, "bold"))
        self.btn_raw.pack(side="left", padx=(0, 5))
        
        self.btn_json = tk.Button(btn_frame, text="Convert (Binary JSON)", command=lambda: self.start_thread(self.convert_binary_json), bg="lightgreen", font=("Arial", 10, "bold"))
        self.btn_json.pack(side="left", padx=(0, 5))
        
        self.btn_rbxmx = tk.Button(btn_frame, text="Export as .rbxmx", command=lambda: self.start_thread(self.export_rbxmx), bg="orange", font=("Arial", 10, "bold"))
        self.btn_rbxmx.pack(side="left")

        self.status_label = tk.Label(root, text="no image loaded.", fg="gray")
        self.status_label.pack(fill="x", pady=5)

        output_header = tk.Frame(root)
        output_header.pack(fill="x", pady=(10, 2))

        tk.Label(output_header, text="Output Luau Code:", fg="black").pack(side="left")
        self.copy_btn = tk.Button(output_header, text="Copy Code", command=self.copy_text, relief="flat", bg="#e0e0e0", width=12)
        self.copy_btn.pack(side="right")

        text_frame = tk.Frame(root, borderwidth=1, relief="solid")
        text_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.scrollbar = tk.Scrollbar(text_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.text_area = tk.Text(text_frame, yscrollcommand=self.scrollbar.set, wrap="none", font=("Consolas", 10))
        self.text_area.pack(fill="both", expand=True, padx=5, pady=5)
        self.scrollbar.config(command=self.text_area.yview)

    def set_buttons_state(self, state):
        self.btn_raw.config(state=state)
        self.btn_json.config(state=state)
        self.btn_rbxmx.config(state=state)

    def start_thread(self, target_function):
        if self.is_processing: return
        self.is_processing = True
        self.set_buttons_state("disabled")
        threading.Thread(target=target_function, daemon=True).start()

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif")]
        )
        if file_path:
            try:
                self.current_image = Image.open(file_path)
                self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}", fg="black")
                self.text_area.delete(1.0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"failed to load image:\n{e}")

    def paste_clipboard(self):
        try:
            import PIL.ImageGrab as ImageGrab
            img = ImageGrab.grabclipboard()
            if img:
                self.current_image = img
                self.status_label.config(text="loaded image from clipboard", fg="black")
                self.text_area.delete(1.0, tk.END)
            else:
                messagebox.showwarning("Clipboard", "no image found in clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"failed to read clipboard:\n{e}")

    def load_from_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "enter a url pls")
            self.is_processing = False
            self.set_buttons_state("normal")
            return
        
        self.root.after(0, lambda: self.status_label.config(text="Downloading image...", fg="blue"))
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                img_data = response.read()
                
            img = Image.open(io.BytesIO(img_data))
            self.current_image = img
            
            def update_ui():
                self.status_label.config(text="loaded image from url", fg="black")
                self.text_area.delete(1.0, tk.END)
                self.is_processing = False
                self.set_buttons_state("normal")
            self.root.after(0, update_ui)
            
        except Exception as e:
            def show_err():
                messagebox.showerror("Error", f"failed to download image:\n{e}")
                self.status_label.config(text="failed to load url", fg="red")
                self.is_processing = False
                self.set_buttons_state("normal")
            self.root.after(0, show_err)

    def process_frame(self, img_frame, width, height, max_colors):
        img_frame = img_frame.resize((width, height)).convert("RGB")
        if max_colors < 256:
            try:
                img_frame = img_frame.quantize(colors=max_colors, dither=Image.Dither.NONE).convert("RGB")
            except AttributeError:
                img_frame = img_frame.quantize(colors=max_colors, dither=0).convert("RGB")
            
        pixels_list = list(img_frame.getdata())
        pixels_data = {}
        for y in range(height):
            y_key = str(y + 1)
            pixels_data[y_key] = []
            x = 0
            while x < width:
                r, g, b = pixels_list[y * width + x]
                span_len = 1
                while x + span_len < width and pixels_list[y * width + (x + span_len)] == (r, g, b):
                    span_len += 1
                pixels_data[y_key].append([span_len, r, g, b])
                x += span_len
        return pixels_data

    def get_processed_data(self):
        if not self.current_image:
            messagebox.showwarning("Warning", "load an image first")
            return None

        try:
            w = int(self.width_entry.get())
            h = int(self.height_entry.get())
            c = int(self.colors_entry.get())
            if w <= 0 or h <= 0 or c <= 1: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "width height and color must be positive value")
            return None

        img = self.current_image
        is_animated = getattr(img, "is_animated", False)
        frames_data = []
        durations = []

        if is_animated:
            self.root.after(0, lambda: self.status_label.config(text="processing frames... 0%", fg="blue"))
            frame_count = 0
            total_frames = getattr(img, "n_frames", 1)
            for frame in ImageSequence.Iterator(img):
                duration_ms = frame.info.get('duration', 100)
                if duration_ms < 34:
                    duration_ms = 34
                durations.append(duration_ms)
                frames_data.append(self.process_frame(frame, w, h, c))
                frame_count += 1
                progress = math.floor((frame_count / total_frames) * 100)
                self.root.after(0, lambda p=progress, f=frame_count, t=total_frames: 
                    self.status_label.config(text=f"Processing GIF frames... {p}% ({f}/{t})", fg="blue"))
        else:
            frames_data = self.process_frame(img, w, h, c)

        return {
            "width": w,
            "height": h,
            "animated": is_animated,
            "durations": durations,
            "pixels": frames_data
        }

    def get_binary_data(self, data):
        pixels = data["pixels"]
        binary_data = b""
        
        def pack_frame(frame_dict):
            spans = []
            for y_key, row in frame_dict.items():
                y = int(y_key)
                for span in row:
                    spans.append(struct.pack("<HHBBB", y, span[0], span[1], span[2], span[3]))
            return struct.pack("<I", len(spans)) + b"".join(spans)
            
        if data["animated"]:
            for frame in pixels:
                binary_data += pack_frame(frame)
        else:
            binary_data += pack_frame(pixels)
            
        return base64.b64encode(binary_data).decode("utf-8")

    def convert_raw(self):
        data = self.get_processed_data()
        if not data: 
            self.is_processing = False
            self.set_buttons_state("normal")
            return
        
        is_animated = data["animated"]
        w, h = data["width"], data["height"]
        durations = data["durations"]
        pixels = data["pixels"]
        
        durations_lua = json.dumps(durations).replace('[', '{').replace(']', '}')

        lua_str = "local ImageData = {\n"
        lua_str += f"    width = {w},\n"
        lua_str += f"    height = {h},\n"
        lua_str += f"    animated = {str(is_animated).lower()},\n"
        lua_str += f"    durations = {durations_lua},\n"
        lua_str += "    pixels = {\n"
        
        if is_animated:
            for frame in pixels:
                lua_str += "        {\n"
                for y_key, row in frame.items():
                    lua_str += f"            ['{y_key}'] = {{"
                    spans_str = ",".join([f"{{{s[0]},{s[1]},{s[2]},{s[3]}}}" for s in row])
                    lua_str += spans_str
                    lua_str += "},\n"
                lua_str += "        },\n"
        else:
            for y_key, row in pixels.items():
                lua_str += f"        ['{y_key}'] = {{"
                spans_str = ",".join([f"{{{s[0]},{s[1]},{s[2]},{s[3]}}}" for s in row])
                lua_str += spans_str
                lua_str += "},\n"
            
        lua_str += "    }\n}\nreturn ImageData\n"

        def update_ui():
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, lua_str)
            self.status_label.config(text="raw luau complete", fg="green")
            self.is_processing = False
            self.set_buttons_state("normal")
        self.root.after(0, update_ui)

    def convert_binary_json(self):
        data = self.get_processed_data()
        if not data: 
            self.is_processing = False
            self.set_buttons_state("normal")
            return
        
        self.root.after(0, lambda: self.status_label.config(text="packing binary data...", fg="blue"))
        b64_data = self.get_binary_data(data)
        
        json_obj = {
            "w": data["width"],
            "h": data["height"],
            "a": data["animated"],
            "d": data["durations"],
            "data": b64_data
        }
        json_str = json.dumps(json_obj, separators=(',', ':'))
        
        def update_ui():
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, json_str)
            self.status_label.config(text=f"binary json complete (Size: {len(json_str)} chars)", fg="green")
            self.is_processing = False
            self.set_buttons_state("normal")
        self.root.after(0, update_ui)

    def export_rbxmx(self):
        data = self.get_processed_data()
        if not data: 
            self.is_processing = False
            self.set_buttons_state("normal")
            return
        
        w, h, a, durations = data["width"], data["height"], data["animated"], data["durations"]
        
        self.root.after(0, lambda: self.status_label.config(text="encoding binary data...", fg="blue"))
        b64_data = self.get_binary_data(data)
        
        chunk_size = 190000
        total_len = len(b64_data)
        num_chunks = math.ceil(total_len / chunk_size)
        
        chunks = [b64_data[i*chunk_size:(i+1)*chunk_size] for i in range(num_chunks)]
            
        def escape_xml(s):
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")
        def get_ref():
            return "RBX" + uuid.uuid4().hex.upper()
        
        self.root.after(0, lambda: self.status_label.config(text=f"generating xml structure ({num_chunks} chunks)...", fg="blue"))
            
        xml_str = '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">\n'
        xml_str += '\t<External>null</External>\n\t<External>nil</External>\n'
        xml_str += f'\t<Item class="Folder" referent="{get_ref()}">\n'
        xml_str += '\t\t<Properties>\n\t\t\t<string name="Name">ImageData</string>\n\t\t\t<BinaryString name="Tags"></BinaryString>\n\t\t</Properties>\n'
        
        def add_string_value(name, value):
            nonlocal xml_str
            xml_str += f'\t\t<Item class="StringValue" referent="{get_ref()}">\n'
            xml_str += f'\t\t\t<Properties>\n\t\t\t\t<string name="Name">{name}</string>\n\t\t\t\t<BinaryString name="Tags"></BinaryString>\n\t\t\t\t<string name="Value">{value}</string>\n\t\t\t</Properties>\n\t\t</Item>\n'
            
        add_string_value("Width", str(w))
        add_string_value("Height", str(h))
        add_string_value("Animated", str(a).lower())
        add_string_value("Durations", ",".join(str(d) for d in durations))
        add_string_value("TotalChunks", str(num_chunks))
        
        for i, chunk in enumerate(chunks):
            add_string_value(str(i+1), escape_xml(chunk))
            
        xml_str += '\t</Item>\n</roblox>'
        
        file_path = filedialog.asksaveasfilename(title="Save RBXMX", defaultextension=".rbxmx", filetypes=[("Roblox Model", "*.rbxmx")])
        
        def finish_ui():
            if file_path:
                self.status_label.config(text="writing file to disk...", fg="blue")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(xml_str)
                self.status_label.config(text=f"Exported {num_chunks} chunk(s) to .rbxmx", fg="green")
                messagebox.showinfo("Success", f"Saved to {file_path}\nyou can now import this into studio")
            self.is_processing = False
            self.set_buttons_state("normal")
        self.root.after(0, finish_ui)

    def copy_text(self):
        code = self.text_area.get(1.0, tk.END).strip()
        if not code:
            return
            
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        
        self.copy_btn.config(text="Copied!", bg="#c3e6cb")
        self.root.after(1500, lambda: self.copy_btn.config(text="Copy Code", bg="#e0e0e0"))

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageToLuaConverter(root)
    root.mainloop()