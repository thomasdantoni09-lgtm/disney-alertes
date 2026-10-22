import os
import json
import requests

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Remplace par le nom EXACT du canal choisi dans l'application ntfy
NTFY_TOPIC = "disney-thomas-2026"  

# Tes 15 attractions cibles
TARGET_ATTRACTIONS = [
    "It's a Small World",
    "Indiana Jones",
    "Phantom Manor",
    "Autopia",
    "Star Wars Hyperspace Mountain",
    "Big Thunder Mountain",
    "Peter Pan's Flight",
    "Twilight Zone Tower of Terror",
    "Ratatouille",
    "Avengers Assemble: Flight Force",
    "RC Racer",
    "Crush's Coaster",
    "Toy Soldiers Parachute Drop",
    "Frozen Ever After",
    "Pirates of the Caribbean"
]

# IDs des parcs : 4 = Parc Disneyland, 332 = Walt Disney Studios / Disney Adventure World
PARK_IDS = [4, 332]
STATE_FILE = "previous_states.json"

# ==========================================
# 2. FONCTIONS DE NOTIFICATION ET FICHIERS
# ==========================================
def send_ntfy_notification(title, message, priority="default", tags=""):
    """Envoie la notification sur ton téléphone via Ntfy"""
    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": tags
    }
    try:
        requests.post(url, data=message.encode('utf-8'), headers=headers, timeout=10)
    except Exception as e:
        print(f"Erreur d'envoi Ntfy: {e}")

def load_previous_states():
    """Charge les états enregistrés lors du dernier passage"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_current_states(states):
    """Sauvegarde l'état actuel des attractions"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(states, f, ensure_ascii=False, indent=2)

# ==========================================
# 3. LOGIQUE PRINCIPALE
# ==========================================
def check_disney_attractions():
    previous_states = load_previous_states()
    current_states = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Récupération des données depuis l'API Queue-Times
    for park_id in PARK_IDS:
        url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue
            
            data = res.json()
            for land in data.get("lands", []):
                for ride in land.get("rides", []):
                    ride_name = ride.get("name", "")
                    
                    # Vérification si l'attraction fait partie de tes 15 cibles
                    for target in TARGET_ATTRACTIONS:
                        if target.lower() in ride_name.lower():
                            current_states[target] = {
                                "is_open": ride.get("is_open", False),
                                "wait_time": ride.get("wait_time", 0),
                                "full_name": ride_name
                            }
                            break
        except Exception as e:
            print(f"Erreur de connexion au parc {park_id}: {e}")

    # Comparaison avec le tour précédent
    for target, info in current_states.items():
        is_open = info["is_open"]
        wait_time = info["wait_time"]
        full_name = info["full_name"]
        
        if target in previous_states:
            was_open = previous_states[target]["is_open"]
            
            # CAS 1 : RÉOUVRIR 🚀
            if not was_open and is_open:
                send_ntfy_notification(
                    title=f"🟢 RÉOUVERTURE : {target}",
                    message=f"L'attraction {full_name} vient de réouvrir ! Temps d'attente : {wait_time} min.",
                    priority="high",
                    tags="rocket,green_circle"
                )
                print(f"Alerte envoyée : {target} a réouvert !")
                
            # CAS 2 : FERMER ⚠️
            elif was_open and not is_open:
                send_ntfy_notification(
                    title=f"🔴 FERMETURE : {target}",
                    message=f"L'attraction {full_name} est désormais fermée (panne/interruption).",
                    priority="default",
                    tags="warning,red_circle"
                )
                print(f"Alerte envoyée : {target} a fermé !")

    # Enregistrement pour la prochaine exécution
    save_current_states(current_states)

if __name__ == "__main__":
    check_disney_attractions()
  
