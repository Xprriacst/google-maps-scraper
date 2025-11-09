#!/usr/bin/env python3
"""Interface web simple avec Flask pour lancer le scraper"""

from flask import Flask, render_template, request, jsonify
import threading
import time
from datetime import datetime
import os
import sys

# Ajouter le répertoire courant au path pour importer le scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import GoogleMapsScraper

app = Flask(__name__)

# Variable globale pour suivre l'état du scraping
scraping_status = {
    "running": False,
    "message": "",
    "progress": 0,
    "total": 0,
    "results": [],
    "error": None
}

def run_scraper_async(search_query, max_results):
    """Exécute le scraper en arrière-plan"""
    global scraping_status
    
    try:
        scraping_status["running"] = True
        scraping_status["message"] = f"Recherche de {max_results} entreprises pour: {search_query}"
        scraping_status["progress"] = 0
        scraping_status["total"] = max_results
        scraping_status["results"] = []
        scraping_status["error"] = None
        
        # Créer et exécuter le scraper
        scraper = GoogleMapsScraper()
        
        # Simuler la progression (le scraper réel n'a pas de callback)
        scraping_status["message"] = "Scraping Google Maps en cours..."
        
        # Exécuter le scraper
        results = scraper.scrape_google_maps(search_query, max_results)
        
        if results:
            scraping_status["message"] = "Traitement des résultats..."
            scraping_status["progress"] = 50
            
            processed_data = scraper.process_results(results)
            
            scraping_status["message"] = "Sauvegarde dans Google Sheets..."
            scraping_status["progress"] = 80
            
            scraper.save_to_google_sheets(processed_data)
            
            scraping_status["message"] = "Envoi vers GoHighLevel (si configuré)..."
            scraping_status["progress"] = 90
            
            scraper.send_to_gohighlevel(processed_data)
            
            scraping_status["progress"] = 100
            scraping_status["message"] = "✅ Scraping terminé avec succès !"
            scraping_status["results"] = processed_data
        else:
            scraping_status["error"] = "Aucun résultat trouvé"
            
    except Exception as e:
        scraping_status["error"] = f"Erreur: {str(e)}"
    finally:
        scraping_status["running"] = False

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🗺️ Google Maps Scraper</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .slider-container {
            margin-top: 10px;
        }
        input[type="range"] {
            width: 100%;
            margin: 10px 0;
        }
        .slider-value {
            text-align: center;
            font-size: 1.2em;
            color: #667eea;
            font-weight: bold;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .status {
            margin-top: 30px;
            padding: 20px;
            border-radius: 8px;
            display: none;
        }
        .status.running {
            background: #e3f2fd;
            border: 1px solid #2196f3;
        }
        .status.success {
            background: #e8f5e8;
            border: 1px solid #4caf50;
        }
        .status.error {
            background: #ffebee;
            border: 1px solid #f44336;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e1e5e9;
            border-radius: 4px;
            overflow: hidden;
            margin: 15px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
            width: 0%;
        }
        .features {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .features h3 {
            color: #333;
            margin-bottom: 15px;
        }
        .features ul {
            list-style: none;
        }
        .features li {
            margin: 8px 0;
            color: #666;
        }
        .features li:before {
            content: "✅ ";
            color: #4caf50;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🗺️ Google Maps Scraper</h1>
        <p class="subtitle">Extraction automatique d'entreprises et recherche d'emails</p>
        
        <form id="scraperForm">
            <div class="form-group">
                <label for="search_query">Recherche Google Maps</label>
                <input type="text" id="search_query" name="search_query" 
                       placeholder="ex: restaurants à Paris" required>
            </div>
            
            <div class="form-group">
                <label for="max_results">Nombre d'entreprises</label>
                <div class="slider-container">
                    <input type="range" id="max_results" name="max_results" 
                           min="10" max="200" value="50" step="10">
                    <div class="slider-value" id="slider_value">50</div>
                </div>
            </div>
            
            <button type="submit" id="submitBtn">🚀 Lancer le scraping</button>
        </form>
        
        <div id="status" class="status">
            <div id="status_message"></div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress_fill"></div>
            </div>
        </div>
        
        <div class="features">
            <h3>🎯 Fonctionnalités</h3>
            <ul>
                <li>Scraping Google Maps via Apify</li>
                <li>Recherche automatique d'emails</li>
                <li>Export vers Google Sheets</li>
                <li>Intégration GoHighLevel</li>
                <li>Interface web intuitive</li>
            </ul>
        </div>
    </div>

    <script>
        // Slider
        const slider = document.getElementById('max_results');
        const sliderValue = document.getElementById('slider_value');
        sliderValue.textContent = slider.value;
        
        slider.addEventListener('input', function() {
            sliderValue.textContent = this.value;
        });
        
        // Form submission
        const form = document.getElementById('scraperForm');
        const submitBtn = document.getElementById('submitBtn');
        const statusDiv = document.getElementById('status');
        const statusMessage = document.getElementById('status_message');
        const progressFill = document.getElementById('progress_fill');
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const searchQuery = document.getElementById('search_query').value;
            const maxResults = document.getElementById('max_results').value;
            
            if (!searchQuery.trim()) {
                alert('Veuillez saisir une recherche valide');
                return;
            }
            
            // Désactiver le bouton
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Scraping en cours...';
            
            // Afficher le statut
            statusDiv.style.display = 'block';
            statusDiv.className = 'status running';
            statusMessage.textContent = 'Démarrage du scraping...';
            progressFill.style.width = '0%';
            
            // Démarrer le scraping
            fetch('/start_scraping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    search_query: searchQuery,
                    max_results: parseInt(maxResults)
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Commencer à vérifier le statut
                    checkStatus();
                } else {
                    showError(data.error);
                }
            })
            .catch(error => {
                showError('Erreur: ' + error.message);
            });
        });
        
        function checkStatus() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                statusMessage.textContent = data.message;
                progressFill.style.width = data.progress + '%';
                
                if (data.error) {
                    showError(data.error);
                } else if (!data.running) {
                    // Scraping terminé
                    statusDiv.className = 'status success';
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🚀 Lancer le scraping';
                    
                    // Afficher les résultats
                    if (data.results && data.results.length > 0) {
                        statusMessage.innerHTML += '<br><br><strong>Résultats:</strong> ' + 
                            data.results.length + ' entreprises trouvées';
                    }
                } else {
                    // Continuer à vérifier
                    setTimeout(checkStatus, 2000);
                }
            })
            .catch(error => {
                showError('Erreur de statut: ' + error.message);
            });
        }
        
        function showError(message) {
            statusDiv.className = 'status error';
            statusMessage.textContent = message;
            submitBtn.disabled = false;
            submitBtn.textContent = '🚀 Lancer le scraping';
        }
    </script>
</body>
</html>
    ''')

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Démarre le scraping"""
    data = request.json
    search_query = data.get('search_query')
    max_results = data.get('max_results')
    
    if not search_query or not max_results:
        return jsonify({"success": False, "error": "Paramètres manquants"})
    
    # Démarrer le scraper en arrière-plan
    thread = threading.Thread(target=run_scraper_async, args=(search_query, max_results))
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True})

@app.route('/status')
def get_status():
    """Retourne le statut du scraping"""
    return jsonify(scraping_status)

if __name__ == '__main__':
    print("🚀 Démarrage de l'interface web...")
    print("📱 Ouvrez votre navigateur sur: http://localhost:5000")
    print("⏹️  Arrêtez avec Ctrl+C")
    
    app.run(host='127.0.0.1', port=5000, debug=False)
