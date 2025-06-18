import os
import json
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from PIL import Image, ImageTk
import requests
from io import BytesIO
import threading
import time

# Local imports
from api_utils import search_manga, get_chapters
from download_utils import download_chapter_images
from page_order import rename_images_in_folder
from config import LIMIT, OFFSET, DOWNLOAD_PATH

LOG_PATH = "log.json"

# Your color scheme
COLORS = {
    'oxford_blue': '#0b132b',      # main background
    'space_cadet': '#1c2541',     # secondary background
    'yinmn_blue': '#3a506b',      # frames, etc
    'verdigris': '#5bc0be',       # buttons
    'fluorescent_cyan': '#6fffe9'  # button text, highlights
}

# Global variables
current_download_path = DOWNLOAD_PATH
search_after_id = None

def load_log():
    if not os.path.exists(LOG_PATH):
        return {"downloaded_chapters": []}
    with open(LOG_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"downloaded_chapters": []}

def save_log(log):
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=4)

def select_download_path():
    global current_download_path
    folder = filedialog.askdirectory(
        title="Select Download Folder",
        initialdir=current_download_path
    )
    if folder:
        current_download_path = folder
        path_label.config(text=f"Download to: {current_download_path}")

def start_download(manga):
    def download_thread():
        try:
            title = manga['title']
            manga_id = manga['id']
            log = load_log()

            status_label.config(text=f"Starting download for {title}...")
            status_label.update_idletasks()

            range_input = chapter_range_entry.get().strip()
            if range_input == "e.g., 1 or 1-5":
                range_input = ""
            
            chapter_from = chapter_to = None
            if range_input:
                if '-' in range_input:
                    try:
                        chapter_from, chapter_to = map(float, range_input.split('-'))
                    except ValueError:
                        messagebox.showerror("Error", "Invalid chapter range format!")
                        return
                else:
                    try:
                        chapter_from = float(range_input)
                    except ValueError:
                        messagebox.showerror("Error", "Invalid chapter number!")
                        return

            offset = OFFSET
            limit = LIMIT
            downloaded_count = 0

            while True:
                chapters = get_chapters(manga_id, limit=limit, offset=offset, chapter_from=chapter_from, chapter_to=chapter_to)
                if not chapters:
                    break

                for chapter in chapters:
                    chapter_number = chapter["attributes"].get("chapter", "Unknown")
                    status_label.config(text=f"Downloading chapter {chapter_number}...")
                    status_label.update_idletasks()
                    
                    chapter_id = chapter["id"]
                    if chapter_id in log["downloaded_chapters"]:
                        continue

                    folder = download_chapter_images(chapter, title, current_download_path)
                    if folder:
                        rename_images_in_folder(folder)
                        log["downloaded_chapters"].append(chapter_id)
                        save_log(log)
                        downloaded_count += 1

                offset += limit
                if len(chapters) < limit:
                    break

            status_label.config(text=f"Download complete! {downloaded_count} chapters downloaded.")
            messagebox.showinfo("Done", f"Downloaded {downloaded_count} chapters for {title}!")
            
        except Exception as e:
            status_label.config(text="Download failed!")
            messagebox.showerror("Error", f"Download failed: {str(e)}")

    # Run download in separate thread to prevent GUI freezing
    thread = threading.Thread(target=download_thread)
    thread.daemon = True
    thread.start()

def delayed_search():
    global search_after_id
    if search_after_id:
        root.after_cancel(search_after_id)
    search_after_id = root.after(500, perform_search)  # Wait 500ms after typing stops

def perform_search():
    # Clear previous results
    for widget in results_frame.winfo_children():
        widget.destroy()

    query = search_entry.get().strip()
    if not query or query == "Type manga name...":
        return

    status_label.config(text="Searching...")
    status_label.update_idletasks()

    try:
        results = search_manga(query)
        if not results:
            status_label.config(text="No manga found.")
            return

        status_label.config(text=f"Found {len(results)} manga")
        
        for manga in results:
            create_manga_card(manga)
            
    except Exception as e:
        status_label.config(text="Search failed!")
        messagebox.showerror("Error", f"Search failed: {str(e)}")

