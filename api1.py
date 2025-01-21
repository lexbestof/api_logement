import requests
from bs4 import BeautifulSoup
import time


URL = "https://teleservices.paris.fr/locannonces/"
SEEN_ANNOUNCES = set()  # Pour stocker les annonces déjà vues
CHECK_INTERVAL = 120  # Temps d'attente entre les requêtes (en secondes)


def fetch_announces():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()  # Vérifie les erreurs HTTP
        soup = BeautifulSoup(response.text, 'html.parser')

        announces = []
        for link in soup.select('a[href^="logement/"]'):
            annonce_id = link['href'].split('/')[-1]  # Extraire l'ID unique
            annonce_url = f"{URL}{link['href']}"  # Construire l'URL complète
            details = {
                "id": annonce_id,
                "url": annonce_url,
                "type": link.find_next("p", class_="lgtInfo").get_text(strip=True) if link.find_next("p", class_="lgtInfo") else "Inconnu",
                "loyer": link.find_next("p", class_="loyer").get_text(strip=True) if link.find_next("p", class_="loyer") else "Inconnu",
                "ville": link.find_next("p", class_="ville").get_text(strip=True) if link.find_next("p", class_="ville") else "Inconnu",
            }
            announces.append(details)
        return announces
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération des annonces : {e}")
        return []



def check_for_new_announces():
    global SEEN_ANNOUNCES
    announces = fetch_announces()
    new_announces = []
    for annonce in announces:
        annonce_id = annonce['id']  # ID unique de l'annonce
        if annonce_id not in SEEN_ANNOUNCES:
            SEEN_ANNOUNCES.add(annonce_id)
            new_announces.append(annonce)
    return new_announces


def save_announces_to_file(announces, filename="new_announces.txt"):
    try:
        with open(filename, "a", encoding="utf-8") as file:  # Ajout de l'encodage UTF-8
            for annonce in announces:
                file.write(
                    f"ID: {annonce['id']}, Type: {annonce['type']}, Loyer: {annonce['loyer']}, Ville: {annonce['ville']}\n"
                )
    except IOError as e:
        print(f"Erreur lors de la sauvegarde des annonces dans le fichier : {e}")



def load_seen_announces(filename="seen_announces.txt"):
    try:
        with open(filename, "r") as file:
            return set(line.strip() for line in file)
    except FileNotFoundError:
        return set()


def save_seen_announces(filename="seen_announces.txt"):
    try:
        with open(filename, "w") as file:
            for annonce_id in SEEN_ANNOUNCES:
                file.write(f"{annonce_id}\n")
    except IOError as e:
        print(f"Erreur lors de la sauvegarde des annonces vues : {e}")


# Charger les annonces déjà vues au démarrage
SEEN_ANNOUNCES = load_seen_announces()

#Envoie des notifications telegram
TELEGRAM_BOT_TOKEN = "7588764616:AAHGHD6y3u2cqZRLN4ajxHvyox_3mrm4R88"
def send_telegram_notification(message):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": 1841906795, "text": message}
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Erreur lors de l'envoi de la notification Telegram : {e}")


# Boucle principale
try:
    while True:
        new_announces = check_for_new_announces()
        
        if new_announces:
            print(f"⚠️ Nouvelle(s) annonce(s) détectée(s) : {len(new_announces)}")
            save_announces_to_file(new_announces)  # Enregistre les nouvelles annonces dans le fichier
            save_seen_announces()  # Sauvegarde l'état des annonces vues
            for annonce in new_announces:
                message = (
                    f"Nouvelle annonce détectée\n"
                    f"Type: {annonce['type']}\n"
                    f"Loyer: {annonce['loyer']}\n"
                    f"Ville: {annonce['ville']}\n"
                    f"URL: {annonce['url']}"
                )
                send_telegram_notification(message)
        else:
            print("Aucune nouvelle annonce détectée.")

        time.sleep(CHECK_INTERVAL)
except KeyboardInterrupt:
    print("\nArrêt du script.")
    save_seen_announces()  # Sauvegarde finale des annonces vues
