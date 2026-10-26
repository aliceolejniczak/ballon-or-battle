import os
import secrets
import string
from datetime import datetime, timezone

import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Ballon d'Or Battle", page_icon="🏆", layout="centered")

st.markdown("""
<style>
.stApp { max-width: 900px; margin: 0 auto; }
.hero { padding: 1.2rem; border-radius: 18px; background: linear-gradient(135deg,#171717,#35302a); color: white; }
.hero h1 { color: #f5d36a; margin-bottom: .2rem; }
.small-muted { color: #a7a7a7; font-size: .9rem; }
</style>
<div class="hero">
<h1>🏆 BALLON D'OR BATTLE</h1>
<p>Vos pronostics. Votre duel. Votre soirée.</p>
</div>
""", unsafe_allow_html=True)

def get_config():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    return url, key

url, key = get_config()
if not url or not key:
    st.error("Il manque la configuration Supabase. Suis les étapes du README, puis ajoute SUPABASE_URL et SUPABASE_KEY dans les secrets de l'application.")
    st.stop()

@st.cache_resource
def supabase_client(url, key) -> Client:
    return create_client(url, key)

sb = supabase_client(url, key)

def rows(table, **filters):
    q = sb.table(table).select("*")
    for k, v in filters.items():
        q = q.eq(k, v)
    return q.execute().data or []

def make_code(n=6):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))

def get_game(code):
    found = rows("games", code=code.upper())
    return found[0] if found else None

def get_players(game_id):
    return sorted(rows("players", game_id=game_id), key=lambda x: x["slot"])

def get_picks(game_id):
    return rows("picks", game_id=game_id)

def get_results(game_id):
    return sorted(rows("results", game_id=game_id), key=lambda x: x["rank"])

def get_player_picks(player_id):
    return rows("picks", player_id=player_id)

def score_pick(predicted_rank, actual_rank):
    base = {1:20, 2:15, 3:12, 4:10, 5:8, 6:6, 7:5, 8:4, 9:3, 10:2}[actual_rank]
    return base - 3 * abs(predicted_rank - actual_rank)

def score_for_player(player, picks, results):
    result_by_name = {r["player_name"].strip().casefold(): r["rank"] for r in results}
    my_picks = [p for p in picks if p["player_id"] == player["id"]]
    total = 0
    details = []
    predicted_names = set()
    for p in my_picks:
        name = p["player_name"].strip()
        keyname = name.casefold()
        predicted_names.add(keyname)
        if keyname in result_by_name:
            actual = result_by_name[keyname]
            pts = score_pick(int(p["predicted_rank"]), int(actual))
            total += pts
            details.append({"Joueur": name, "Ton rang": int(p["predicted_rank"]), "Rang réel": actual, "Points": pts})
        else:
            # A predicted player outside the revealed top 10 incurs a penalty once all 10 results are entered.
            if len(results) >= 10:
                pts = -2
                total += pts
                details.append({"Joueur": name, "Ton rang": int(p["predicted_rank"]), "Rang réel": "Hors Top 10", "Points": pts})
    # A player missing from the submitted Top 10 simply earns no points; no extra penalty.
    return total, details

st.caption("Un jeu privé à deux — pas de compte à créer pour jouer.")

with st.sidebar:
    st.header("Règles du jeu")
    st.markdown("""
**Points selon le rang réel, si le joueur est dans ton Top 10 :**
- 1er : 20 pts
- 2e : 15 pts
- 3e : 12 pts
- 4e : 10 pts
- 5e : 8 pts
- 6e : 6 pts
- 7e : 5 pts
- 8e : 4 pts
- 9e : 3 pts
- 10e : 2 pts

**Précision :** −3 points par place d'écart.  
Ex. : 3e réel, prédit 4e = +9 ; prédit 6e = +3.

Un joueur prédit mais absent du Top 10 officiel vaut −2 points, calculés quand les 10 résultats sont saisis. Un joueur oublié ne rapporte aucun point.
""")

tabs = st.tabs(["Créer une partie", "Rejoindre une partie", "Ma partie"])

