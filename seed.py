from sqlalchemy.orm import Session
from models import Role, User, Player, Map, Match, PlayerMatchStats

def seed_data(db: Session):
    if db.query(Role).first():
        print("Fixtures exista deja in baza de date.")
        return

    print("Se introduc datele de test (Fixtures)...")

    role_admin = Role(name="Admin", description="Acces complet la toate operatiile si administrare")
    role_premium = Role(name="Premium", description="Acces la rapoarte avansate si export PDF/CSV")
    role_standard = Role(name="Standard", description="Acces de baza pentru vizualizarea statisticilor")
    db.add_all([role_admin, role_premium, role_standard])
    db.commit()

    users = [
        User(username="admin_cs2", email="admin@cs2tracker.ro", password_hash="hashed_secret_1", role_id=role_admin.id),
        User(username="pro_player", email="pro@cs2tracker.ro", password_hash="hashed_secret_2", role_id=role_premium.id),
        User(username="casual_user", email="casual@cs2tracker.ro", password_hash="hashed_secret_3", role_id=role_standard.id),
    ]
    db.add_all(users)

    mirage = Map(name="de_mirage", is_active_duty=1)
    inferno = Map(name="de_inferno", is_active_duty=1)
    nuke = Map(name="de_nuke", is_active_duty=1)
    dust2 = Map(name="de_dust2", is_active_duty=1)
    db.add_all([mirage, inferno, nuke, dust2])
    db.commit()

    p1 = Player(steam_id="76561198000000001", nickname="s1mple_ro", avatar_url="https://example.com/a1.png")
    p2 = Player(steam_id="76561198000000002", nickname="ZywOo_fan", avatar_url="https://example.com/a2.png")
    p3 = Player(steam_id="76561198000000003", nickname="iM_legend", avatar_url="https://example.com/a3.png")
    db.add_all([p1, p2, p3])
    db.commit()

    m1 = Match(map_id=mirage.id, team_ct_score=13, team_t_score=9)
    m2 = Match(map_id=inferno.id, team_ct_score=11, team_t_score=13)
    db.add_all([m1, m2])
    db.commit()

    stats = [
        PlayerMatchStats(player_id=p1.id, match_id=m1.id, kills=24, deaths=14, assists=5, adr=98.5, headshot_percentage=54.2),
        PlayerMatchStats(player_id=p2.id, match_id=m1.id, kills=18, deaths=17, assists=4, adr=76.0, headshot_percentage=44.0),
        PlayerMatchStats(player_id=p3.id, match_id=m2.id, kills=28, deaths=16, assists=7, adr=105.3, headshot_percentage=62.5),
    ]
    db.add_all(stats)
    db.commit()
    print("Fixtures au fost introduse cu succes!")