def create_manga_card(manga):
    # Themed manga frame
    manga_frame = tk.Frame(
        results_frame, 
        bg=COLORS['space_cadet'],
        padx=15, 
        pady=15, 
        borderwidth=2, 
        relief="solid",
        highlightbackground=COLORS['yinmn_blue'],
        highlightthickness=1
    )
    manga_frame.pack(pady=10, fill="x", padx=15)

    # Title label with theme
    title_label = tk.Label(
        manga_frame, 
        text=manga['title'], 
        font=("Arial", 14, "bold"),
        bg=COLORS['space_cadet'],
        fg=COLORS['fluorescent_cyan'],
        wraplength=500
    )
    title_label.pack(pady=(0, 10))

    # Center container for image and button
    center_frame = tk.Frame(manga_frame, bg=COLORS['space_cadet'])
    center_frame.pack(expand=True)

    # Cover image (centered)
    if manga['cover_url']:
        try:
            response = requests.get(manga['cover_url'], timeout=10)
            img_data = Image.open(BytesIO(response.content))
            img_data.thumbnail((150, 200))  # Slightly larger
            photo = ImageTk.PhotoImage(img_data)
            
            label_img = tk.Label(center_frame, image=photo, bg=COLORS['space_cadet'])
            label_img.image = photo  # Keep reference
            label_img.pack(pady=(0, 15))
        except Exception as e:
            # Show placeholder if image fails
            placeholder = tk.Label(
                center_frame,
                text="No Image\nAvailable",
                bg=COLORS['yinmn_blue'],
                fg=COLORS['fluorescent_cyan'],
                font=('Arial', 12),
                width=15,
                height=8,
                relief='solid',
                borderwidth=1
            )
            placeholder.pack(pady=(0, 15))

    # Download button (centered)
    download_btn = tk.Button(
        center_frame, 
        text="Download This Manga", 
        command=lambda m=manga: start_download(m),
        bg=COLORS['verdigris'],
        fg=COLORS['oxford_blue'],
        font=('Arial', 12, 'bold'),
        relief='flat',
        padx=25,
        pady=12,
        activebackground=COLORS['fluorescent_cyan'],
        activeforeground=COLORS['oxford_blue'],
        cursor='hand2'
    )
    download_btn.pack()

# GUI Setup
root = tk.Tk()
root.title("Manga Downloader")
root.geometry("800x900")
root.configure(bg=COLORS['oxford_blue'])

# Title header
title_header = tk.Label(
    root,
    text="Manga Downloader",
    font=("Arial", 20, "bold"),
    bg=COLORS['oxford_blue'],
    fg=COLORS['fluorescent_cyan'],
    pady=20
)
title_header.pack()

# Download path section
path_frame = tk.Frame(root, bg=COLORS['oxford_blue'])
path_frame.pack(pady=10)

path_button = tk.Button(
    path_frame,
    text="Choose Download Folder",
    command=select_download_path,
    bg=COLORS['yinmn_blue'],
    fg=COLORS['fluorescent_cyan'],
    font=('Arial', 10, 'bold'),
    relief='flat',
    padx=15,
    pady=5,
    activebackground=COLORS['verdigris'],
    activeforeground=COLORS['oxford_blue'],
    cursor='hand2'
)
path_button.pack()

path_label = tk.Label(
    path_frame,
    text=f"Download to: {current_download_path}",
    font=("Arial", 9),
    bg=COLORS['oxford_blue'],
    fg=COLORS['verdigris'],
    wraplength=600
)
path_label.pack(pady=(5, 0))

# Search frame with theme
search_frame = tk.Frame(root, bg=COLORS['oxford_blue'])
search_frame.pack(pady=20)

# Search label
search_label = tk.Label(
    search_frame,
    text="Search Manga (type any letters for suggestions):",
    font=("Arial", 12),
    bg=COLORS['oxford_blue'],
    fg=COLORS['verdigris']
)
search_label.pack(pady=(0, 10))