with tabs[0]:
    st.subheader("Créer votre duel")
    creator_name = st.text_input("Ton prénom ou pseudo", key="creator_name", placeholder="Ex. Alice")
    if st.button("Créer une partie", type="primary", use_container_width=True):
        if not creator_name.strip():
            st.warning("Entre un pseudo pour continuer.")
        else:
            code = make_code()
            game_resp = sb.table("games").insert({"code": code, "status": "picking"}).execute()
            game = game_resp.data[0]
            player_resp = sb.table("players").insert({
                "game_id": game["id"], "name": creator_name.strip(), "slot": 1,
                "access_token": secrets.token_urlsafe(18)
            }).execute()
            player = player_resp.data[0]
            st.session_state["game_code"] = code
            st.session_state["player_id"] = player["id"]
            st.session_state["access_token"] = player["access_token"]
            st.success(f"Partie créée ! Code à partager : {code}")
            st.info("Garde ce navigateur ouvert ou note le code et ton pseudo. Ton identifiant de joueur est conservé dans cette session.")

with tabs[1]:
    st.subheader("Rejoindre une partie")
    join_code = st.text_input("Code de la partie", key="join_code", max_chars=6).strip().upper()
    join_name = st.text_input("Ton prénom ou pseudo", key="join_name", placeholder="Ex. Sam")
    if st.button("Rejoindre", use_container_width=True):
        game = get_game(join_code) if join_code else None
        if not game:
            st.error("Code introuvable. Vérifie les lettres et chiffres.")
        elif not join_name.strip():
            st.warning("Entre un pseudo.")
        else:
            players = get_players(game["id"])
            if len(players) >= 2:
                st.error("Cette partie a déjà deux joueurs.")
            elif any(p["name"].strip().casefold() == join_name.strip().casefold() for p in players):
                st.error("Ce pseudo est déjà utilisé dans cette partie.")
            else:
                token = secrets.token_urlsafe(18)
                player_resp = sb.table("players").insert({
                    "game_id": game["id"], "name": join_name.strip(), "slot": 2,
                    "access_token": token
                }).execute()
                player = player_resp.data[0]
                st.session_state["game_code"] = join_code
                st.session_state["player_id"] = player["id"]
                st.session_state["access_token"] = token
                st.success("Tu as rejoint la partie ! Passe dans l'onglet « Ma partie ».")

