#!/usr/bin/env python3
"""
Serveur web simple pour l'interface Google Maps Scraper
Utilise http.server (intégré à Python) avec une API REST
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import os
from urllib.parse import parse_qs, urlparse
from scraper import GoogleMapsScraper

# État global du scraping
scraping_state = {
    "running": False,
    "progress": 0,
    "message": "En attente",
    "total": 0,
    "current": 0,
    "results": []
}

class ScraperHandler(BaseHTTPRequestHandler):
    """Gestionnaire des requêtes HTTP"""
    
    def do_GET(self):
        """Traite les requêtes GET"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Servir la page HTML
            self.serve_html()
        elif parsed_path.path == '/api/status':
            # Retourner le statut du scraping
            self.send_json_response(scraping_state)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Traite les requêtes POST"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/start':
            # Démarrer le scraping
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            if scraping_state["running"]:
                self.send_json_response({"success": False, "error": "Scraping déjà en cours"})
                return
            
            # Démarrer le scraping dans un thread
            search_query = data.get('search_query', '')
            max_results = data.get('max_results', 50)
            
            if not search_query:
                self.send_json_response({"success": False, "error": "Recherche vide"})
                return
            
            thread = threading.Thread(target=self.run_scraper, args=(search_query, max_results))
            thread.daemon = True
            thread.start()
            
            self.send_json_response({"success": True})
        else:
            self.send_error(404)
    
    def run_scraper(self, search_query, max_results):
        """Exécute le scraping"""
        global scraping_state
        
        try:
            scraping_state["running"] = True
            scraping_state["progress"] = 0
            scraping_state["message"] = f"Recherche de {max_results} entreprises: {search_query}"
            scraping_state["total"] = max_results
            scraping_state["current"] = 0
            scraping_state["results"] = []
            
            scraper = GoogleMapsScraper()
            
            # Scraping Google Maps
            scraping_state["message"] = "📥 Scraping Google Maps..."
            scraping_state["progress"] = 10
            results = scraper.scrape_google_maps(search_query, max_results)
            
            if not results:
                scraping_state["message"] = "❌ Aucun résultat trouvé"
                scraping_state["running"] = False
                return
            
            scraping_state["message"] = f"✅ {len(results)} entreprises trouvées"
            scraping_state["progress"] = 30
            
            # Traitement
            scraping_state["message"] = "🔄 Recherche des emails..."
            processed_data = scraper.process_results(results)
            scraping_state["progress"] = 60
            
            # Sauvegarde Google Sheets
            scraping_state["message"] = "📝 Sauvegarde dans Google Sheets..."
            scraper.save_to_google_sheets(processed_data)
            scraping_state["progress"] = 80
            
            # GoHighLevel
            scraping_state["message"] = "📤 Envoi vers GoHighLevel..."
            scraper.send_to_gohighlevel(processed_data)
            scraping_state["progress"] = 100
            
            scraping_state["message"] = "✅ Scraping terminé avec succès!"
            scraping_state["results"] = processed_data
            
        except Exception as e:
            scraping_state["message"] = f"❌ Erreur: {str(e)}"
            scraping_state["progress"] = 0
        finally:
            scraping_state["running"] = False
    
    def serve_html(self):
        """Sert la page HTML"""
        html_content = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Maps Scraper</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
            padding: 40px;
            animation: slideIn 0.5s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #666;
            font-size: 1.1em;
        }

        .form-group {
            margin-bottom: 25px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 14px;
        }

        input[type="text"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e8ed;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .slider-container {
            position: relative;
        }

        input[type="range"] {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: #e1e8ed;
            outline: none;
            -webkit-appearance: none;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(102, 126, 234, 0.5);
        }

        input[type="range"]::-moz-range-thumb {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            cursor: pointer;
            border: none;
        }

        .slider-value {
            text-align: center;
            margin-top: 10px;
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }

        .btn {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }

        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .status-card {
            margin-top: 30px;
            padding: 20px;
            border-radius: 10px;
            display: none;
        }

        .status-card.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .status-card.running {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
        }

        .status-card.success {
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
        }

        .status-card.error {
            background: #ffebee;
            border-left: 4px solid #f44336;
        }

        .status-message {
            font-size: 16px;
            margin-bottom: 15px;
            color: #333;
        }

        .progress-bar {
            width: 100%;
            height: 10px;
            background: #e1e8ed;
            border-radius: 5px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
            width: 0%;
        }

        .results {
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 8px;
        }

        .result-item {
            padding: 10px;
            border-bottom: 1px solid #e1e8ed;
        }

        .result-item:last-child {
            border-bottom: none;
        }

        .features {
            margin-top: 30px;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }

        .feature {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            text-align: center;
        }

        .feature-icon {
            font-size: 2em;
            margin-bottom: 8px;
        }

        .feature-text {
            font-size: 0.9em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗺️ Google Maps Scraper</h1>
            <p class="subtitle">Extraction automatique d'entreprises et recherche d'emails</p>
        </div>

        <form id="scraperForm">
            <div class="form-group">
                <label for="searchQuery">Recherche Google Maps</label>
                <input 
                    type="text" 
                    id="searchQuery" 
                    placeholder="Ex: restaurants à Paris" 
                    required
                >
            </div>

            <div class="form-group">
                <label for="maxResults">Nombre d'entreprises</label>
                <div class="slider-container">
                    <input 
                        type="range" 
                        id="maxResults" 
                        min="10" 
                        max="200" 
                        value="50" 
                        step="10"
                    >
                    <div class="slider-value" id="sliderValue">50</div>
                </div>
            </div>

            <button type="submit" class="btn" id="submitBtn">
                🚀 Lancer le scraping
            </button>
        </form>

        <div id="statusCard" class="status-card">
            <div class="status-message" id="statusMessage"></div>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="results" id="results" style="display: none;"></div>
        </div>

        <div class="features">
            <div class="feature">
                <div class="feature-icon">🗺️</div>
                <div class="feature-text">Scraping Google Maps</div>
            </div>
            <div class="feature">
                <div class="feature-icon">📧</div>
                <div class="feature-text">Recherche d'emails</div>
            </div>
            <div class="feature">
                <div class="feature-icon">📊</div>
                <div class="feature-text">Export Google Sheets</div>
            </div>
            <div class="feature">
                <div class="feature-icon">🚀</div>
                <div class="feature-text">GoHighLevel</div>
            </div>
        </div>
    </div>

    <script>
        // Slider
        const slider = document.getElementById('maxResults');
        const sliderValue = document.getElementById('sliderValue');

        slider.addEventListener('input', () => {
            sliderValue.textContent = slider.value;
        });

        // Form
        const form = document.getElementById('scraperForm');
        const submitBtn = document.getElementById('submitBtn');
        const statusCard = document.getElementById('statusCard');
        const statusMessage = document.getElementById('statusMessage');
        const progressFill = document.getElementById('progressFill');
        const resultsDiv = document.getElementById('results');

        let checkInterval;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const searchQuery = document.getElementById('searchQuery').value;
            const maxResults = parseInt(document.getElementById('maxResults').value);

            // Désactiver le bouton
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Scraping en cours...';

            // Afficher le status
            statusCard.className = 'status-card active running';
            statusMessage.textContent = 'Démarrage du scraping...';
            progressFill.style.width = '0%';
            resultsDiv.style.display = 'none';

            try {
                const response = await fetch('/api/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ search_query: searchQuery, max_results: maxResults })
                });

                const data = await response.json();

                if (data.success) {
                    // Commencer à vérifier le statut
                    checkInterval = setInterval(checkStatus, 1000);
                } else {
                    showError(data.error || 'Erreur inconnue');
                }
            } catch (error) {
                showError('Erreur de connexion: ' + error.message);
            }
        });

        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                statusMessage.textContent = data.message;
                progressFill.style.width = data.progress + '%';

                if (!data.running && data.progress === 100) {
                    // Succès
                    clearInterval(checkInterval);
                    statusCard.className = 'status-card active success';
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🚀 Lancer le scraping';

                    if (data.results && data.results.length > 0) {
                        resultsDiv.style.display = 'block';
                        resultsDiv.innerHTML = `
                            <strong>✅ ${data.results.length} entreprises scrapées</strong><br>
                            <small>Consultez votre Google Sheet pour voir les détails</small>
                        `;
                    }
                } else if (!data.running && data.progress === 0 && data.message.includes('❌')) {
                    // Erreur
                    clearInterval(checkInterval);
                    showError(data.message);
                }
            } catch (error) {
                console.error('Erreur de vérification du statut:', error);
            }
        }

        function showError(message) {
            clearInterval(checkInterval);
            statusCard.className = 'status-card active error';
            statusMessage.textContent = message;
            submitBtn.disabled = false;
            submitBtn.textContent = '🚀 Lancer le scraping';
            progressFill.style.width = '0%';
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def send_json_response(self, data):
        """Envoie une réponse JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Supprime les logs HTTP pour garder l'affichage propre"""
        pass

def run_server(port=8000):
    """Lance le serveur HTTP"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ScraperHandler)
    
    print("\n" + "="*70)
    print("🚀 GOOGLE MAPS SCRAPER - Interface Web")
    print("="*70)
    print(f"\n✨ Serveur démarré avec succès!")
    print(f"📱 Ouvrez votre navigateur sur: http://localhost:{port}")
    print(f"⏹️  Arrêtez avec Ctrl+C\n")
    print("="*70 + "\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Serveur arrêté. Au revoir!")

if __name__ == '__main__':
    run_server()
