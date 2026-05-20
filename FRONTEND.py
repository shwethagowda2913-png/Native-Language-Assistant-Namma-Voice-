import tkinter as tk
from tkinter import ttk, messagebox, font
from PIL import Image, ImageTk, ImageFilter, ImageEnhance
import requests
import json
import threading
from datetime import datetime
import time
import os
import speech_recognition as sr
import pyttsx3

class ServiceAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 NammaVoice")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        
        # API base URL
        self.api_base = "http://localhost:5000/api"
        
        # User session data
        self.user_data = {}
        self.current_language = 'English'
        self.translations = {}
        self.session = requests.Session()
        
        # Voice components - Initialize only if libraries available
        self.voice_enabled = True
        try:
            self.recognizer = sr.Recognizer()
            self.tts_engine = pyttsx3.init()
            self.is_listening = False
            self.setup_tts()
        except Exception as e:
            print(f"Voice features disabled: {e}")
            self.voice_enabled = False
        
        # Language code mapping for speech recognition
        self.lang_codes = {
            'English': 'en-IN',
            'Hindi': 'hi-IN',
            'Kannada': 'kn-IN',
            'Tamil': 'ta-IN',
            'Telugu': 'te-IN',
            'Bengali': 'bn-IN'
        }
        
        # Fonts
        self.title_font = font.Font(family="Arial", size=20, weight="bold")
        self.subtitle_font = font.Font(family="Arial", size=13, weight="bold")
        self.label_font = font.Font(family="Arial", size=11)
        self.button_font = font.Font(family="Arial", size=11, weight="bold")
        
        # Colors
        self.primary_color = '#3498db'
        self.success_color = '#27ae60'
        self.danger_color = '#e74c3c'
        self.warning_color = '#f39c12'
        self.dark_color = '#2c3e50'
        self.light_color = '#ecf0f1'
        self.voice_color = '#9b59b6'
        
        # Setup background
        self.setup_background()
        
        # Initialize UI
        self.setup_ui()
        self.load_translations()
        self.check_backend_connection()
    
    def setup_tts(self):
        """Configure text-to-speech engine"""
        if not self.voice_enabled:
            return
        try:
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"TTS setup error: {e}")
    
    def speak(self, text):
        """Text-to-speech in separate thread"""
        if not self.voice_enabled:
            return
        def speak_thread():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"Speech error: {e}")
        threading.Thread(target=speak_thread, daemon=True).start()
    
    def listen(self, callback, prompt_text="Listening..."):
        """Speech recognition"""
        if not self.voice_enabled:
            messagebox.showinfo("Voice Disabled", "Voice features not available. Please install: pip install SpeechRecognition pyttsx3 pyaudio")
            return
            
        if self.is_listening:
            return
        
        self.is_listening = True
        self.update_status(prompt_text, self.voice_color)
        self.speak(prompt_text)
        
        def listen_thread():
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                lang_code = self.lang_codes.get(self.current_language, 'en-IN')
                text = self.recognizer.recognize_google(audio, language=lang_code)
                
                self.root.after(0, lambda: callback(text))
                self.root.after(0, lambda: self.update_status(f"Heard: {text}", self.success_color))
                
            except sr.WaitTimeoutError:
                self.root.after(0, lambda: self.update_status("No speech detected", self.warning_color))
            except sr.UnknownValueError:
                self.root.after(0, lambda: self.update_status("Could not understand", self.danger_color))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", self.danger_color))
            finally:
                self.is_listening = False
        
        threading.Thread(target=listen_thread, daemon=True).start()
    
    def setup_background(self):
        """Setup background image with blur effect"""
        try:
            possible_paths = [
                "download.jpeg",
                "download.jpg",
                "background.jpeg",
                "background.jpg",
                r"C:\Users\Shwetha M K\OneDrive\Desktop\BIT\Native Language Assistant\download.jpeg"
            ]
            
            bg_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    bg_path = path
                    break
            
            if bg_path and os.path.exists(bg_path):
                bg_image = Image.open(bg_path)
                bg_image = bg_image.resize((1920, 1080), Image.Resampling.LANCZOS)
                bg_image = bg_image.filter(ImageFilter.GaussianBlur(5))
                enhancer = ImageEnhance.Brightness(bg_image)
                bg_image = enhancer.enhance(0.5)
                self.bg_photo = ImageTk.PhotoImage(bg_image)
                self.bg_canvas = tk.Canvas(self.root, highlightthickness=0)
                self.bg_canvas.pack(fill="both", expand=True)
                self.bg_canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
                print("✅ Background image loaded successfully")
            else:
                print(f"⚠️ Background image not found")
                self.create_gradient_background()
        except Exception as e:
            print(f"⚠️ Error loading background: {e}")
            self.create_gradient_background()
    
    def create_gradient_background(self):
        """Create gradient background as fallback"""
        self.bg_canvas = tk.Canvas(self.root, highlightthickness=0)
        self.bg_canvas.pack(fill="both", expand=True)
        width, height = 1920, 1080
        for i in range(height):
            color = self.interpolate_color('#1a5490', '#0d2f56', i / height)
            self.bg_canvas.create_line(0, i, width, i, fill=color)
    
    def interpolate_color(self, color1, color2, factor):
        """Interpolate between two hex colors"""
        c1 = tuple(int(color1[i:i+2], 16) for i in (1, 3, 5))
        c2 = tuple(int(color2[i:i+2], 16) for i in (1, 3, 5))
        rgb = tuple(int(c1[i] + (c2[i] - c1[i]) * factor) for i in range(3))
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
    
    def check_backend_connection(self):
        """Check if backend is running"""
        def check():
            try:
                response = requests.get(f"{self.api_base}/health", timeout=3)
                if response.status_code == 200:
                    self.root.after(0, lambda: print("✅ Backend connected"))
                else:
                    self.root.after(0, self.show_backend_error)
            except:
                self.root.after(0, self.show_backend_error)
        threading.Thread(target=check, daemon=True).start()
    
    def show_backend_error(self):
        messagebox.showerror("Backend Error", "Cannot connect to backend!\n\nPlease run: python app.py")
    
    def setup_ui(self):
        """Setup main UI with scrollbar"""
        self.main_canvas = tk.Canvas(self.bg_canvas, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.bg_canvas, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas, bg='#ffffff')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.canvas_frame = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.main_canvas.place(relx=0.5, rely=0.5, anchor="center", width=600, height=650)
        self.scrollbar.place(relx=0.95, rely=0.5, anchor="center", height=650)
        
        self.main_frame = tk.Frame(self.scrollable_frame, bg='#ffffff', relief=tk.RAISED, bd=2)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.show_login_screen()
    
    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def load_translations(self):
        def load():
            try:
                response = requests.get(f"{self.api_base}/translations/{self.current_language}", timeout=5)
                if response.status_code == 200:
                    self.translations = response.json()
            except Exception as e:
                print(f"Error loading translations: {e}")
                self.translations = {}
        threading.Thread(target=load, daemon=True).start()
    
    def get_text(self, key):
        return self.translations.get(key, key)
    
    def create_card(self, parent, title="", bg_color='white'):
        """Create card container"""
        card = tk.Frame(parent, bg=bg_color, relief=tk.RAISED, bd=2)
        card.pack(fill=tk.X, pady=5, padx=135)
        if title:
            tk.Label(card, text=title, font=self.subtitle_font, 
                    bg=bg_color, fg=self.dark_color).pack(pady=10)
        return card
    
    def create_button(self, parent, text, command, bg_color=None):
        """Create styled button"""
        if bg_color is None:
            bg_color = self.primary_color
        btn = tk.Button(
            parent, text=text, command=command,
            font=self.button_font, bg=bg_color, fg='white',
            relief=tk.RAISED, padx=25, pady=12, cursor='hand2',
            bd=2, activebackground=self.darken_color(bg_color)
        )
        return btn
    
    def create_voice_button(self, parent, command, tooltip="Voice Input"):
        """Create microphone button for voice input"""
        btn = tk.Button(
            parent, text="🎤", command=command,
            font=('Arial', 16), bg=self.voice_color, fg='white',
            relief=tk.RAISED, padx=10, pady=5, cursor='hand2',
            bd=2, activebackground=self.darken_color(self.voice_color)
        )
        return btn
    
    def darken_color(self, color):
        """Darken a hex color by 20%"""
        try:
            rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
            dark_rgb = tuple(int(c * 0.8) for c in rgb)
            return f'#{dark_rgb[0]:02x}{dark_rgb[1]:02x}{dark_rgb[2]:02x}'
        except:
            return color
    
    def update_status(self, message, color=None):
        if color is None:
            color = self.dark_color
        self.status_label.config(text=message, fg=color)
    
    def show_login_screen(self):
        self.clear_frame()
        
        # Header
        header = self.create_card(self.main_frame, bg_color=self.dark_color)
        tk.Label(header, text="🌐 NammaVoice",
                font=self.title_font, bg=self.dark_color, fg='white').pack(pady=25)
        tk.Label(header, text="All Services in Your Language",
                font=self.label_font, bg=self.dark_color, fg='white').pack(pady=(0, 25))
        
        # Language selection
        lang_card = self.create_card(self.main_frame, "Select Language")
        self.language_var = tk.StringVar(value=self.current_language)
        lang_combo = ttk.Combobox(
            lang_card, textvariable=self.language_var,
            values=['English', 'Hindi', 'Kannada', 'Tamil', 'Telugu', 'Bengali'],
            state='readonly', width=15, font=self.label_font
        )
        lang_combo.pack(pady=30)
        lang_combo.bind('<<ComboboxSelected>>', self.on_language_change)
        
        # Phone number with voice input
        phone_card = self.create_card(self.main_frame, self.get_text('enter_phone'))
        phone_frame = tk.Frame(phone_card, bg='white')
        phone_frame.pack(pady=2)
        
        tk.Label(phone_frame, text="📱", font=('Arial', 16), bg='white').pack(side=tk.LEFT)
        self.phone_entry = tk.Entry(phone_frame, font=self.label_font, width=15, relief=tk.SOLID, bd=1)
        self.phone_entry.pack(side=tk.LEFT, padx=5)
        
        if self.voice_enabled:
            self.create_voice_button(phone_frame, lambda: self.listen(
                lambda text: self.phone_entry.delete(0, tk.END) or self.phone_entry.insert(0, text.replace(" ", "")),
                "Say your phone number"
            )).pack(side=tk.LEFT)
        
        self.create_button(phone_card, "Send OTP", self.send_otp, self.primary_color).pack(pady=1)
        
        # OTP input with voice
        self.otp_card = self.create_card(self.main_frame, self.get_text('enter_otp'))
        self.otp_card.config(width=490, height=300)
        self.otp_card.pack_propagate(False)
        self.otp_card.pack_forget()
        
        otp_frame = tk.Frame(self.otp_card, bg='white')
        otp_frame.pack(pady=2)
        
        tk.Label(otp_frame, text="🔐", font=('Arial', 16), bg='white').pack(side=tk.LEFT, padx=(0, 10))
        self.otp_entry = tk.Entry(otp_frame, font=self.label_font, width=15, relief=tk.SOLID, bd=1, show="*")
        self.otp_entry.pack(side=tk.LEFT, padx=5)
        
        if self.voice_enabled:
            self.create_voice_button(otp_frame, lambda: self.listen(
                lambda text: self.otp_entry.delete(0, tk.END) or self.otp_entry.insert(0, text.replace(" ", "")),
                "Say your OTP"
            )).pack(side=tk.LEFT)
        
        self.create_button(self.otp_card, "Verify OTP", self.verify_otp, self.success_color).pack(pady=5)
        
        self.status_label = tk.Label(self.main_frame, text="", font=self.label_font, bg='white')
        self.status_label.pack(pady=10)
    
    def on_language_change(self, event=None):
        self.current_language = self.language_var.get()
        self.load_translations()
        self.update_status(f"Language: {self.current_language}", self.success_color)
        self.speak(f"Language changed to {self.current_language}")
    
    def send_otp(self):
        phone_number = self.phone_entry.get().strip()
        if not phone_number or len(phone_number) < 10:
            messagebox.showerror("Error", "Please enter valid phone number")
            self.speak("Please enter valid phone number")
            return
        
        self.update_status("Sending OTP...", self.warning_color)
        self.speak("Sending OTP")
        
        def send_request():
            try:
                response = self.session.post(f"{self.api_base}/send-otp", 
                                           json={'phone_number': phone_number, 'language': self.current_language},
                                           timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    self.root.after(0, lambda: self.otp_card.pack(pady=1))
                    self.root.after(1, lambda: self.update_status(data['message'], self.success_color))
                    self.root.after(1, lambda: self.speak(data['message']))
                    if 'otp' in data:
                        self.root.after(0, lambda: messagebox.showinfo("OTP", f"Your OTP: {data['otp']}"))
                        self.root.after(0, lambda: self.speak(f"Your OTP is {data['otp']}"))
                else:
                    error = response.json().get('error', 'Failed')
                    self.root.after(0, lambda: self.update_status(error, self.danger_color))
                    self.root.after(0, lambda: self.speak(error))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", self.danger_color))
        
        threading.Thread(target=send_request, daemon=True).start()
    
    def verify_otp(self):
        phone_number = self.phone_entry.get().strip()
        otp_code = self.otp_entry.get().strip()
        
        if not otp_code or len(otp_code) != 6:
            messagebox.showerror("Error", "Enter 6-digit OTP")
            self.speak("Enter 6 digit OTP")
            return
        
        self.update_status("Verifying...", self.warning_color)
        self.speak("Verifying OTP")
        
        def verify_request():
            try:
                response = self.session.post(f"{self.api_base}/verify-otp", 
                                           json={'phone_number': phone_number, 'otp_code': otp_code, 
                                                'language': self.current_language},
                                           timeout=10)
                
                if response.status_code == 200:
                    self.user_data = response.json()
                    self.root.after(0, lambda: self.update_status(self.user_data['message'], self.success_color))
                    self.root.after(0, lambda: self.speak(self.user_data['message']))
                    time.sleep(1)
                    self.root.after(0, self.show_main_dashboard)
                else:
                    error = response.json().get('error', 'Failed')
                    self.root.after(0, lambda: self.update_status(error, self.danger_color))
                    self.root.after(0, lambda: self.speak(error))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", self.danger_color))
        
        threading.Thread(target=verify_request, daemon=True).start()
    
    def show_main_dashboard(self):
        self.clear_frame()
        
        header = self.create_card(self.main_frame, bg_color=self.dark_color)
        tk.Label(header, text=f"{self.get_text('welcome')}", 
                font=self.title_font, bg=self.dark_color, fg='white').pack(pady=20)
        
        self.speak(self.get_text('welcome'))
        
        lang_frame = tk.Frame(header, bg=self.dark_color)
        lang_frame.pack(pady=(0, 20))
        
        tk.Label(lang_frame, text="Language:", bg=self.dark_color, fg='white', 
                font=self.label_font).pack(side=tk.LEFT, padx=(0, 10))
        
        self.dashboard_language_var = tk.StringVar(value=self.current_language)
        lang_combo = ttk.Combobox(
            lang_frame, textvariable=self.dashboard_language_var,
            values=['English', 'Hindi', 'Kannada', 'Tamil', 'Telugu', 'Bengali'],
            state='readonly', width=12, font=self.label_font
        )
        lang_combo.pack(side=tk.LEFT)
        lang_combo.bind('<<ComboboxSelected>>', self.update_dashboard_language)
        
        services = self.create_card(self.main_frame, "Available Services")
        
        bill_frame = tk.Frame(services, bg='white')
        bill_frame.pack(fill=tk.X, pady=15, padx=20)
        tk.Label(bill_frame, text="💡 Electricity Bill", font=self.subtitle_font, 
                bg='white', fg=self.dark_color).pack(side=tk.LEFT)
        self.create_button(bill_frame, f"{self.get_text('bill_payment')}", 
                          self.show_bill_payment, self.danger_color).pack(side=tk.RIGHT)
        
        tk.Frame(services, height=2, bg='#ddd').pack(fill=tk.X, padx=20, pady=10)
        
        ride_frame = tk.Frame(services, bg='white')
        ride_frame.pack(fill=tk.X, pady=15, padx=20)
        tk.Label(ride_frame, text="🚗 Transportation", font=self.subtitle_font,
                bg='white', fg=self.dark_color).pack(side=tk.LEFT)
        self.create_button(ride_frame, f"{self.get_text('book_ride')}", 
                          self.show_ride_booking, self.warning_color).pack(side=tk.RIGHT)
        
        logout_card = self.create_card(self.main_frame)
        self.create_button(logout_card, "Logout", self.logout, '#95a5a6').pack(pady=15)
        
        self.status_label = tk.Label(self.main_frame, text="Dashboard loaded", 
                                     font=self.label_font, bg='white', fg=self.success_color)
        self.status_label.pack(pady=10)
    
    def update_dashboard_language(self, event=None):
        self.current_language = self.dashboard_language_var.get()
        self.load_translations()
        self.speak(f"Language changed to {self.current_language}")
        
        def update():
            try:
                response = self.session.post(f"{self.api_base}/user/language", 
                                           json={'language': self.current_language}, timeout=5)
                if response.status_code == 200:
                    self.root.after(0, lambda: self.update_status(f"Language: {self.current_language}", 
                                                                  self.success_color))
                    time.sleep(1)
                    self.root.after(0, self.show_main_dashboard)
            except:
                pass
        
        threading.Thread(target=update, daemon=True).start()
    
    def show_bill_payment(self):
        self.clear_frame()
        self.speak("Bill payment")
        
        header = self.create_card(self.main_frame, bg_color=self.danger_color)
        tk.Label(header, text=f"💡 {self.get_text('bill_payment')}", 
                font=self.title_font, bg=self.danger_color, fg='white').pack(pady=20)
        
        customer_card = self.create_card(self.main_frame, "Customer ID")
        customer_frame = tk.Frame(customer_card, bg='white')
        customer_frame.pack(pady=15)
        
        tk.Label(customer_frame, text="🆔", font=('Arial', 16), bg='white').pack(side=tk.LEFT, padx=(0, 10))
        self.customer_id_entry = tk.Entry(customer_frame, font=self.label_font, width=20, relief=tk.SOLID, bd=1)
        self.customer_id_entry.pack(side=tk.LEFT, padx=5)
        
        if self.voice_enabled:
            self.create_voice_button(customer_frame, lambda: self.listen(
                lambda text: self.customer_id_entry.delete(0, tk.END) or self.customer_id_entry.insert(0, text.replace(" ", "")),
                "Say your customer ID"
            )).pack(side=tk.LEFT)
        
        self.create_button(customer_card, "Fetch Bill", self.fetch_bill, self.primary_color).pack(pady=15)
        
        self.bill_details_card = self.create_card(self.main_frame, "Bill Details")
        self.bill_details_card.pack_forget()
        
        nav_frame = tk.Frame(self.main_frame, bg='white')
        nav_frame.pack(pady=20)
        self.create_button(nav_frame, "← Back", self.show_main_dashboard, '#95a5a6').pack()
        
        self.status_label = tk.Label(self.main_frame, text="Enter customer ID", 
                                     font=self.label_font, bg='white')
        self.status_label.pack(pady=10)
    
    def fetch_bill(self):
        customer_id = self.customer_id_entry.get().strip()
        if not customer_id:
            messagebox.showerror("Error", "Enter Customer ID")
            self.speak("Enter Customer ID")
            return
        
        self.update_status("Fetching...", self.warning_color)
        self.speak("Fetching your bill")
        
        def fetch_request():
            try:
                response = self.session.post(f"{self.api_base}/bills/fetch",
                                           json={'customer_id': customer_id}, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    self.root.after(0, lambda: self.display_bill_details(data['bill_details']))
                    self.root.after(0, lambda: self.update_status(data['message'], self.success_color))
                    self.root.after(0, lambda: self.speak(f"Bill amount is {data['bill_details']['amount']} rupees"))
                else:
                    error = response.json().get('error', 'Failed')
                    self.root.after(0, lambda: self.update_status(error, self.danger_color))
                    self.root.after(0, lambda: self.speak(error))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", self.danger_color))
        
        threading.Thread(target=fetch_request, daemon=True).start()
    
    def display_bill_details(self, bill):
        for widget in self.bill_details_card.winfo_children():
            widget.destroy()
        
        self.bill_details_card.pack(pady=10)
        
        tk.Label(self.bill_details_card, text="Bill Details", font=self.subtitle_font, 
                bg='white').pack(pady=10)
        
        details_frame = tk.Frame(self.bill_details_card, bg='white')
        details_frame.pack(pady=10, padx=20, fill=tk.X)
        
        details = [
            ("Amount", f"₹{bill['amount']}"),
            ("Due Date", bill['due_date']),
            ("Units", str(bill['units_consumed']))
        ]
        
        for label, value in details:
            row = tk.Frame(details_frame, bg='white')
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label, font=self.label_font, bg='white', width=15, anchor='w').pack(side=tk.LEFT)
            tk.Label(row, text=value, font=('Arial', 11, 'bold'), bg='white', 
                    fg=self.primary_color).pack(side=tk.LEFT)
        
        payment_frame = tk.Frame(self.bill_details_card, bg='white')
        payment_frame.pack(pady=15)
        
        tk.Label(payment_frame, text="Payment Method:", font=self.label_font, bg='white').pack()
        
        self.payment_method_var = tk.StringVar(value='UPI')
        ttk.Combobox(payment_frame, textvariable=self.payment_method_var,
                    values=['UPI', 'Credit Card', 'Debit Card', 'Net Banking'],
                    state='readonly', width=20).pack(pady=10)
        
        self.create_button(self.bill_details_card, f"Pay ₹{bill['amount']}", 
                          lambda: self.pay_bill(bill), self.success_color).pack(pady=20)
    
    def pay_bill(self, bill):
        if not messagebox.askyesno("Confirm", f"Pay ₹{bill['amount']}?"):
            return
        
        self.update_status("Processing payment...", self.warning_color)
        self.speak("Processing payment")
        
        def payment_request():
            try:
                response = self.session.post(f"{self.api_base}/bills/pay",
                                           json={'customer_id': bill['customer_id'], 
                                                'amount': bill['amount'],
                                                'payment_method': self.payment_method_var.get()},
                                           timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    self.root.after(0, lambda: self.speak(f"Payment successful. Transaction ID {data['transaction_id']}"))
                    self.root.after(0, lambda: messagebox.showinfo("Success", 
                        f"{data['message']}\n\nTransaction ID: {data['transaction_id']}"))
                    time.sleep(1)
                    self.root.after(0, self.show_main_dashboard)
                else:
                    error = response.json().get('error', 'Failed')
                    self.root.after(0, lambda: self.update_status(error, self.danger_color))
                    self.root.after(0, lambda: self.speak(error))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", self.danger_color))
        
        threading.Thread(target=payment_request, daemon=True).start()
    
    def show_ride_booking(self):
        self.clear_frame()
        self.speak("Book a ride")
        
        header = self.create_card(self.main_frame, bg_color=self.warning_color)
        tk.Label(header, text=f"🚗 {self.get_text('book_ride')}", 
                font=self.title_font, bg=self.warning_color, fg='white').pack(pady=20)
        
        location_card = self.create_card(self.main_frame, "Journey Details")
        
        # Pickup with voice
        pickup_frame = tk.Frame(location_card, bg='white')
        pickup_frame.pack(pady=10, padx=20, fill=tk.X)
        tk.Label(pickup_frame, text="📍 Pickup Location:", font=self.label_font, bg='white').pack(anchor='w')
        
        pickup_input_frame = tk.Frame(pickup_frame, bg='white')
        pickup_input_frame.pack(pady=5, fill=tk.X)
        self.pickup_entry = tk.Entry(pickup_input_frame, font=self.label_font, width=30, relief=tk.SOLID, bd=1)
        self.pickup_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        if self.voice_enabled:
            self.create_voice_button(pickup_input_frame, lambda: self.listen(
                lambda text: self.pickup_entry.delete(0, tk.END) or self.pickup_entry.insert(0, text),
                "Say your pickup location"
            )).pack(side=tk.LEFT)
        
        # Drop with voice
        drop_frame = tk.Frame(location_card, bg='white')
        drop_frame.pack(pady=10, padx=20, fill=tk.X)
        tk.Label(drop_frame, text="📍 Drop Location:", font=self.label_font, bg='white').pack(anchor='w')
        
        drop_input_frame = tk.Frame(drop_frame, bg='white')
        drop_input_frame.pack(pady=5, fill=tk.X)
        self.drop_entry = tk.Entry(drop_input_frame, font=self.label_font, width=30, relief=tk.SOLID, bd=1)
        self.drop_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        if self.voice_enabled:
            self.create_voice_button(drop_input_frame, lambda: self.listen(
                lambda text: self.drop_entry.delete(0, tk.END) or self.drop_entry.insert(0, text),
                "Say your drop location"
            )).pack(side=tk.LEFT)
        
        # Ride type
        ride_type_card = self.create_card(self.main_frame, "Select Ride Type")
        self.ride_type_var = tk.StringVar(value='auto')
        
        rides = [
            ('auto', '🛺 Auto Rickshaw - ₹25 base fare'),
            ('mini', '🚗 Mini Car - ₹50 base fare'),
            ('sedan', '🚙 Sedan - ₹80 base fare')
        ]
        
        for value, text in rides:
            tk.Radiobutton(ride_type_card, text=text, variable=self.ride_type_var, value=value,
                          font=self.label_font, bg='white', selectcolor='#e8f4f8').pack(anchor=tk.W, padx=20, pady=5)
        
        self.create_button(self.main_frame, "Book Ride Now", self.book_ride, 
                          self.success_color).pack(pady=30)
        
        nav_frame = tk.Frame(self.main_frame, bg='white')
        nav_frame.pack(pady=20)
        self.create_button(nav_frame, "← Back", self.show_main_dashboard, '#95a5a6').pack()
        
        self.status_label = tk.Label(self.main_frame, text="Enter pickup and drop locations", 
                                     font=self.label_font, bg='white')
        self.status_label.pack(pady=10)
    
    def book_ride(self):
        pickup = self.pickup_entry.get().strip()
        drop = self.drop_entry.get().strip()
        
        if not pickup or not drop:
            messagebox.showerror("Error", "Enter both pickup and drop locations")
            self.speak("Enter both pickup and drop locations")
            return
        
        self.update_status("Searching for drivers...", self.warning_color)
        self.speak("Searching for drivers")
        
        def booking_request():
            try:
                response = self.session.post(f"{self.api_base}/rides/book",
                                           json={'pickup_location': pickup, 'drop_location': drop,
                                                'ride_type': self.ride_type_var.get()},
                                           timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    ride = data['ride_details']
                    self.root.after(0, lambda: self.show_ride_confirmation(ride))
                    self.root.after(0, lambda: self.speak(
                        f"Ride confirmed. Driver {ride['driver_name']} will arrive in {ride['estimated_arrival']}"
                    ))
                else:
                    error = response.json().get('error', 'Booking failed')
                    self.root.after(0, lambda: self.update_status(error, self.danger_color))
                    self.root.after(0, lambda: self.speak(error))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Error: {str(e)}", self.danger_color))
        
        threading.Thread(target=booking_request, daemon=True).start()
    
    def show_ride_confirmation(self, ride):
        """Show ride booking confirmation"""
        self.clear_frame()
        
        header = self.create_card(self.main_frame, bg_color=self.success_color)
        tk.Label(header, text="✅ Ride Confirmed!", 
                font=self.title_font, bg=self.success_color, fg='white').pack(pady=20)
        tk.Label(header, text=f"Booking ID: #{ride['booking_id']}", 
                font=self.label_font, bg=self.success_color, fg='white').pack(pady=(0, 20))
        
        # Journey details
        journey_card = self.create_card(self.main_frame, "Journey Details")
        journey_frame = tk.Frame(journey_card, bg='white')
        journey_frame.pack(pady=15, padx=20, fill=tk.X)
        
        journey_info = [
            ("From", ride['pickup_location'], "📍"),
            ("To", ride['drop_location'], "📍"),
            ("Ride Type", ride['ride_type'].title(), "🚗"),
            ("Estimated Fare", f"₹{ride['estimated_fare']}", "💰")
        ]
        
        for label, value, icon in journey_info:
            row = tk.Frame(journey_frame, bg='white')
            row.pack(fill=tk.X, pady=8)
            
            icon_label = tk.Label(row, text=icon, font=('Arial', 14), bg='white')
            icon_label.pack(side=tk.LEFT, padx=(0, 10))
            
            label_text = tk.Label(row, text=f"{label}:", font=self.label_font, 
                                 bg='white', width=15, anchor='w')
            label_text.pack(side=tk.LEFT)
            
            value_text = tk.Label(row, text=value, font=('Arial', 11, 'bold'), 
                                 bg='white', fg=self.primary_color)
            value_text.pack(side=tk.LEFT)
        
        # Driver details
        driver_card = self.create_card(self.main_frame, "Driver Information")
        driver_card.config(bg='#e8f8f5')
        
        driver_frame = tk.Frame(driver_card, bg='#e8f8f5')
        driver_frame.pack(pady=15, padx=20, fill=tk.X)
        
        driver_info = [
            ("👤", "Driver:", ride['driver_name']),
            ("🚗", "Vehicle:", ride['vehicle_number']),
            ("📞", "Contact:", ride['driver_phone'])
        ]
        
        for icon, label, value in driver_info:
            row = tk.Frame(driver_frame, bg='#e8f8f5')
            row.pack(fill=tk.X, pady=5)
            tk.Label(row, text=icon, font=('Arial', 16), bg='#e8f8f5').pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(row, text=label, font=self.label_font, bg='#e8f8f5').pack(side=tk.LEFT)
            tk.Label(row, text=value, font=('Arial', 12, 'bold'), 
                    bg='#e8f8f5', fg=self.dark_color).pack(side=tk.LEFT, padx=(10, 0))
        
        # Arrival time
        arrival_card = self.create_card(self.main_frame)
        arrival_card.config(bg='#fff3cd', relief=tk.SOLID, bd=2)
        
        arrival_frame = tk.Frame(arrival_card, bg='#fff3cd')
        arrival_frame.pack(pady=20)
        
        tk.Label(arrival_frame, text="⏱️", font=('Arial', 24), bg='#fff3cd').pack()
        tk.Label(arrival_frame, text="Estimated Arrival", font=self.label_font, 
                bg='#fff3cd', fg='#856404').pack(pady=(5, 0))
        tk.Label(arrival_frame, text=ride['estimated_arrival'], 
                font=('Arial', 16, 'bold'), bg='#fff3cd', fg='#856404').pack(pady=(5, 0))
        
        # Action buttons
        button_frame = tk.Frame(self.main_frame, bg='white')
        button_frame.pack(pady=25)
        
        self.create_button(button_frame, "Track Driver", lambda: self.track_driver(ride), 
                          self.primary_color).pack(side=tk.LEFT, padx=10)
        self.create_button(button_frame, "Cancel Ride", lambda: self.cancel_ride(ride), 
                          self.danger_color).pack(side=tk.LEFT, padx=10)
        
        # Back button
        nav_frame = tk.Frame(self.main_frame, bg='white')
        nav_frame.pack(pady=20)
        self.create_button(nav_frame, "← Back to Dashboard", self.show_main_dashboard, 
                          '#95a5a6').pack()
        
        self.status_label = tk.Label(self.main_frame, text="Your ride is on the way!", 
                                     font=self.label_font, bg='white', fg=self.success_color)
        self.status_label.pack(pady=10)
    
    def track_driver(self, ride):
        """Simulate driver tracking"""
        msg = (f"Driver Location: Approaching pickup point\n\n"
               f"Distance: ~2.5 km away\n"
               f"ETA: {ride['estimated_arrival']}\n\n"
               f"Driver: {ride['driver_name']}\n"
               f"Vehicle: {ride['vehicle_number']}")
        messagebox.showinfo("Driver Tracking", msg)
        self.speak(f"Driver is approaching. Estimated arrival in {ride['estimated_arrival']}")
    
    def cancel_ride(self, ride):
        """Cancel ride booking"""
        if messagebox.askyesno("Cancel Ride", 
                              "Are you sure you want to cancel this ride?\n\n"
                              "Cancellation charges may apply."):
            messagebox.showinfo("Ride Cancelled", 
                               f"Booking #{ride['booking_id']} has been cancelled")
            self.speak("Ride cancelled")
            self.show_main_dashboard()
    
    def logout(self):
        """Logout user"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            try:
                self.session.post(f"{self.api_base}/logout", timeout=3)
            except:
                pass
            self.user_data = {}
            self.speak("Logged out successfully")
            self.show_login_screen()

if __name__ == "__main__":
    root = tk.Tk()
    app = ServiceAssistantApp(root)
    root.mainloop()