# Ballon d'Or Battle — Python + Streamlit

Mini-app pour deux joueurs : Top 10 secret, verrouillage individuel, révélation des rangs officiels et calcul des scores.

## Ce qu'il faut
- Un compte gratuit Supabase : https://supabase.com/
- Un compte GitHub : https://github.com/
- Streamlit Community Cloud : https://share.streamlit.io/

## 1. Créer la base Supabase
1. Crée un projet sur Supabase.
2. Ouvre **SQL Editor** → **New query**.
3. Copie-colle tout le contenu de `supabase_schema.sql`, puis clique sur **Run**.
4. Dans **Project Settings → API** (ou **Connect** selon l'interface), récupère :
   - l'URL du projet (`Project URL`)
   - la clé secrète serveur `service_role` / `secret key`.
5. Garde la clé secrète privée. Elle ne doit jamais être publiée dans GitHub ou partagée.

## 2. Mettre les fichiers sur GitHub
1. Crée un dépôt GitHub, par exemple `ballon-or-battle`.
2. Ajoute `app.py`, `requirements.txt` et `supabase_schema.sql`.
3. Ne mets pas la clé Supabase dans le dépôt.

## 3. Déployer Streamlit
1. Va sur https://share.streamlit.io/ et connecte GitHub.
2. Choisis le dépôt et `app.py` comme fichier principal.
3. Dans les paramètres avancés / **Secrets**, ajoute exactement :

```toml
SUPABASE_URL = "https://TON-PROJET.supabase.co"
SUPABASE_KEY = "TA_CLE_SECRETE_SUPABASE"
```

4. Déploie. Une URL publique sera créée : partage-la avec ton copain.

## 4. Jouer
1. Ouvre l'application et crée une partie avec ton pseudo.
2. Partage le code de 6 caractères avec ton copain.
3. Chacun remplit son Top 10 sur son téléphone.
4. Chacun clique sur **Verrouiller définitivement mon Top 10**.
5. Une fois les deux Top 10 verrouillés, démarrez la cérémonie.
6. À chaque joueur annoncé, saisissez son nom et son rang officiel. Utilisez toujours la même orthographe que dans vos pronostics.

## Barème
- Rang réel 1 à 10 : respectivement 20, 15, 12, 10, 8, 6, 5, 4, 3, 2 points de base.
- On retire 3 points par place d'écart avec le rang réel.
- Un joueur prédit mais absent du Top 10 officiel vaut -2 points, une fois les 10 rangs saisis.
- Un joueur officiel oublié dans un Top 10 ne rapporte aucun point.

## Limites à connaître
- La configuration est gratuite dans les limites des offres gratuites des services, qui peuvent évoluer.
- L'application utilise une clé serveur Supabase côté Streamlit. Le code public ne contient pas cette clé, mais l'application reste un petit projet personnel, pas une plateforme auditée pour des données sensibles.
- La version actuelle ne propose pas de bouton pour corriger/supprimer un résultat erroné. En cas d'erreur, il faudra corriger la ligne dans Supabase ou ajouter cette fonction.
- Le code de partie n'est pas un mécanisme d'authentification fort. Ne l'utilisez pas pour des données privées.
