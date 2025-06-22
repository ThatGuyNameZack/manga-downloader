import sys
import os
import json
import requests
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtNetwork import *
import threading
from concurrent.futures import ThreadPoolExecutor

# Local imports
from api_utils import search_manga, get_chapters
from download_utils import download_chapter_images
from page_order import rename_images_in_folder
from config import LIMIT, OFFSET, DOWNLOAD_PATH

LOG_PATH = "log.json"

class ImageLoader(QThread):
    """Thread for loading images asynchronously"""
    imageLoaded = pyqtSignal(str, QPixmap)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def run(self):
        try:
            response = requests.get(self.url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                if not pixmap.isNull():
                    # Scale to reasonable size
                    scaled_pixmap = pixmap.scaled(150, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.imageLoaded.emit(self.url, scaled_pixmap)
        except Exception as e:
            print(f"Failed to load image: {e}")

class SearchWorker(QThread):
    """Thread for search operations"""
    searchCompleted = pyqtSignal(list)
    searchFailed = pyqtSignal(str)
    
    def __init__(self, query):
        super().__init__()
        self.query = query
        
    def run(self):
        try:
            results = search_manga(self.query, limit=15)
            self.searchCompleted.emit(results)
        except Exception as e:
            self.searchFailed.emit(str(e))

class DownloadWorker(QThread):
    """Thread for download operations"""
    downloadProgress = pyqtSignal(str)
    downloadCompleted = pyqtSignal(int)
    downloadFailed = pyqtSignal(str)
    
    def __init__(self, manga, chapter_range, download_path):
        super().__init__()
        self.manga = manga
        self.chapter_range = chapter_range
        self.download_path = download_path
        
    def run(self):
        try:
            title = self.manga['title']
            manga_id = self.manga['id']
            
            # Load log
            log = self.load_log()
            
            self.downloadProgress.emit(f"Starting download for {title}...")
            
            # Parse chapter range
            chapter_from = chapter_to = None
            if self.chapter_range:
                if '-' in self.chapter_range:
                    try:
                        chapter_from, chapter_to = map(float, self.chapter_range.split('-'))
                    except ValueError:
                        self.downloadFailed.emit("Invalid chapter range format!")
                        return
                else:
                    try:
                        chapter_from = float(self.chapter_range)
                    except ValueError:
                        self.downloadFailed.emit("Invalid chapter number!")
                        return
            
            offset = OFFSET
            limit = min(LIMIT, 50)
            downloaded_count = 0
            
            while True:
                chapters = get_chapters(manga_id, limit=limit, offset=offset, 
                                     chapter_from=chapter_from, chapter_to=chapter_to)
                if not chapters:
                    break
                    
                for chapter in chapters:
                    chapter_number = chapter["attributes"].get("chapter", "Unknown")
                    self.downloadProgress.emit(f"Downloading chapter {chapter_number}...")
                    
                    chapter_id = chapter["id"]
                    if chapter_id in log["downloaded_chapters"]:
                        continue
                        
                    folder = download_chapter_images(chapter, title, self.download_path)
                    if folder:
                        rename_images_in_folder(folder)
                        log["downloaded_chapters"].append(chapter_id)
                        self.save_log(log)
                        downloaded_count += 1
                
                offset += limit
                if len(chapters) < limit:
                    break
                    
            self.downloadCompleted.emit(downloaded_count)
            
        except Exception as e:
            self.downloadFailed.emit(str(e))
    
    def load_log(self):
        if not os.path.exists(LOG_PATH):
            return {"downloaded_chapters": []}
        try:
            with open(LOG_PATH, "r") as f:
                return json.load(f)
        except:
            return {"downloaded_chapters": []}
    
    def save_log(self, log):
        try:
            with open(LOG_PATH, "w") as f:
                json.dump(log, f, indent=2)
        except Exception as e:
            print(f"Failed to save log: {e}")

class MangaCard(QWidget):
    """Custom widget for manga display"""
    downloadRequested = pyqtSignal(dict)
    
    def __init__(self, manga_data):
        super().__init__()
        self.manga_data = manga_data
        self.image_loader = None
        self.setupUI()
        
    def setupUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Card frame
        self.setStyleSheet("""
            MangaCard {
                background-color: #1c2541;
                border: 2px solid #3a506b;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        # Title
        title_label = QLabel(self.manga_data['title'])
        title_label.setStyleSheet("""
            QLabel {
                color: #6fffe9;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                padding: 5px;
            }
        """)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Image placeholder
        self.image_label = QLabel("Loading...")
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #3a506b;
                color: #6fffe9;
                border: 1px solid #5bc0be;
                border-radius: 4px;
                padding: 20px;
            }
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(150, 200)
        layout.addWidget(self.image_label, 0, Qt.AlignCenter)
        
        # Download button
        download_btn = QPushButton("Download This Manga")
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #5bc0be;
                color: #0b132b;
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 12px 25px;
            }
            QPushButton:hover {
                background-color: #6fffe9;
            }
            QPushButton:pressed {
                background-color: #4a9997;
            }
        """)
        download_btn.clicked.connect(lambda: self.downloadRequested.emit(self.manga_data))
        layout.addWidget(download_btn, 0, Qt.AlignCenter)
        
        self.setLayout(layout)
        
        # Load image
        if self.manga_data['cover_url']:
            self.load_image()
    
    def load_image(self):
        if self.image_loader and self.image_loader.isRunning():
            return
            
        self.image_loader = ImageLoader(self.manga_data['cover_url'])
        self.image_loader.imageLoaded.connect(self.on_image_loaded)
        self.image_loader.start()
    
    def on_image_loaded(self, url, pixmap):
        if url == self.manga_data['cover_url']:
            self.image_label.setPixmap(pixmap)
            self.image_label.setText("")

class MangaDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_download_path = DOWNLOAD_PATH
        self.search_worker = None
        self.download_worker = None
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.setupUI()
        self.setWindowTitle("Manga Downloader - PyQt5")
        self.setGeometry(100, 100, 900, 800)
        
    def setupUI(self):
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b132b;
                color: #6fffe9;
            }
            QLabel {
                color: #6fffe9;
            }
            QLineEdit {
                background-color: #3a506b;
                color: #6fffe9;
                border: 2px solid #5bc0be;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #6fffe9;
            }
            QPushButton {
                background-color: #5bc0be;
                color: #0b132b;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #6fffe9;
            }
            QPushButton:pressed {
                background-color: #4a9997;
            }
            QScrollArea {
                border: none;
                background-color: #0b132b;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Manga Downloader")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #6fffe9;
                padding: 20px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Download path section
        path_layout = QHBoxLayout()
        path_btn = QPushButton("Choose Download Folder")
        path_btn.clicked.connect(self.select_download_path)
        path_layout.addWidget(path_btn)
        
        self.path_label = QLabel(f"Download to: {self.current_download_path}")
        self.path_label.setStyleSheet("color: #5bc0be; font-size: 10px;")
        self.path_label.setWordWrap(True)
        path_layout.addWidget(self.path_label, 1)
        
        layout.addLayout(path_layout)
        
        # Search section
        search_label = QLabel("Search Manga:")
        search_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(search_label)
        
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Type manga name...")
        self.search_entry.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_entry)
        
        # Chapter range section
        chapter_label = QLabel("Chapter Range (optional - e.g., '1' or '1-5'):")
        chapter_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(chapter_label)
        
        self.chapter_entry = QLineEdit()
        self.chapter_entry.setPlaceholderText("e.g., 1 or 1-5")
        layout.addWidget(self.chapter_entry)
        
        # Status label
        self.status_label = QLabel("Ready. Type a manga name to search.")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6fffe9;
                font-style: italic;
                font-size: 12px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Results area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout()
        self.results_layout.setSpacing(15)
        self.results_widget.setLayout(self.results_layout)
        
        self.scroll_area.setWidget(self.results_widget)
        layout.addWidget(self.scroll_area, 1)
        
        central_widget.setLayout(layout)
        
        # Create progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
    
    def select_download_path(self):
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Download Folder", 
            self.current_download_path
        )
        if folder:
            self.current_download_path = folder
            self.path_label.setText(f"Download to: {self.current_download_path}")
    
    def on_search_changed(self):
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms delay
    
    def perform_search(self):
        query = self.search_entry.text().strip()
        if not query:
            self.clear_results()
            return
        
        self.status_label.setText("Searching...")
        self.clear_results()
        
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.terminate()
        
        self.search_worker = SearchWorker(query)
        self.search_worker.searchCompleted.connect(self.on_search_completed)
        self.search_worker.searchFailed.connect(self.on_search_failed)
        self.search_worker.start()
    
    def on_search_completed(self, results):
        if not results:
            self.status_label.setText("No manga found.")
            return
        
        self.status_label.setText(f"Found {len(results)} manga")
        
        for manga in results:
            card = MangaCard(manga)
            card.downloadRequested.connect(self.start_download)
            self.results_layout.addWidget(card)
        
        # Add stretch to push cards to top
        self.results_layout.addStretch()
    
    def on_search_failed(self, error):
        self.status_label.setText("Search failed!")
        QMessageBox.critical(self, "Error", f"Search failed: {error}")
    
    def clear_results(self):
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def start_download(self, manga):
        if self.download_worker and self.download_worker.isRunning():
            QMessageBox.information(self, "Info", "A download is already in progress!")
            return
        
        chapter_range = self.chapter_entry.text().strip()
        if chapter_range == "e.g., 1 or 1-5":
            chapter_range = ""
        
        self.download_worker = DownloadWorker(manga, chapter_range, self.current_download_path)
        self.download_worker.downloadProgress.connect(self.on_download_progress)
        self.download_worker.downloadCompleted.connect(self.on_download_completed)
        self.download_worker.downloadFailed.connect(self.on_download_failed)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.download_worker.start()
    
    def on_download_progress(self, message):
        self.status_label.setText(message)
    
    def on_download_completed(self, count):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Download complete! {count} chapters downloaded.")
        QMessageBox.information(self, "Done", f"Downloaded {count} chapters!")
    
    def on_download_failed(self, error):
        self.progress_bar.setVisible(False)
        self.status_label.setText("Download failed!")
        QMessageBox.critical(self, "Error", f"Download failed: {error}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Manga Downloader")
    app.setOrganizationName("MangaDownloader")
    
    # Apply dark theme
    app.setStyle('Fusion')
    
    window = MangaDownloader()
    window.show()
    
    sys.exit(app.exec_())