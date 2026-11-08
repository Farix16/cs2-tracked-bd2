from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

#1.Roles
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class RoleResponse(RoleBase):
    id: int
    class Config:
        from_attributes = True


#2.users
class UserBase(BaseModel):
    username: str
    email: str
    role_id: int

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True


#3.players
class PlayerBase(BaseModel):
    steam_id: str
    nickname: str
    avatar_url: Optional[str] = None

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(BaseModel):
    steam_id: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

class PlayerResponse(PlayerBase):
    id: int
    class Config:
        from_attributes = True


#4.mape
class MapBase(BaseModel):
    name: str
    is_active_duty: int = 1

class MapCreate(MapBase):
    pass

class MapUpdate(BaseModel):
    name: Optional[str] = None
    is_active_duty: Optional[int] = None

class MapResponse(MapBase):
    id: int
    class Config:
        from_attributes = True


#5.matches
class MatchBase(BaseModel):
    map_id: int
    team_ct_score: int = Field(ge=0)
    team_t_score: int = Field(ge=0)

class MatchCreate(MatchBase):
    pass

class MatchUpdate(BaseModel):
    map_id: Optional[int] = None
    team_ct_score: Optional[int] = Field(default=None, ge=0)
    team_t_score: Optional[int] = Field(default=None, ge=0)

class MatchResponse(MatchBase):
    id: int
    played_at: datetime
    class Config:
        from_attributes = True


#6.player match stats
class PlayerMatchStatsBase(BaseModel):
    player_id: int
    match_id: int
    kills: int = Field(default=0, ge=0)
    deaths: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    adr: float = Field(default=0.0, ge=0.0)
    headshot_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

class PlayerMatchStatsCreate(PlayerMatchStatsBase):
    pass

class PlayerMatchStatsUpdate(BaseModel):
    kills: Optional[int] = Field(default=None, ge=0)
    deaths: Optional[int] = Field(default=None, ge=0)
    assists: Optional[int] = Field(default=None, ge=0)
    adr: Optional[float] = Field(default=None, ge=0.0)
    headshot_percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0)

class PlayerMatchStatsResponse(PlayerMatchStatsBase):
    id: int
    class Config:
        from_attributes = True