with tabs[2]:
    st.subheader("Ta partie")
    current_code = st.session_state.get("game_code", "")
    current_player_id = st.session_state.get("player_id", "")
    if not current_code or not current_player_id:
        st.info("Crée une partie ou rejoins-en une dans les onglets précédents, puis reviens ici.")
    else:
        game = get_game(current_code)
        if not game:
            st.error("Partie introuvable.")
            st.stop()
        players = get_players(game["id"])
        me = next((p for p in players if p["id"] == current_player_id), None)
        if not me:
            st.error("Session de joueur introuvable. Rejoins de nouveau la partie avec son code.")
            st.stop()
        other = next((p for p in players if p["id"] != current_player_id), None)
        st.markdown(f"**Partie : `{current_code}`** · Tu joues sous le pseudo **{me['name']}**")
        if not other:
            st.warning("En attente du deuxième joueur. Partage le code de la partie.")
        else:
            st.success(f"Vous êtes prêts : {me['name']} et {other['name']}.")

        my_picks = get_player_picks(me["id"])
        all_picks = get_picks(game["id"])
        results = get_results(game["id"])
        locked = bool(me.get("locked", False))
        revealed = game.get("status") == "live"

        st.markdown("### 1. Ton Top 10 secret")
        if not locked:
            st.write("Entre un joueur par ligne et attribue-lui un rang distinct de 1 à 10.")
            existing = {int(p["predicted_rank"]): p["player_name"] for p in my_picks}
            with st.form("picks_form"):
                values = []
                for rank in range(1, 11):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        name = st.text_input(f"{rank}. Joueur", value=existing.get(rank, ""), key=f"pick_name_{rank}")
                    with c2:
                        st.text_input("Rang", value=str(rank), disabled=True, key=f"rank_display_{rank}")
                    values.append((rank, name.strip()))
                confirm = st.checkbox("Je confirme que mon Top 10 est définitif.")
                submitted = st.form_submit_button("Enregistrer mon Top 10", type="primary", use_container_width=True)
            if submitted:
                names = [n.casefold() for _, n in values]
                if not confirm:
                    st.error("Coche la confirmation avant d'enregistrer.")
                elif any(not n for n in names):
                    st.error("Remplis les 10 joueurs.")
                elif len(set(names)) != 10:
                    st.error("Chaque joueur doit apparaître une seule fois.")
                else:
                    # Replace only this player's existing entries.
                    if my_picks:
                        sb.table("picks").delete().eq("player_id", me["id"]).execute()
                    sb.table("picks").insert([
                        {"game_id": game["id"], "player_id": me["id"], "player_name": name, "predicted_rank": rank}
                        for rank, name in values
                    ]).execute()
                    st.success("Top 10 enregistré. Vérifie-le, puis verrouille-le.")
                    st.rerun()
            if len(my_picks) == 10:
                if st.button("🔒 Verrouiller définitivement mon Top 10", type="primary", use_container_width=True):
                    sb.table("players").update({"locked": True}).eq("id", me["id"]).execute()
                    st.success("Ton Top 10 est verrouillé.")
                    st.rerun()
        else:
            st.success("Ton Top 10 est verrouillé.")
            st.caption("Tes choix ne peuvent plus être modifiés.")
            st.dataframe([{"Rang prédit": p["predicted_rank"], "Joueur": p["player_name"]} for p in sorted(my_picks, key=lambda x: x["predicted_rank"])], hide_index=True, use_container_width=True)

        # Do not show other player's picks until both have locked and a player explicitly starts live mode.
        players = get_players(game["id"])
        both_locked = len(players) == 2 and all(p.get("locked", False) for p in players)
        st.markdown("### 2. Révélation en direct")
        if both_locked and game.get("status") != "live":
            st.info("Les deux Top 10 sont verrouillés. Vous pouvez lancer la révélation.")
            if st.button("🎬 Démarrer la cérémonie", type="primary", use_container_width=True):
                sb.table("games").update({"status": "live"}).eq("id", game["id"]).execute()
                st.rerun()
        elif not both_locked:
            st.caption("La révélation sera disponible lorsque les deux joueurs auront verrouillé leur Top 10.")
        else:
            st.write("À chaque joueur annoncé, ajoutez son nom exactement comme dans les pronostics et son rang officiel.")
            with st.form("result_form"):
                actual_name = st.text_input("Joueur annoncé", placeholder="Ex. Fabian Ruiz")
                actual_rank = st.selectbox("Rang officiel", options=list(range(1, 11)))
                add_result = st.form_submit_button("Enregistrer la révélation", use_container_width=True)
            if add_result:
                if not actual_name.strip():
                    st.error("Entre le nom du joueur.")
                elif any(r["rank"] == actual_rank for r in results):
                    st.error(f"Le rang {actual_rank} est déjà attribué. Supprime ou corrige le résultat existant dans Supabase.")
                elif any(r["player_name"].strip().casefold() == actual_name.strip().casefold() for r in results):
                    st.error("Ce joueur a déjà été enregistré.")
                else:
                    sb.table("results").insert({
                        "game_id": game["id"], "player_name": actual_name.strip(), "rank": actual_rank
                    }).execute()
                    st.rerun()

            if results:
                st.markdown("#### Joueurs déjà révélés")
                st.dataframe([{"Rang réel": r["rank"], "Joueur": r["player_name"]} for r in results], hide_index=True, use_container_width=True)
                st.markdown("#### Scores provisoires")
                all_picks = get_picks(game["id"])
                score_rows = []
                for p in players:
                    total, _ = score_for_player(p, all_picks, results)
                    score_rows.append({"Joueur": p["name"], "Score": total, "Top 10 verrouillé": p.get("locked", False)})
                st.dataframe(score_rows, hide_index=True, use_container_width=True)
                with st.expander("Voir les points détaillés"):
                    for p in players:
                        total, details = score_for_player(p, all_picks, results)
                        st.markdown(f"**{p['name']} — {total} points**")
                        if details:
                            st.dataframe(details, hide_index=True, use_container_width=True)
                        else:
                            st.caption("Aucun point calculé pour l'instant.")
            if len(results) == 10:
                st.balloons()
                st.success("Top 10 complet ! Le duel est terminé.")
        st.caption("Astuce : actualise la page pour voir les changements effectués depuis l'autre téléphone.")
