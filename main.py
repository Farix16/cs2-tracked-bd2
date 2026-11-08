from contextlib import asynccontextmanager
from typing import List
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
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
    return {"status": "Online", "message": "Baza de date, Fixtures si Operatiile CRUD sunt active!"}


# =====================================================================
# 1. CRUD PENTRU ROLES
# =====================================================================
@app.post("/roles", response_model=schemas.RoleResponse, tags=["1. Roles CRUD"])
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db)):
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
def update_role(role_id: int, role_data: schemas.RoleUpdate, db: Session = Depends(get_db)):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rolul nu a fost gasit")
    for key, value in role_data.model_dump(exclude_unset=True).items():
        setattr(role, key, value)
    db.commit()
    db.refresh(role)
    return role

@app.delete("/roles/{role_id}", tags=["1. Roles CRUD"])
def delete_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rolul nu a fost gasit")
    db.delete(role)
    db.commit()
    return {"message": f"Rolul cu ID {role_id} a fost sters"}


# =====================================================================
# 2. CRUD PENTRU USERS
# =====================================================================
@app.post("/users", response_model=schemas.UserResponse, tags=["2. Users CRUD"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=f"hashed_{user.password}",
        role_id=user.role_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users", response_model=List[schemas.UserResponse], tags=["2. Users CRUD"])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.get("/users/{user_id}", response_model=schemas.UserResponse, tags=["2. Users CRUD"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost gasit")
    return user

@app.put("/users/{user_id}", response_model=schemas.UserResponse, tags=["2. Users CRUD"])
def update_user(user_id: int, user_data: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost gasit")
    update_dict = user_data.model_dump(exclude_unset=True)
    if "password" in update_dict:
        update_dict["password_hash"] = f"hashed_{update_dict.pop('password')}"
    for key, value in update_dict.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{user_id}", tags=["2. Users CRUD"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost gasit")
    db.delete(user)
    db.commit()
    return {"message": f"Utilizatorul cu ID {user_id} a fost sters"}


# =====================================================================
# 3. CRUD PENTRU PLAYERS
# =====================================================================
@app.post("/players", response_model=schemas.PlayerResponse, tags=["3. Players CRUD"])
def create_player(player: schemas.PlayerCreate, db: Session = Depends(get_db)):
    db_player = models.Player(**player.model_dump())
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
def update_player(player_id: int, player_data: schemas.PlayerUpdate, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jucatorul nu a fost gasit")
    for key, value in player_data.model_dump(exclude_unset=True).items():
        setattr(player, key, value)
    db.commit()
    db.refresh(player)
    return player

@app.delete("/players/{player_id}", tags=["3. Players CRUD"])
def delete_player(player_id: int, db: Session = Depends(get_db)):
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jucatorul nu a fost gasit")
    db.delete(player)
    db.commit()
    return {"message": f"Jucatorul cu ID {player_id} a fost sters"}


# =====================================================================
# 4. CRUD PENTRU MAPS
# =====================================================================
@app.post("/maps", response_model=schemas.MapResponse, tags=["4. Maps CRUD"])
def create_map(game_map: schemas.MapCreate, db: Session = Depends(get_db)):
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
def update_map(map_id: int, map_data: schemas.MapUpdate, db: Session = Depends(get_db)):
    game_map = db.query(models.Map).filter(models.Map.id == map_id).first()
    if not game_map:
        raise HTTPException(status_code=404, detail="Harta nu a fost gasita")
    for key, value in map_data.model_dump(exclude_unset=True).items():
        setattr(game_map, key, value)
    db.commit()
    db.refresh(game_map)
    return game_map

@app.delete("/maps/{map_id}", tags=["4. Maps CRUD"])
def delete_map(map_id: int, db: Session = Depends(get_db)):
    game_map = db.query(models.Map).filter(models.Map.id == map_id).first()
    if not game_map:
        raise HTTPException(status_code=404, detail="Harta nu a fost gasita")
    db.delete(game_map)
    db.commit()
    return {"message": f"Harta cu ID {map_id} a fost stearsa"}


# =====================================================================
# 5. CRUD PENTRU MATCHES
# =====================================================================
@app.post("/matches", response_model=schemas.MatchResponse, tags=["5. Matches CRUD"])
def create_match(match: schemas.MatchCreate, db: Session = Depends(get_db)):
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
def update_match(match_id: int, match_data: schemas.MatchUpdate, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Meciul nu a fost gasit")
    for key, value in match_data.model_dump(exclude_unset=True).items():
        setattr(match, key, value)
    db.commit()
    db.refresh(match)
    return match

@app.delete("/matches/{match_id}", tags=["5. Matches CRUD"])
def delete_match(match_id: int, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Meciul nu a fost gasit")
    db.delete(match)
    db.commit()
    return {"message": f"Meciul cu ID {match_id} a fost sters"}


# =====================================================================
# 6. CRUD PENTRU PLAYER_MATCH_STATS
# =====================================================================
@app.post("/stats", response_model=schemas.PlayerMatchStatsResponse, tags=["6. Player Match Stats CRUD"])
def create_stats(stats: schemas.PlayerMatchStatsCreate, db: Session = Depends(get_db)):
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
def update_stat(stat_id: int, stat_data: schemas.PlayerMatchStatsUpdate, db: Session = Depends(get_db)):
    stat = db.query(models.PlayerMatchStats).filter(models.PlayerMatchStats.id == stat_id).first()
    if not stat:
        raise HTTPException(status_code=404, detail="Statistica nu a fost gasita")
    for key, value in stat_data.model_dump(exclude_unset=True).items():
        setattr(stat, key, value)
    db.commit()
    db.refresh(stat)
    return stat

@app.delete("/stats/{stat_id}", tags=["6. Player Match Stats CRUD"])
def delete_stat(stat_id: int, db: Session = Depends(get_db)):
    stat = db.query(models.PlayerMatchStats).filter(models.PlayerMatchStats.id == stat_id).first()
    if not stat:
        raise HTTPException(status_code=404, detail="Statistica nu a fost gasita")
    db.delete(stat)
    db.commit()
    return {"message": f"Statistica cu ID {stat_id} a fost stearsa"}