# BET INTELLIGENCE AI

Application Streamlit gratuite d'analyse statistique des matchs de football.

## Calendrier automatique
- À chaque première ouverture, l'application récupère automatiquement les rencontres des compétitions suivies.
- Les matchs en direct et à venir sont triés par heure de coup d'envoi, du plus proche au plus éloigné.
- Le calendrier couvre les principales compétitions européennes, américaines, sud-américaines, asiatiques et africaines, ainsi que les coupes continentales et quelques compétitions féminines.
- Le cache est conservé 15 minutes. Le bouton **Actualiser les matchs** force une nouvelle récupération.
- Source : scoreboards publics ESPN, sans clé API ni abonnement. Cette API n'est pas une API officielle garantie ; la disponibilité et la couverture peuvent varier selon les compétitions.

## Lancer sur ordinateur
1. Installer Python 3.10 ou plus récent.
2. Ouvrir un terminal dans ce dossier.
3. Exécuter :
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Déployer gratuitement sur Streamlit Community Cloud
1. Créer un dépôt GitHub et y envoyer `app.py`, `requirements.txt` et le dossier `.streamlit`.
2. Ouvrir https://share.streamlit.io/
3. Connecter GitHub, sélectionner le dépôt et choisir `app.py` comme fichier principal.
4. Cliquer sur Deploy.

## Historique statistique (facultatif)
L'import CSV n'est plus nécessaire pour afficher les rencontres. Il reste facultatif et peut aider à affiner les buts attendus. Colonnes attendues : `Domicile`, `Extérieur`, `Buts domicile`, `Buts extérieur`. La colonne `Terminé` est facultative.

## Modèle et limites
- Le module d'analyse calcule les probabilités avec une distribution de Poisson et une correction Dixon-Coles simplifiée.
- Les cotes saisies servent à estimer la value mathématique.
- Les pronostics enregistrés et résultats saisis sont conservés dans SQLite.
- Le calendrier automatique ne signifie pas que le modèle dispose automatiquement de statistiques historiques complètes pour chaque équipe : sans historique suffisant, des paramètres de départ sont proposés et doivent être ajustés avec prudence.
- Les blessures, compositions, suspensions, météo et mouvements de cotes ne sont pas automatiquement intégrés.
- Les lignes de handicap affichées sont des probabilités simplifiées pour ±0,5, pas une modélisation complète de toutes les lignes asiatiques (¼, ¾, etc.).
- Les probabilités sont des estimations, jamais des garanties de gains.