# Search input
search_entry = tk.Entry(
    search_frame, 
    width=40,
    font=("Arial", 14),
    bg=COLORS['yinmn_blue'],
    fg=COLORS['fluorescent_cyan'],
    insertbackground=COLORS['verdigris'],
    relief='flat',
    bd=2
)
search_entry.insert(0, "Type manga name...")
search_entry.pack(ipady=8)

# Chapter range section
chapter_frame = tk.Frame(root, bg=COLORS['oxford_blue'])
chapter_frame.pack(pady=15)

chapter_label = tk.Label(
    chapter_frame,
    text="Chapter Range (optional - leave blank for all chapters):",
    font=("Arial", 12),
    bg=COLORS['oxford_blue'],
    fg=COLORS['verdigris']
)
chapter_label.pack(pady=(0, 5))

chapter_range_entry = tk.Entry(
    chapter_frame, 
    width=30,
    font=("Arial", 12),
    bg=COLORS['yinmn_blue'],
    fg=COLORS['fluorescent_cyan'],
    insertbackground=COLORS['verdigris'],
    relief='flat',
    bd=2
)
chapter_range_entry.insert(0, "e.g., 1 or 1-5")
chapter_range_entry.pack(ipady=5)

# Status label
status_label = tk.Label(
    root,
    text="Ready. Type a manga name to search.",
    font=("Arial", 11, "italic"),
    bg=COLORS['oxford_blue'],
    fg=COLORS['fluorescent_cyan']
)
status_label.pack(pady=10)

# Results container with scrollbar
results_container = tk.Frame(root, bg=COLORS['oxford_blue'])
results_container.pack(fill="both", expand=True, padx=15, pady=10)

# Canvas and scrollbar for results
canvas = tk.Canvas(results_container, bg=COLORS['oxford_blue'], highlightthickness=0)
scrollbar = ttk.Scrollbar(results_container, orient="vertical", command=canvas.yview)
results_frame = tk.Frame(canvas, bg=COLORS['oxford_blue'])

results_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=results_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Style the scrollbar
style = ttk.Style()
style.theme_use('clam')
style.configure("Vertical.TScrollbar", 
                background=COLORS['yinmn_blue'],
                troughcolor=COLORS['space_cadet'],
                bordercolor=COLORS['yinmn_blue'],
                arrowcolor=COLORS['fluorescent_cyan'],
                darkcolor=COLORS['yinmn_blue'],
                lightcolor=COLORS['verdigris'])

# Bind mousewheel to canvas
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

# Search functionality
def on_search_change(event=None):
    delayed_search()

def clear_search_placeholder(event):
    if search_entry.get() == "Type manga name...":
        search_entry.delete(0, tk.END)
        search_entry.config(fg=COLORS['fluorescent_cyan'])

def restore_search_placeholder(event):
    if not search_entry.get():
        search_entry.insert(0, "Type manga name...")
        search_entry.config(fg=COLORS['verdigris'])

# Bind search events
search_entry.bind('<KeyRelease>', on_search_change)
search_entry.bind("<FocusIn>", clear_search_placeholder)
search_entry.bind("<FocusOut>", restore_search_placeholder)
search_entry.config(fg=COLORS['verdigris'])

# Chapter range placeholder handling
def clear_chapter_placeholder(event):
    if chapter_range_entry.get() == "e.g., 1 or 1-5":
        chapter_range_entry.delete(0, tk.END)
        chapter_range_entry.config(fg=COLORS['fluorescent_cyan'])

def restore_chapter_placeholder(event):
    if not chapter_range_entry.get():
        chapter_range_entry.insert(0, "e.g., 1 or 1-5")
        chapter_range_entry.config(fg=COLORS['verdigris'])

chapter_range_entry.bind("<FocusIn>", clear_chapter_placeholder)
chapter_range_entry.bind("<FocusOut>", restore_chapter_placeholder)
chapter_range_entry.config(fg=COLORS['verdigris'])

root.mainloop()