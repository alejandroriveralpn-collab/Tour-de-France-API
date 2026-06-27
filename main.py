from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import requests
import time
import random

API_KEY = "640143a914dca7439c99b9cdea66bb57"


# =============================
# SIMULATION CYCLISTE (FALLBACK)
# =============================

def simulate_live_race():
    riders = [
        "Pogačar",
        "Vingegaard",
        "Evenepoel",
        "Pidcock",
        "Bernal"
    ]

    leader_time = 0
    data = []

    for r in riders:
        gap = leader_time
        data.append({
            "rider": r,
            "gap_seconds": gap
        })
        leader_time += random.randint(5, 40)

    return {
        "source": "simulation",
        "timestamp": time.time(),
        "classification": data
    }


# =============================
# API SPORTS (TENTATIVE LIVE)
# =============================

def api_sports_live():
    url = "https://v3.api-sports.io/fixtures"

    headers = {
        "x-apisports-key": API_KEY
    }

    try:
        r = requests.get(url, headers=headers, timeout=5)

        return {
            "source": "api-sports",
            "status_code": r.status_code,
            "data": r.json()
        }

    except Exception as e:
        return {
            "error": str(e)
        }


# =============================
# LETOUR SCRAPER SIMPLE (SAFE)
# =============================

def scrape_letour():
    try:
        url = "https://www.letour.fr/fr/actus"
        r = requests.get(url, timeout=5)

        return {
            "source": "letour",
            "status_code": r.status_code,
            "snippet": r.text[:300]  # juste aperçu sécurisé
        }

    except Exception as e:
        return {"error": str(e)}


# =============================
# SERVER
# =============================

class Handler(BaseHTTPRequestHandler):

    def send(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_GET(self):

        # ROOT
        if self.path == "/":
            self.send({
                "api": "Cycling Live Tracker",
                "endpoints": ["/live", "/gc", "/scrape"]
            })

        # LIVE TRACKING HYBRIDE
        elif self.path == "/live":

            api = api_sports_live()

            if api.get("status_code") == 200:
                self.send({
                    "mode": "api_live",
                    "data": api
                })
                return

            # fallback scraping
            scrape = scrape_letour()

            if "error" not in scrape:
                self.send({
                    "mode": "web_scrape",
                    "data": scrape
                })
                return

            # last fallback simulation
            self.send({
                "mode": "simulation",
                "data": simulate_live_race()
            })

        # GENERAL CLASSIFICATION
        elif self.path == "/gc":
            self.send(simulate_live_race())

        # SCRAPER TEST
        elif self.path == "/scrape":
            self.send(scrape_letour())

        else:
            self.send({"error": "route not found"})


server = HTTPServer(("127.0.0.1", 8000), Handler)

print("🚴 LIVE TRACKING API RUNNING")

server.serve_forever()