from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    role = relationship("Role", back_populates="users")

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    steam_id = Column(String(20), unique=True, nullable=False)
    nickname = Column(String(100), nullable=False)
    avatar_url = Column(String(255))
    match_stats = relationship("PlayerMatchStats", back_populates="player", cascade="all, delete-orphan")

class Map(Base):
    __tablename__ = "maps"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    is_active_duty = Column(Integer, default=1)
    matches = relationship("Match", back_populates="game_map")

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    map_id = Column(Integer, ForeignKey("maps.id", ondelete="RESTRICT"), nullable=False)
    played_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    team_ct_score = Column(Integer, nullable=False)
    team_t_score = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint('team_ct_score >= 0', name='check_ct_score_positive'),
        CheckConstraint('team_t_score >= 0', name='check_t_score_positive'),
    )
    game_map = relationship("Map", back_populates="matches")
    player_stats = relationship("PlayerMatchStats", back_populates="match", cascade="all, delete-orphan")

class PlayerMatchStats(Base):
    __tablename__ = "player_match_stats"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    kills = Column(Integer, nullable=False, default=0)
    deaths = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)
    adr = Column(Float, nullable=False, default=0.0)
    headshot_percentage = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        CheckConstraint('kills >= 0', name='check_kills_positive'),
        CheckConstraint('deaths >= 0', name='check_deaths_positive'),
        CheckConstraint('adr >= 0.0', name='check_adr_positive'),
        CheckConstraint('headshot_percentage >= 0.0 AND headshot_percentage <= 100.0', name='check_hs_valid'),
    )
    player = relationship("Player", back_populates="match_stats")
    match = relationship("Match", back_populates="player_stats")