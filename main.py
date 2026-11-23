import json
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

import models
import schemas
from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_roles,
    verify_password,
)
from database import Base, SessionLocal, engine, get_db
from seed import seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="CS2 Stats Tracker API - Proiect BD2",
    description="Monitorizarea si inregistrarea statisticilor jucatorilor de CS2",
    lifespan=lifespan
)


@app.get("/", tags=["General"])
def read_root():
    return FileResponse("static/index.html")


# 0. AUTENTIFICARE SI VERIFICARE ROL CURENT (ETAPA 3)

@app.post("/login", tags=["0. Autentificare & Roluri"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username sau parola incorecta"
        )
    token = create_access_token(data={"sub": user.username, "role": user.role.name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role.name
    }


@app.get("/me", tags=["0. Autentificare & Roluri"])
def get_my_profile(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.name,
        "permissions_description": current_user.role.description
    }


@app.get("/analytics/advanced", tags=["0. Autentificare & Roluri"])
def get_advanced_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin", "Premium"]))
):
    """Ruta accesibila DOAR pentru rolurile Premium si Admin."""
    stats = db.query(models.PlayerMatchStats).all()
    total_kills = sum(s.kills for s in stats)
    avg_adr = round(sum(s.adr for s in stats) / len(stats), 2) if stats else 0
    return {
        "access_level": current_user.role.name,
        "total_recorded_kills": total_kills,
        "global_average_adr": avg_adr,
        "message": "Statistici avansate deblocate pentru conturi Premium/Admin."
    }


# 1. CRUD PENTRU ROLES (Modificari permise doar pentru Admin)

@app.post("/roles", response_model=schemas.RoleResponse, tags=["1. Roles CRUD"])
def create_role(
    role: schemas.RoleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    db_role = models.Role(**role.model_dump())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


@app.get("/roles", response_model=List[schemas.RoleResponse], tags=["1. Roles CRUD"])
def get_roles(db: Session = Depends(get_db)):
    return db.query(models.Role).all()


@app.get("/roles/{role_id}", response_model=schemas.RoleResponse, tags=["1. Roles CRUD"])
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rolul nu a fost gasit")
    return role


@app.put("/roles/{role_id}", response_model=schemas.RoleResponse, tags=["1. Roles CRUD"])
def update_role(
    role_id: int,
    role_data: schemas.RoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rolul nu a fost gasit")
    for key, value in role_data.model_dump(exclude_unset=True).items():
        setattr(role, key, value)
    db.commit()
    db.refresh(role)
    return role


@app.delete("/roles/{role_id}", tags=["1. Roles CRUD"])
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rolul nu a fost gasit")
    db.delete(role)
    db.commit()
    return {"message": f"Rolul cu ID {role_id} a fost sters"}


# 2. CRUD PENTRU USERS (Inregistrare publica, stergere doar Admin)

@app.post("/users", response_model=schemas.UserResponse, tags=["2. Users CRUD"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        role_id=user.role_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users", response_model=List[schemas.UserResponse], tags=["2. Users CRUD"])
def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    return db.query(models.User).all()


@app.get("/users/{user_id}", response_model=schemas.UserResponse, tags=["2. Users CRUD"])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin", "Premium", "Standard"]))
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost gasit")
    return user


@app.put("/users/{user_id}", response_model=schemas.UserResponse, tags=["2. Users CRUD"])
def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost gasit")
    update_dict = user_data.model_dump(exclude_unset=True)
    if "password" in update_dict:
        update_dict["password_hash"] = hash_password(update_dict.pop("password"))
    for key, value in update_dict.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}", tags=["2. Users CRUD"])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost gasit")
    db.delete(user)
    db.commit()
    return {"message": f"Utilizatorul cu ID {user_id} a fost sters"}


# 3. CRUD PENTRU PLAYERS (Citire: toti | Creare/Editare: Premium & Admin | Stergere: Admin)

@app.post("/players", response_model=schemas.PlayerResponse, tags=["3. Players CRUD"])
def create_player(
    player: schemas.PlayerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin", "Premium"]))
):
    db_player = models.Player(
        **player.model_dump(),
        is_manual=(current_user.role.name == "Premium")
    )
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


@app.get("/players", response_model=List[schemas.PlayerResponse], tags=["3. Players CRUD"])
def get_players(db: Session = Depends(get_db)):
    return db.query(models.Player).all()


@app.get("/players/{player_id}", response_model=schemas.PlayerResponse, tags=["3. Players CRUD"])
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jucatorul nu a fost gasit")
    return player


@app.put("/players/{player_id}", response_model=schemas.PlayerResponse, tags=["3. Players CRUD"])
def update_player(
    player_id: int,
    player_data: schemas.PlayerUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin", "Premium"]))
):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jucatorul nu a fost gasit")
    for key, value in player_data.model_dump(exclude_unset=True).items():
        setattr(player, key, value)
    db.commit()
    db.refresh(player)
    return player


@app.delete("/players/{player_id}", tags=["3. Players CRUD"])
def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jucatorul nu a fost gasit")
    db.delete(player)
    db.commit()
    return {"message": f"Jucatorul cu ID {player_id} a fost sters"}


# 4. CRUD PENTRU MAPS (Citire: toti | Modificare/Stergere: Admin)

@app.post("/maps", response_model=schemas.MapResponse, tags=["4. Maps CRUD"])
def create_map(
    game_map: schemas.MapCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    db_map = models.Map(**game_map.model_dump())
    db.add(db_map)
    db.commit()
    db.refresh(db_map)
    return db_map


@app.get("/maps", response_model=List[schemas.MapResponse], tags=["4. Maps CRUD"])
def get_maps(db: Session = Depends(get_db)):
    return db.query(models.Map).all()


@app.get("/maps/{map_id}", response_model=schemas.MapResponse, tags=["4. Maps CRUD"])
def get_map(map_id: int, db: Session = Depends(get_db)):
    game_map = db.query(models.Map).filter(models.Map.id == map_id).first()
    if not game_map:
        raise HTTPException(status_code=404, detail="Harta nu a fost gasita")
    return game_map


@app.put("/maps/{map_id}", response_model=schemas.MapResponse, tags=["4. Maps CRUD"])
def update_map(
    map_id: int,
    map_data: schemas.MapUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    game_map = db.query(models.Map).filter(models.Map.id == map_id).first()
    if not game_map:
        raise HTTPException(status_code=404, detail="Harta nu a fost gasita")
    for key, value in map_data.model_dump(exclude_unset=True).items():
        setattr(game_map, key, value)
    db.commit()
    db.refresh(game_map)
    return game_map


@app.delete("/maps/{map_id}", tags=["4. Maps CRUD"])
def delete_map(
    map_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    game_map = db.query(models.Map).filter(models.Map.id == map_id).first()
    if not game_map:
        raise HTTPException(status_code=404, detail="Harta nu a fost gasita")
    db.delete(game_map)
    db.commit()
    return {"message": f"Harta cu ID {map_id} a fost stearsa"}


# 5. CRUD PENTRU MATCHES (Citire: toti | Adaugare: Premium & Admin | Stergere: Admin)

@app.post("/matches", response_model=schemas.MatchResponse, tags=["5. Matches CRUD"])
def create_match(
    match: schemas.MatchCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin", "Premium"]))
):
    db_match = models.Match(**match.model_dump())
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match


@app.get("/matches", response_model=List[schemas.MatchResponse], tags=["5. Matches CRUD"])
def get_matches(db: Session = Depends(get_db)):
    return db.query(models.Match).all()


@app.get("/matches/{match_id}", response_model=schemas.MatchResponse, tags=["5. Matches CRUD"])
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Meciul nu a fost gasit")
    return match


@app.put("/matches/{match_id}", response_model=schemas.MatchResponse, tags=["5. Matches CRUD"])
def update_match(
    match_id: int,
    match_data: schemas.MatchUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin", "Premium"]))
):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Meciul nu a fost gasit")
    for key, value in match_data.model_dump(exclude_unset=True).items():
        setattr(match, key, value)
    db.commit()
    db.refresh(match)
    return match


@app.delete("/matches/{match_id}", tags=["5. Matches CRUD"])
def delete_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Meciul nu a fost gasit")
    db.delete(match)
    db.commit()
    return {"message": f"Meciul cu ID {match_id} a fost sters"}


# 6. CRUD PENTRU PLAYER_MATCH_STATS

@app.post("/stats", response_model=schemas.PlayerMatchStatsResponse, tags=["6. Player Match Stats CRUD"])
def create_stats(
    stats: schemas.PlayerMatchStatsCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin", "Premium"]))
):
    db_stats = models.PlayerMatchStats(**stats.model_dump())
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)
    return db_stats


@app.get("/stats", response_model=List[schemas.PlayerMatchStatsResponse], tags=["6. Player Match Stats CRUD"])
def get_all_stats(db: Session = Depends(get_db)):
    return db.query(models.PlayerMatchStats).all()


@app.get("/stats/{stat_id}", response_model=schemas.PlayerMatchStatsResponse, tags=["6. Player Match Stats CRUD"])
def get_stat(stat_id: int, db: Session = Depends(get_db)):
    stat = db.query(models.PlayerMatchStats).filter(models.PlayerMatchStats.id == stat_id).first()
    if not stat:
        raise HTTPException(status_code=404, detail="Statistica nu a fost gasita")
    return stat


@app.put("/stats/{stat_id}", response_model=schemas.PlayerMatchStatsResponse, tags=["6. Player Match Stats CRUD"])
def update_stat(
    stat_id: int,
    stat_data: schemas.PlayerMatchStatsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin", "Premium"]))
):
    stat = db.query(models.PlayerMatchStats).filter(models.PlayerMatchStats.id == stat_id).first()
    if not stat:
        raise HTTPException(status_code=404, detail="Statistica nu a fost gasita")
    for key, value in stat_data.model_dump(exclude_unset=True).items():
        setattr(stat, key, value)
    db.commit()
    db.refresh(stat)
    return stat


@app.delete("/stats/{stat_id}", tags=["6. Player Match Stats CRUD"])
def delete_stat(
    stat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    stat = db.query(models.PlayerMatchStats).filter(models.PlayerMatchStats.id == stat_id).first()
    if not stat:
        raise HTTPException(status_code=404, detail="Statistica nu a fost gasita")
    db.delete(stat)
    db.commit()
    return {"message": f"Statistica cu ID {stat_id} a fost stearsa"}


# 7. ETAPA 4: PERFORMANTA (GENERATOR DATE, INDECSI SI PLANURI EXECUTIE)

@app.post("/admin/generate-bulk", tags=["7. Performanta (Indecsi & Load Test)"])
def generate_bulk_data(
    count: int = 2000,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    """Genereaza rapid mii de jucatori si statistici pentru testarea indecsilor si Load Test."""
    start_time = time.perf_counter()
    maps = db.query(models.Map).all()
    map_id = maps[0].id if maps else 1

    match = db.query(models.Match).first()
    if not match:
        match = models.Match(map_id=map_id, team_ct_score=13, team_t_score=10)
        db.add(match)
        db.commit()
        db.refresh(match)

    existing_count = db.query(models.Player).count()
    new_players = []
    for i in range(existing_count + 1, existing_count + count + 1):
        new_players.append(models.Player(
            steam_id=f"7656119{i:010d}",
            nickname=f"CS2_Player_{i}",
            avatar_url="https://example.com/avatar.png"
        ))
    db.bulk_save_objects(new_players)
    db.commit()

    all_pids = [r[0] for r in db.query(models.Player.id).order_by(models.Player.id.desc()).limit(count).all()]
    new_stats = []
    for pid in all_pids:
        for _ in range(3):
            new_stats.append(models.PlayerMatchStats(
                player_id=pid,
                match_id=match.id,
                kills=random.randint(5, 35),
                deaths=random.randint(5, 25),
                assists=random.randint(0, 12),
                adr=round(random.uniform(45.0, 115.0), 1),
                headshot_percentage=round(random.uniform(20.0, 75.0), 1)
            ))
    db.bulk_save_objects(new_stats)
    db.commit()

    elapsed = round((time.perf_counter() - start_time) * 1000, 2)
    return {
        "message": f"S-au generat {count} jucatori si {count * 3} statistici de meci in {elapsed} ms!",
        "total_players": db.query(models.Player).count(),
        "total_stats": db.query(models.PlayerMatchStats).count()
    }


@app.post("/admin/benchmark-indexes", tags=["7. Performanta (Indecsi & Load Test)"])
def benchmark_indexes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    """Compara planul de executie (EXPLAIN / EXPLAIN QUERY PLAN) si timpul de rulare INAINTE si DUPA indecsi."""
    explain_cmd = "EXPLAIN QUERY PLAN" if str(engine.url).startswith("sqlite") else "EXPLAIN"
    query_sql = """
        SELECT p.nickname, s.kills, s.adr, s.headshot_percentage
        FROM player_match_stats s
        JOIN players p ON s.player_id = p.id
        WHERE s.kills >= 28 AND s.adr >= 95.0
        ORDER BY s.adr DESC
        LIMIT 50
    """

    # 1. Stergem indecsii ca sa masuram performanta FARA indecsi
    db.execute(text("DROP INDEX IF EXISTS idx_stats_kills_adr"))
    db.execute(text("DROP INDEX IF EXISTS idx_stats_player_id"))
    db.commit()

    plan_before_rows = db.execute(text(f"{explain_cmd} {query_sql}")).fetchall()
    plan_before = " | ".join([str(r[-1]) for r in plan_before_rows])

    t0 = time.perf_counter()
    for _ in range(20):
        db.execute(text(query_sql)).fetchall()
    time_before_ms = round((time.perf_counter() - t0) * 1000, 2)

    # 2. Cream indecsii compusi pe coloanele filtrate si de JOIN
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_stats_kills_adr ON player_match_stats (kills, adr DESC)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_stats_player_id ON player_match_stats (player_id)"))
    db.commit()

    plan_after_rows = db.execute(text(f"{explain_cmd} {query_sql}")).fetchall()
    plan_after = " | ".join([str(r[-1]) for r in plan_after_rows])

    t1 = time.perf_counter()
    for _ in range(20):
        db.execute(text(query_sql)).fetchall()
    time_after_ms = round((time.perf_counter() - t1) * 1000, 2)

    return {
        "total_stats_rows": db.query(models.PlayerMatchStats).count(),
        "before_indexes": {
            "execution_plan": plan_before,
            "time_20_runs_ms": time_before_ms
        },
        "after_indexes": {
            "execution_plan": plan_after,
            "time_20_runs_ms": time_after_ms
        }
    }


@app.delete("/admin/clear-bots", tags=["7. Performanta (Indecsi & Load Test)"])
def clear_generated_bots(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    """Sterge toti jucatorii generati automat (CS2_Player_*) si statisticile lor."""
    bot_ids = [r[0] for r in db.query(models.Player.id).filter(models.Player.nickname.like("CS2_Player_%")).all()]
    if not bot_ids:
        return {"message": "Nu exista boti generati de sters."}

    db.query(models.PlayerMatchStats).filter(models.PlayerMatchStats.player_id.in_(bot_ids)).delete(synchronize_session=False)
    deleted_count = db.query(models.Player).filter(models.Player.id.in_(bot_ids)).delete(synchronize_session=False)
    db.commit()
    return {"message": f"Au fost stersi {deleted_count} boti si toate statisticile lor!"}


# 8. INTEGRARE STEAM WEB API (IMPORT JUCATOR DIRECT DIN STEAM)

STEAM_API_KEY = os.getenv("STEAM_API_KEY", "PUNE_CHEIA_TA_AICI_DOAR_LOCAL")


@app.post("/players/import-steam/{steam_id}", tags=["3. Players CRUD"])
def import_player_from_steam(
    steam_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin", "Premium"]))
):
    """Preia nickname, avatar si statistici CS2 direct din Steam Web API."""
    if not STEAM_API_KEY or STEAM_API_KEY == "PUNE_CHEIA_TA_AICI_DOAR_LOCAL":
        raise HTTPException(status_code=400, detail="Lipseste STEAM_API_KEY! Configureaza cheia in server.")

    # 0. Daca nu este un SteamID64 (17 cifre), il convertim din Custom URL (Vanity URL)
    if not (steam_id.isdigit() and len(steam_id) == 17):
        vanity_url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={steam_id}"
        try:
            with urllib.request.urlopen(vanity_url, timeout=10) as resp:
                vanity_data = json.loads(resp.read().decode()).get("response", {})
                if vanity_data.get("success") == 1:
                    steam_id = vanity_data["steamid"]
                else:
                    raise HTTPException(status_code=404, detail=f"Nu a fost gasit niciun profil Steam cu numele '{steam_id}'.")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Eroare la rezolvarea linkului Steam: {str(e)}")

    # 1. Cerem datele de profil (Nickname + Avatar)
    summary_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steam_id}"
    try:
        with urllib.request.urlopen(summary_url, timeout=10) as resp:
            summary_data = json.loads(resp.read().decode())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Eroare comunicare cu Steam API: {str(e)}")

    players_list = summary_data.get("response", {}).get("players", [])
    if not players_list:
        raise HTTPException(status_code=404, detail="Nu a fost gasit niciun cont Steam cu acest SteamID64.")

    steam_user = players_list[0]
    nickname = steam_user.get("personaname", f"Steam_{steam_id[-4:]}")
    avatar_url = steam_user.get("avatarfull", "")

    db_player = db.query(models.Player).filter(models.Player.steam_id == steam_id).first()
    if not db_player:
        db_player = models.Player(steam_id=steam_id, nickname=nickname, avatar_url=avatar_url)
        db.add(db_player)
        db.commit()
        db.refresh(db_player)
    else:
        db_player.nickname = nickname
        db_player.avatar_url = avatar_url
        db.commit()

    # 2. Cerem statisticile de CS2 (AppID 730)
    stats_msg = "Profil importat! (Statisticile CS2 sunt private pe Steam)."
    stats_url = f"https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v2/?appid=730&key={STEAM_API_KEY}&steamid={steam_id}"
    try:
        with urllib.request.urlopen(stats_url, timeout=10) as resp:
            stats_data = json.loads(resp.read().decode())
            raw_stats = {s["name"]: s["value"] for s in stats_data.get("playerstats", {}).get("stats", [])}

            total_kills = raw_stats.get("total_kills", 0)
            total_deaths = raw_stats.get("total_deaths", 1)
            total_hs = raw_stats.get("total_kills_headshot", 0)
            total_dmg = raw_stats.get("total_damage_done", 0)
            total_rounds = raw_stats.get("total_rounds_played", 1)

            hs_pct = round((total_hs / total_kills) * 100, 1) if total_kills > 0 else 0.0
            adr = round(total_dmg / total_rounds, 1) if total_rounds > 0 else 0.0

            match = db.query(models.Match).first()
            if match and total_kills > 0:
                db_stat = models.PlayerMatchStats(
                    player_id=db_player.id,
                    match_id=match.id,
                    kills=total_kills,
                    deaths=total_deaths,
                    assists=0,
                    adr=min(adr, 500.0),
                    headshot_percentage=min(hs_pct, 100.0)
                )
                db.add(db_stat)
                db.commit()
                stats_msg = f"Profil + statistici CS2 importate (Kills: {total_kills}, ADR: {adr}, HS%: {hs_pct}%)!"
    except urllib.error.HTTPError:
        pass
    except Exception:
        pass

    return {
        "message": stats_msg,
        "player": {
            "id": db_player.id,
            "nickname": db_player.nickname,
            "steam_id": db_player.steam_id,
            "avatar_url": db_player.avatar_url
        }
    }


# 9. LOGIN CU STEAM, UPGRADE PREMIUM (1 EUR), DOWNGRADE & EDITARE PROFIL

class SteamLoginRequest(BaseModel):
    steam_input: str


class ProfileUpdateRequest(BaseModel):
    nickname: str
    avatar_url: str = ""


@app.post("/login-steam", tags=["0. Autentificare & Roluri"])
def login_with_steam(payload: SteamLoginRequest, db: Session = Depends(get_db)):
    """Logare sau creare automata de cont Standard direct cu SteamID / link Steam."""
    raw = payload.steam_input.strip()
    steam_id = raw

    m_prof = re.search(r"7656\d{13}", raw)
    m_vanity = re.search(r"steamcommunity\.com/id/([^/?#]+)", raw, re.IGNORECASE)
    if m_prof:
        steam_id = m_prof.group(0)
    elif m_vanity:
        steam_id = m_vanity.group(1)

    if not (steam_id.isdigit() and len(steam_id) == 17) and STEAM_API_KEY and STEAM_API_KEY != "PUNE_CHEIA_TA_AICI_DOAR_LOCAL":
        try:
            v_url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={steam_id}"
            with urllib.request.urlopen(v_url, timeout=8) as resp:
                v_data = json.loads(resp.read().decode()).get("response", {})
                if v_data.get("success") == 1:
                    steam_id = v_data["steamid"]
        except Exception:
            pass

    if not steam_id:
        raise HTTPException(status_code=400, detail="Introdu un SteamID64 sau un link de profil Steam valid.")

    user = db.query(models.User).filter(models.User.steam_id == steam_id).first()
    if not user:
        standard_role = db.query(models.Role).filter(models.Role.name == "Standard").first()
        if not standard_role:
            raise HTTPException(status_code=500, detail="Rolul Standard nu exista in baza de date.")

        nickname = f"Steam_{steam_id[-6:]}"
        avatar_url = ""
        if STEAM_API_KEY and STEAM_API_KEY != "PUNE_CHEIA_TA_AICI_DOAR_LOCAL" and steam_id.isdigit():
            try:
                s_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steam_id}"
                with urllib.request.urlopen(s_url, timeout=8) as resp:
                    plist = json.loads(resp.read().decode()).get("response", {}).get("players", [])
                    if plist:
                        nickname = plist[0].get("personaname", nickname)
                        avatar_url = plist[0].get("avatarfull", "")
            except Exception:
                pass

        unique_username = f"{nickname}_{steam_id[-4:]}"
        user = models.User(
            username=unique_username,
            email=f"{steam_id}@steam.local",
            password_hash=hash_password(f"steam_oauth_{steam_id}"),
            role_id=standard_role.id,
            steam_id=steam_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        player = db.query(models.Player).filter(models.Player.steam_id == steam_id).first()
        if not player:
            player = models.Player(steam_id=steam_id, nickname=nickname, avatar_url=avatar_url, is_manual=False)
            db.add(player)
            db.commit()

    token = create_access_token(data={"sub": user.username, "role": user.role.name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role.name,
        "steam_id": user.steam_id
    }


@app.post("/me/upgrade", tags=["0. Autentificare & Roluri"])
def upgrade_to_premium(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Simuleaza o subscriptie de 1 EUR/luna si face upgrade contului la Premium."""
    premium_role = db.query(models.Role).filter(models.Role.name == "Premium").first()
    if not premium_role:
        raise HTTPException(status_code=500, detail="Rolul Premium nu a fost gasit.")

    current_user.role_id = premium_role.id
    db.commit()
    db.refresh(current_user)

    new_token = create_access_token(data={"sub": current_user.username, "role": "Premium"})
    return {
        "message": "Felicitari! Subscriptia de 1 EUR/luna a fost activata. Ai acum cont Premium!",
        "access_token": new_token,
        "username": current_user.username,
        "role": "Premium",
        "steam_id": current_user.steam_id
    }


@app.put("/me/profile", tags=["0. Autentificare & Roluri"])
def update_my_player_profile(
    data: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Premium", "Admin"]))
):
    """Permite conturilor Premium/Admin sa isi modifice propriul profil de jucator."""
    if not current_user.steam_id:
        raise HTTPException(status_code=400, detail="Contul tau nu are un profil Steam asociat.")
    player = db.query(models.Player).filter(models.Player.steam_id == current_user.steam_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Profilul de jucator nu a fost gasit.")

    player.nickname = data.nickname
    if data.avatar_url:
        player.avatar_url = data.avatar_url
    db.commit()
    return {"message": f"Profilul tau a fost actualizat la nickname-ul '{player.nickname}'!"}


@app.post("/admin/downgrade/{user_id}", tags=["0. Autentificare & Roluri"])
def downgrade_user_to_standard(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["Admin"]))
):
    """Permite Adminului sa dea downgrade unui cont Premium inapoi la Standard."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost gasit.")
    standard_role = db.query(models.Role).filter(models.Role.name == "Standard").first()
    user.role_id = standard_role.id
    db.commit()
    return {"message": f"Utilizatorul {user.username} a primit downgrade la Standard."}


@app.get("/account-badges", tags=["0. Autentificare & Roluri"])
def get_account_badges(db: Session = Depends(get_db)):
    """Returneaza tipul de cont (Standard/Premium/Admin) asociat fiecarui SteamID pentru Dashboard."""
    users = db.query(models.User).filter(models.User.steam_id.isnot(None)).all()
    return {
        u.steam_id: {"user_id": u.id, "username": u.username, "role": u.role.name}
        for u in users
    }


@app.get("/auth/steam", tags=["0. Autentificare & Roluri"])
def auth_steam_redirect(request: Request):
    """Trimite utilizatorul pe pagina oficiala Steam OpenID pentru a-si dovedi identitatea."""
    base_url = str(request.base_url).rstrip("/")
    if "onrender.com" in base_url and base_url.startswith("http://"):
        base_url = base_url.replace("http://", "https://", 1)

    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": f"{base_url}/auth/steam/callback",
        "openid.realm": f"{base_url}/",
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }
    steam_url = "https://steamcommunity.com/openid/login?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=steam_url)


@app.get("/auth/steam/callback", tags=["0. Autentificare & Roluri"])
def auth_steam_callback(request: Request, db: Session = Depends(get_db)):
    """Verifica semnatura primita de la Steam, logheaza utilizatorul si importa automat statisticile CS2."""
    query_params = dict(request.query_params)
    if query_params.get("openid.mode") != "id_res":
        return RedirectResponse(url="/?steam_error=Autentificare+anulata")

    verify_params = dict(query_params)
    verify_params["openid.mode"] = "check_authentication"
    data = urllib.parse.urlencode(verify_params).encode("utf-8")

    try:
        req = urllib.request.Request("https://steamcommunity.com/openid/login", data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result_text = resp.read().decode("utf-8")
    except Exception:
        return RedirectResponse(url="/?steam_error=Eroare+comunicare+Steam")

    if "is_valid:true" not in result_text:
        return RedirectResponse(url="/?steam_error=Semnatura+Steam+invalida")

    claimed_id = query_params.get("openid.claimed_id", "")
    m = re.search(r"(\d{17})$", claimed_id)
    if not m:
        return RedirectResponse(url="/?steam_error=SteamID+invalid")
    steam_id = m.group(1)

    has_api_key = bool(STEAM_API_KEY and STEAM_API_KEY != "PUNE_CHEIA_TA_AICI_DOAR_LOCAL")

    # 1. Preluam Nickname-ul si Avatarul actual de pe Steam
    nickname = f"Steam_{steam_id[-6:]}"
    avatar_url = ""
    if has_api_key:
        try:
            s_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steam_id}"
            with urllib.request.urlopen(s_url, timeout=8) as resp:
                plist = json.loads(resp.read().decode()).get("response", {}).get("players", [])
                if plist:
                    nickname = plist[0].get("personaname", nickname)
                    avatar_url = plist[0].get("avatarfull", "")
        except Exception:
            pass

    # 2. Cautam sau cream contul de User (Standard)
    user = db.query(models.User).filter(models.User.steam_id == steam_id).first()
    if not user:
        standard_role = db.query(models.Role).filter(models.Role.name == "Standard").first()
        user = models.User(
            username=f"{nickname}_{steam_id[-4:]}",
            email=f"{steam_id}@steam.local",
            password_hash=hash_password(f"steam_openid_{steam_id}"),
            role_id=standard_role.id,
            steam_id=steam_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 3. Cautam sau cream profilul de Player
    player = db.query(models.Player).filter(models.Player.steam_id == steam_id).first()
    if not player:
        player = models.Player(steam_id=steam_id, nickname=nickname, avatar_url=avatar_url, is_manual=False)
        db.add(player)
        db.commit()
        db.refresh(player)
    elif avatar_url:
        player.avatar_url = avatar_url
        db.commit()

    # 4. Importam automat statisticile CS2 din Steam Web API
    if has_api_key:
        try:
            stats_url = f"https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v2/?appid=730&key={STEAM_API_KEY}&steamid={steam_id}"
            with urllib.request.urlopen(stats_url, timeout=8) as resp:
                stats_data = json.loads(resp.read().decode())
                raw_stats = {s["name"]: s["value"] for s in stats_data.get("playerstats", {}).get("stats", [])}

                total_kills = raw_stats.get("total_kills", 0)
                total_deaths = raw_stats.get("total_deaths", 1)
                total_hs = raw_stats.get("total_kills_headshot", 0)
                total_dmg = raw_stats.get("total_damage_done", 0)
                total_rounds = raw_stats.get("total_rounds_played", 1)

                hs_pct = round((total_hs / total_kills) * 100, 1) if total_kills > 0 else 0.0
                adr = round(total_dmg / total_rounds, 1) if total_rounds > 0 else 0.0

                match = db.query(models.Match).first()
                if match and total_kills > 0:
                    existing_stat = db.query(models.PlayerMatchStats).filter(
                        models.PlayerMatchStats.player_id == player.id
                    ).first()
                    if existing_stat:
                        existing_stat.kills = total_kills
                        existing_stat.deaths = total_deaths
                        existing_stat.adr = min(adr, 500.0)
                        existing_stat.headshot_percentage = min(hs_pct, 100.0)
                    else:
                        db.add(models.PlayerMatchStats(
                            player_id=player.id,
                            match_id=match.id,
                            kills=total_kills,
                            deaths=total_deaths,
                            assists=0,
                            adr=min(adr, 500.0),
                            headshot_percentage=min(hs_pct, 100.0)
                        ))
                    db.commit()
        except Exception:
            pass

    token = create_access_token(data={"sub": user.username, "role": user.role.name})
    redirect_params = urllib.parse.urlencode({
        "steam_token": token,
        "steam_user": user.username,
        "steam_role": user.role.name,
        "steam_id": steam_id
    })
    return RedirectResponse(url=f"/?{redirect_params}")