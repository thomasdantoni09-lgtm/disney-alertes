import os
import json
import requests

# ==========================================
# 1. CONFIGURATION
# ==========================================
# Le nom exact de ton canal dans l'application ntfy
NTFY_TOPIC = "disney-thomas-2026"  

# Mots-clés des 15 attractions cibles (en minuscules pour une correspondance parfaite)
TARGET_ATTRACTIONS = {
    "small world": "It's a Small World",
    "indiana jones": "Indiana Jones et le Temple du Péril",
    "phantom manor": "Phantom Manor",
    "autopia": "Autopia",
    "hyperspace mountain": "Star Wars Hyperspace Mountain",
    "big thunder mountain": "Big Thunder Mountain",
    "peter pan": "Peter Pan's Flight",
    "tower of terror": "The Twilight Zone Tower of Terror",
    "ratatouille": "Ratatouille: L'Aventure Totalement Toquée de Rémy",
    "flight force": "Avengers Assemble: Flight Force",
    "rc racer": "RC Racer",
    "crush": "Crush's Coaster",
    "parachute drop": "Toy Soldiers Parachute Drop",
    "frozen": "Frozen Ever After",
    "pirates of the caribbean": "Pirates of the Caribbean"
}

# IDs des parcs : 4 = Parc Disneyland, 5 = Walt Disney Studios
PARK_IDS = [4, 5]
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
        res = requests.post(url, data=message.encode('utf-8'), headers=headers, timeout=10)
        print(f"Statut d'envoi Ntfy : {res.status_code}")
    except Exception as e:
        print(f"Erreur d'envoi Ntfy: {e}")

def load_previous_states():
    """Charge les états enregistrés lors du dernier passage"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier json : {e}")
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
    
    # Récupération des données depuis l'API Queue-Times pour les 2 parcs
    for park_id in PARK_IDS:
        url = f"https://queue-times.com/parks/{park_id}/queue_times.json"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                print(f"Erreur HTTP {res.status_code} sur le parc {park_id}")
                continue
            
            data = res.json()
            for land in data.get("lands", []):
                for ride in land.get("rides", []):
                    ride_name = ride.get("name", "")
                    
                    # Recherche si l'attraction fait partie de tes 15 cibles
                    for keyword, display_name in TARGET_ATTRACTIONS.items():
                        if keyword in ride_name.lower():
                            current_states[display_name] = {
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
            
            # CAS 1 : RÉOUVERTURE 🚀
            if not was_open and is_open:
                send_ntfy_notification(
                    title=f"🟢 RÉOUVERTURE : {target}",
                    message=f"L'attraction {full_name} vient de réouvrir ! Temps d'attente : {wait_time} min.",
                    priority="high",
                    tags="rocket,green_circle"
                )
                print(f"Alerte envoyée : {target} a réouvert !")
                
            # CAS 2 : FERMETURE ⚠️
            elif was_open and not is_open:
                send_ntfy_notification(
                    title=f"🔴 FERMETURE : {target}",
                    message=f"L'attraction {full_name} est désormais fermée.",
                    priority="default",
                    tags="warning,red_circle"
                )
                print(f"Alerte envoyée : {target} a fermé !")

    # Enregistrement pour la prochaine exécution
    save_current_states(current_states)
    print(f"Vérification terminée. {len(current_states)} attractions mises à jour dans {STATE_FILE}.")

if __name__ == "__main__":
    check_disney_attractions()
    
