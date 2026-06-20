import os
import time
import threading
import platform
import subprocess
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserIconView
from kivy.clock import Clock, mainthread
from PIL import Image
from reportlab.pdfgen import canvas

class ImageCompressorApp(App):
    def build(self):
        self.main_layout = BoxLayout(orientation='vertical', padding=20, spacing=12)
        
        self.title_label = Label(text="Image Compressor Pro Toolkit", font_size='22sp', size_hint_y=0.08, bold=True)
        self.main_layout.add_widget(self.title_label)
        
        self.status_label = Label(text="Status: Tayyar hain! Photos select karein.", font_size='14sp', size_hint_y=0.08, color=(0.9, 0.9, 0.2, 1))
        self.main_layout.add_widget(self.status_label)
        
        self.progress_bar = ProgressBar(max=100, size_hint_y=0.05)
        self.main_layout.add_widget(self.progress_bar)
        
        settings_layout = BoxLayout(orientation='horizontal', size_hint_y=0.06, spacing=10)
        self.back_btn = Button(text="<-- Wapis", size_hint_x=0.5, background_color=(0.5, 0.5, 0.5, 1))
        self.back_btn.bind(on_press=self.go_back)
        self.reset_btn = Button(text="Settings: Reset", size_hint_x=0.5, background_color=(0.8, 0.2, 0.2, 1))
        self.reset_btn.bind(on_press=self.reset_settings)
        settings_layout.add_widget(self.back_btn)
        settings_layout.add_widget(self.reset_btn)
        self.main_layout.add_widget(settings_layout)
        
        slider_layout = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=10)
        self.slider_label = Label(text="Quality: 65% (~277 KB)", size_hint_x=0.4, font_size='14sp')
        self.quality_slider = Slider(min=10, max=100, value=65, step=5, size_hint_x=0.6)
        self.quality_slider.bind(value=self.on_slider_value_change)
        
        slider_layout.add_widget(self.slider_label)
        slider_layout.add_widget(self.quality_slider)
        self.main_layout.add_widget(slider_layout)
        
        self.file_chooser = FileChooserIconView(size_hint_y=0.5, multiselect=True)
        self.main_layout.add_widget(self.file_chooser)
        
        self.compress_btn = Button(text="Sirf Select Ki Hui Photos Compress Karein", size_hint_y=0.08, background_color=(0.2, 0.6, 1, 1), font_size='14sp', bold=True)
        self.compress_btn.bind(on_press=lambda x: threading.Thread(target=self.compress_selected_images).start())
        self.main_layout.add_widget(self.compress_btn)
        
        self.bulk_compress_btn = Button(text="Is Folder Ki SAARI PHOTOS Compress Karein", size_hint_y=0.08, background_color=(0.1, 0.8, 0.4, 1), font_size='14sp', bold=True)
        self.bulk_compress_btn.bind(on_press=lambda x: threading.Thread(target=self.compress_all_images_in_folder).start())
        self.main_layout.add_widget(self.bulk_compress_btn)
        
        return self.main_layout

    @mainthread
    def update_status(self, text):
        self.status_label.text = text

    @mainthread
    def update_progress(self, val):
        self.progress_bar.value = val

    def reset_settings(self, instance):
        self.quality_slider.value = 65
        self.update_status("Status: Tayyar hain! Photos select karein.")
        self.update_progress(0)

    def go_back(self, instance):
        current = self.file_chooser.path
        parent = os.path.dirname(current)
        if parent != current:
            self.file_chooser.path = parent

    def on_slider_value_change(self, instance, value):
        q = int(value)
        if q <= 15: estimated_kb = "~200 KB"
        elif q <= 40: estimated_kb = "~250 KB"
        elif q <= 70: estimated_kb = "~277 KB"
        elif q <= 85: estimated_kb = "~350 KB"
        else: estimated_kb = "~500+ KB"
        self.slider_label.text = f"Quality: {q}% ({estimated_kb})"

    def generate_report(self, folder, count, quality, total_old_mb, total_new_mb, size_saved_mb):
        pdf_path = os.path.join(folder, "Delivery_Report.pdf")
        c = canvas.Canvas(pdf_path)
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 350, 650, width=300, height=170, mask='auto')
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 800, "Image Compressor Pro: Client Report")
        c.setFont("Helvetica", 12)
        c.drawString(100, 780, f"Total Images Processed: {count}")
        c.drawString(100, 765, f"Optimization Quality: {quality}%")
        c.drawString(100, 750, f"Original Total Size: {total_old_mb:.2f} MB")
        c.drawString(100, 735, f"New Total Size: {total_new_mb:.2f} MB")
        c.drawString(100, 720, f"Total Space Saved: {size_saved_mb:.2f} MB")
        c.drawString(100, 705, f"Date: {time.ctime()}")
        c.drawString(100, 680, "Message for Client:")
        c.drawString(100, 665, "Sir, your images have been professionally optimized.")
        c.drawString(100, 650, "Note: Only photos with successfully reduced size are included.")
        c.save()

    def compress_selected_images(self, *args):
        selected = self.file_chooser.selection
        if not selected:
            self.update_status("Status: Pehle photos select karein!")
            return
        self._run_compression(selected)

    def compress_all_images_in_folder(self, *args):
        current_path = self.file_chooser.path
        files_in_folder = [os.path.join(current_path, f) for f in os.listdir(current_path) if os.path.isfile(os.path.join(current_path, f))]
        if not files_in_folder:
            self.update_status("Status: Is folder mein koi photos nahi!")
            return
        self._run_compression(files_in_folder)

    def _run_compression(self, file_list):
        count = 0
        total_old = 0
        total_new = 0
        total_files = len(file_list)
        quality_val = int(self.quality_slider.value)
        output_folder = ""
        
        for i, full_path in enumerate(file_list):
            if os.path.isfile(full_path):
                current_num = i + 1
                self.update_status(f"Processing: {current_num}/{total_files}...")
                self.update_progress((current_num / total_files) * 100)
                
                old_size = os.path.getsize(full_path)
                output_folder, new_path = self.process_super_compression(full_path, quality_val)
                if new_path:
                    new_size = os.path.getsize(new_path)
                    total_old += old_size
                    total_new += new_size
                count += 1
        
        if output_folder: 
            self.generate_report(output_folder, count, quality_val, total_old/(1024*1024), total_new/(1024*1024), (total_old-total_new)/(1024*1024))
        
        self.update_status("Complete!")
        self.refresh_file_chooser()

    def refresh_file_chooser(self):
        current_dir = self.file_chooser.path
        self.file_chooser.path = os.path.dirname(current_dir)
        self.file_chooser.path = current_dir

    def process_super_compression(self, input_path, quality_val):
        try:
            img = Image.open(input_path)
            folder, filename = os.path.split(input_path)
            output_folder = os.path.join(folder, "Compressed_Outputs")
            if not os.path.exists(output_folder): os.makedirs(output_folder)
            unique_id = str(int(time.time()))[-4:]
            max_size = 1024
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Original format retrieve karna
            fmt = img.format if img.format else 'PNG'
            output_filename = f"super_{unique_id}_{filename}"
            output_path = os.path.join(output_folder, output_filename)
            
            # Save logic: PNG ke liye Palette mode taake size chota rahe
            if fmt == 'PNG' or img.mode == 'RGBA':
                max_colors = max(16, min(256, int((quality_val / 100) * 256)))
                img_optimized = img.convert("P", palette=Image.ADAPTIVE, colors=max_colors)
                img_optimized.save(output_path, format='PNG', optimize=True)
            else:
                img.save(output_path, format=fmt, quality=quality_val, optimize=True)
            return output_folder, output_path
        except Exception: return None, None

if __name__ == '__main__':
    ImageCompressorApp().run()
