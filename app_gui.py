#!/usr/bin/env python3
"""
Interface GUI simple avec Tkinter (intégré à Python)
Pas besoin de dépendances web externes
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os

# Ajouter le répertoire courant au path pour importer le scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import GoogleMapsScraper

class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🗺️ Google Maps Scraper")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Variables
        self.is_running = False
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principal
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titre
        title_label = ttk.Label(main_frame, text="🗺️ Google Maps Scraper", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, 
                                  text="Extraction automatique d'entreprises et recherche d'emails",
                                  font=("Arial", 10))
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Champ de recherche
        search_label = ttk.Label(main_frame, text="Recherche Google Maps:")
        search_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.search_entry = ttk.Entry(main_frame, width=40)
        self.search_entry.grid(row=2, column=1, pady=(0, 5))
        self.search_entry.insert(0, "restaurants à Paris")
        
        # Slider pour le nombre de résultats
        results_label = ttk.Label(main_frame, text="Nombre d'entreprises:")
        results_label.grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        
        self.results_var = tk.IntVar(value=50)
        self.results_slider = ttk.Scale(main_frame, from_=10, to=200, 
                                       variable=self.results_var, 
                                       orient=tk.HORIZONTAL, length=200)
        self.results_slider.grid(row=3, column=1, pady=(10, 5))
        
        self.results_label = ttk.Label(main_frame, text="50")
        self.results_label.grid(row=4, column=1, pady=(0, 20))
        
        # Mettre à jour le label quand le slider change
        self.results_slider.configure(command=self.update_results_label)
        
        # Bouton de démarrage
        self.start_button = ttk.Button(main_frame, text="🚀 Lancer le scraping", 
                                      command=self.start_scraping)
        self.start_button.grid(row=5, column=0, columnspan=2, pady=(0, 20))
        
        # Zone de log
        log_label = ttk.Label(main_frame, text="Progression:")
        log_label.grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=12, width=50)
        self.log_text.grid(row=7, column=0, columnspan=2, pady=(0, 10))
        
        # Bouton de fermeture
        close_button = ttk.Button(main_frame, text="Fermer", command=root.quit)
        close_button.grid(row=8, column=0, columnspan=2)
        
        # Message initial
        self.log("🚀 Google Maps Scraper prêt à l'emploi")
        self.log("💡 Configurez votre recherche et cliquez sur 'Lancer le scraping'")
        self.log("")
    
    def update_results_label(self, value):
        """Met à jour le label du nombre de résultats"""
        self.results_label.config(text=str(int(float(value))))
    
    def log(self, message):
        """Ajoute un message dans la zone de log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_scraping(self):
        """Démarre le scraping dans un thread séparé"""
        if self.is_running:
            messagebox.showwarning("Attention", "Le scraping est déjà en cours!")
            return
        
        search_query = self.search_entry.get().strip()
        max_results = self.results_var.get()
        
        if not search_query:
            messagebox.showerror("Erreur", "Veuillez saisir une recherche valide!")
            return
        
        # Désactiver le bouton
        self.is_running = True
        self.start_button.config(state="disabled", text="⏳ Scraping en cours...")
        
        # Vider le log
        self.log_text.delete(1.0, tk.END)
        self.log(f"🔍 Recherche: {search_query}")
        self.log(f"📊 Nombre d'entreprises: {max_results}")
        self.log("")
        
        # Démarrer le scraper dans un thread
        thread = threading.Thread(target=self.run_scraper, args=(search_query, max_results))
        thread.daemon = True
        thread.start()
    
    def run_scraper(self, search_query, max_results):
        """Exécute le scraper"""
        try:
            self.log("🚀 Démarrage du scraping...")
            
            # Créer le scraper
            scraper = GoogleMapsScraper()
            
            # Scraper Google Maps
            self.log("📥 Recherche sur Google Maps...")
            results = scraper.scrape_google_maps(search_query, max_results)
            
            if not results:
                self.log("❌ Aucun résultat trouvé")
                self.finish_scraping()
                return
            
            self.log(f"✅ {len(results)} entreprises trouvées")
            
            # Traiter les résultats
            self.log("🔄 Traitement des résultats...")
            processed_data = scraper.process_results(results)
            
            self.log(f"📧 {sum(1 for b in processed_data if b['contact_email'])} emails trouvés")
            
            # Sauvegarder dans Google Sheets
            self.log("📝 Sauvegarde dans Google Sheets...")
            scraper.save_to_google_sheets(processed_data)
            
            # Envoyer vers GoHighLevel
            self.log("📤 Envoi vers GoHighLevel (si configuré)...")
            scraper.send_to_gohighlevel(processed_data)
            
            self.log("")
            self.log("🎉 SCRAPING TERMINÉ AVEC SUCCÈS!")
            self.log(f"📊 Résumé: {len(results)} entreprises traitées")
            self.log("📱 Consultez votre Google Sheet pour voir les résultats")
            
        except Exception as e:
            self.log(f"❌ Erreur: {str(e)}")
        
        finally:
            self.finish_scraping()
    
    def finish_scraping(self):
        """Réactive l'interface après le scraping"""
        self.is_running = False
        self.start_button.config(state="normal", text="🚀 Lancer le scraping")

def main():
    """Fonction principale"""
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
