from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os

# Настройки
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bot.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="МеханоБот API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели БД
class Person(Base):
    __tablename__ = "person"
    
    user_id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    photo = Column(String(255), default="default.jpg")
    experience = Column(Integer, default=0)
    money = Column(Integer, default=100)
    hp = Column(Integer, default=100)
    damage = Column(Integer, default=20)
    luck = Column(Integer, default=20)
    level = Column(Integer, default=1)

class Achievement(Base):
    __tablename__ = "achievement"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    image = Column(String(255), default="default_achievement.jpg")
    condition = Column(String(255), nullable=True)
    awarded_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "event"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    datetime = Column(DateTime, nullable=False)
    chat_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    item_id = Column(Integer, nullable=False)
    item_name = Column(String(100), nullable=False)
    item_type = Column(String(50), nullable=False)
    quantity = Column(Integer, default=1)
    purchased_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'chat_id', 'item_id', name='uq_user_item'),
    )

class ActiveEffectDB(Base):
    __tablename__ = "active_effects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    effect_type = Column(String(50), nullable=False)
    value = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Integer, nullable=False)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Pydantic Схемы
class PersonCreate(BaseModel):
    user_id: int
    chat_id: int
    name: str
    photo: str = "default.jpg"
    level: int = 1

class PersonUpdate(BaseModel):
    name: Optional[str] = None
    photo: Optional[str] = None
    experience: Optional[int] = None
    money: Optional[int] = None
    hp: Optional[int] = None
    damage: Optional[int] = None
    luck: Optional[int] = None
    level: Optional[int] = None

class PersonResponse(BaseModel):
    userId: int
    chatId: int
    name: str
    photo: str
    experience: int
    money: int
    hp: int
    damage: int
    luck: int
    level: int = 1
    
    class Config:
        from_attributes = True

class AchievementCreate(BaseModel):
    user_id: int
    chat_id: int
    name: str
    description: str
    image: str = "default_achievement.jpg"
    condition: Optional[str] = None

class AchievementResponse(BaseModel):
    id: int
    name: str
    photo: str
    condition: Optional[str] = None
    description: str
    
    class Config:
        from_attributes = True

class EventCreate(BaseModel):
    name: str
    datetime: str
    chat_id: int
    user_id: int
    description: Optional[str] = None

class EventResponse(BaseModel):
    id: int
    name: str
    startedAt: str
    chatId: int
    userId: int
    
    class Config:
        from_attributes = True

class ItemResponse(BaseModel):
    id: int
    name: str
    price: int
    description: str
    type: str
    
    class Config:
        from_attributes = True

class InventoryAddRequest(BaseModel):
    user_id: int
    chat_id: int
    item_id: int
    item_name: str
    item_type: str
    quantity: int = 1

class InventoryItemResponse(BaseModel):
    id: int
    item_id: int
    name: str
    type: str
    quantity: int
    
    class Config:
        from_attributes = True

class EffectResponse(BaseModel):
    effect_type: str
    value: int
    remaining_seconds: int
    
    class Config:
        from_attributes = True

class UseItemRequest(BaseModel):
    user_id: int
    chat_id: int
    item_id: int

# Вспомогательные функции
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_person(db: Session, chat_id: int, user_id: int):
    return db.query(Person).filter(
        Person.chat_id == chat_id,
        Person.user_id == user_id
    ).first()

# API Эндпоинты

# Person
@app.get("/api/person/id/{chat_id}", response_model=List[PersonResponse])
def get_players_by_chat(chat_id: int, db: Session = Depends(get_db)):
    players = db.query(Person).filter(Person.chat_id == chat_id).all()
    return [
        PersonResponse(
            userId=p.user_id,
            chatId=p.chat_id,
            name=p.name,
            photo=p.photo,
            experience=p.experience,
            money=p.money,
            hp=p.hp,
            damage=p.damage,
            luck=p.luck,
            level=p.level
        )
        for p in players
    ]

@app.post("/api/person/create_alt", status_code=201)
def create_player_alt(data: dict, db: Session = Depends(get_db)):
    try:
        user_id = data.get('user_id')
        chat_id = data.get('chat_id')
        name = data.get('name')
        photo = data.get('photo', 'default.jpg')
        level = data.get('level', 1)
        
        if not all([user_id, chat_id, name]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        existing = get_person(db, chat_id, user_id)
        if existing:
            raise HTTPException(status_code=400, detail="Игрок уже существует")
        
        db_player = Person(
            user_id=user_id,
            chat_id=chat_id,
            name=name,
            photo=photo,
            experience=0,
            money=100,
            hp=100,
            damage=20,
            luck=20,
            level=level
        )
        db.add(db_player)
        db.commit()
        db.refresh(db_player)
        return {"message": "Игрок создан"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/person/create", status_code=201)
def create_player(person: PersonCreate, db: Session = Depends(get_db)):
    existing = get_person(db, person.chat_id, person.user_id)
    if existing:
        raise HTTPException(status_code=400, detail="Игрок уже существует")
    
    db_player = Person(
        user_id=person.user_id,
        chat_id=person.chat_id,
        name=person.name,
        photo=person.photo,
        experience=0,
        money=100,
        hp=100,
        damage=20,
        luck=20,
        level=person.level
    )
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return {"message": "Игрок создан"}

@app.put("/api/person/update")
def update_player(
        chat_id: int,
        user_id: int,
        data: PersonUpdate,
        db: Session = Depends(get_db)
):
    player = get_person(db, chat_id, user_id)
    if not player:
        raise HTTPException(status_code=404, detail="Игрок не найден")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(player, key, value)

    db.commit()
    return {"message": "Игрок обновлён"}

@app.get("/api/person/all", response_model=List[PersonResponse])
def get_all_players(db: Session = Depends(get_db)):
    players = db.query(Person).all()
    return [
        PersonResponse(
            userId=p.user_id,
            chatId=p.chat_id,
            name=p.name,
            photo=p.photo,
            experience=p.experience,
            money=p.money,
            hp=p.hp,
            damage=p.damage,
            luck=p.luck,
            level=p.level
        )
        for p in players
    ]

@app.put("/api/person/update_level")
def update_player_level(
    chat_id: int,
    user_id: int,
    level: int,
    db: Session = Depends(get_db)
):
    player = get_person(db, chat_id, user_id)
    if not player:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    
    player.level = level
    db.commit()
    return {"message": "Уровень обновлён", "level": level}

@app.get("/api/person/level/{chat_id}/{user_id}")
def get_player_level(
    chat_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    player = get_person(db, chat_id, user_id)
    if not player:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    
    return {"level": player.level, "experience": player.experience}

# Achievement
@app.get("/api/achievement/person/{chat_id}/{user_id}", response_model=List[AchievementResponse])
def get_user_achievements(chat_id: int, user_id: int, db: Session = Depends(get_db)):
    achievements = db.query(Achievement).filter(
        Achievement.chat_id == chat_id,
        Achievement.user_id == user_id
    ).all()
    return [
        AchievementResponse(
            id=a.id,
            name=a.name,
            photo=a.image,
            condition=a.condition,
            description=a.description
        )
        for a in achievements
    ]

@app.post("/api/achievement/create", status_code=201)
def create_achievement(achievement: AchievementCreate, db: Session = Depends(get_db)):
    db_achievement = Achievement(
        user_id=achievement.user_id,
        chat_id=achievement.chat_id,
        name=achievement.name,
        description=achievement.description,
        image=achievement.image,
        condition=achievement.condition
    )
    db.add(db_achievement)
    db.commit()
    return {"message": "Достижение выдано"}

@app.delete("/api/achievement/delete/{achievement_id}", status_code=204)
def delete_achievement(achievement_id: int, db: Session = Depends(get_db)):
    achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()
    if achievement:
        db.delete(achievement)
        db.commit()
    return None

# Event
@app.get("/api/event/chat/{chat_id}", response_model=List[EventResponse])
def get_events(chat_id: int, db: Session = Depends(get_db)):
    events = db.query(Event).filter(Event.chat_id == chat_id).all()
    return [
        EventResponse(
            id=e.id,
            name=e.name,
            startedAt=e.datetime.strftime("%d.%m.%Y %H:%M"),
            chatId=e.chat_id,
            userId=e.user_id
        )
        for e in events
    ]

@app.post("/api/event/create", status_code=201)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    try:
        try:
            event_datetime = datetime.strptime(event.datetime, "%d.%m.%Y %H:%M")
        except ValueError:
            event_datetime = datetime.strptime(event.datetime, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты")
    
    db_event = Event(
        name=event.name,
        datetime=event_datetime,
        chat_id=event.chat_id,
        user_id=event.user_id,
        description=event.description
    )
    db.add(db_event)
    db.commit()
    return {"message": "Мероприятие создано"}

@app.delete("/api/event/delete/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event:
        db.delete(event)
        db.commit()
    return None

# Items (для магазина)
@app.get("/api/item/all", response_model=List[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return [
        ItemResponse(id=1, name="Зелье здоровья", price=50, description="Восстанавливает 20 HP", type="shop"),
        ItemResponse(id=2, name="Зелье силы", price=80, description="Увеличивает урон на 5", type="shop"),
        ItemResponse(id=3, name="Амулет удачи", price=100, description="Увеличивает удачу", type="shop"),
        ItemResponse(id=4, name="Броня", price=150, description="Увеличивает HP на 20", type="shop"),
    ]

@app.get("/api/inventory/{chat_id}/{user_id}", response_model=List[InventoryItemResponse])
def get_inventory(chat_id: int, user_id: int, db: Session = Depends(get_db)):
    items = db.query(Inventory).filter(
        Inventory.chat_id == chat_id,
        Inventory.user_id == user_id
    ).all()
    
    return [
        InventoryItemResponse(
            id=inv.id,
            item_id=inv.item_id,
            name=inv.item_name,
            type=inv.item_type,
            quantity=inv.quantity
        )
        for inv in items
    ]

@app.post("/api/inventory/add")
def add_to_inventory(request: InventoryAddRequest, db: Session = Depends(get_db)):
    existing = db.query(Inventory).filter(
        Inventory.user_id == request.user_id,
        Inventory.chat_id == request.chat_id,
        Inventory.item_id == request.item_id
    ).first()
    
    if existing:
        existing.quantity += request.quantity
    else:
        new_item = Inventory(
            user_id=request.user_id,
            chat_id=request.chat_id,
            item_id=request.item_id,
            item_name=request.item_name,
            item_type=request.item_type,
            quantity=request.quantity
        )
        db.add(new_item)
    
    db.commit()
    return {"message": "Предмет добавлен в инвентарь"}

#Инвентарь
@app.delete("/api/inventory/remove/{inventory_id}")
def remove_inventory_item(inventory_id: int, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    db.delete(item)
    db.commit()
    return {"message": "Предмет удален"}

@app.put("/api/inventory/update")
def update_inventory_quantity(data: dict, db: Session = Depends(get_db)):
    inventory_id = data.get('inventory_id')
    quantity = data.get('quantity')
    
    item = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    
    item.quantity = quantity
    db.commit()
    return {"message": "Количество обновлено"}

#Зелья
@app.get("/api/effects/{chat_id}/{user_id}", response_model=List[EffectResponse])
def get_active_effects(chat_id: int, user_id: int, db: Session = Depends(get_db)):
    effects = db.query(ActiveEffectDB).filter(
        ActiveEffectDB.chat_id == chat_id,
        ActiveEffectDB.user_id == user_id
    ).all()
    
    now = datetime.utcnow()
    result = []
    for e in effects:
        elapsed = (now - e.started_at).total_seconds()
        remaining = max(0, e.duration_seconds - elapsed)
        if remaining > 0:
            result.append(EffectResponse(
                effect_type=e.effect_type,
                value=e.value,
                remaining_seconds=int(remaining)
            ))
    
    return result

@app.post("/api/effects/apply")
def apply_effect(
    chat_id: int,
    user_id: int,
    effect_type: str,
    value: int,
    duration_seconds: int,
    db: Session = Depends(get_db)
):
    effect = ActiveEffectDB(
        user_id=user_id,
        chat_id=chat_id,
        effect_type=effect_type,
        value=value,
        duration_seconds=duration_seconds
    )
    db.add(effect)
    db.commit()
    return {"message": "Эффект применен"}

@app.delete("/api/effects/clear/{chat_id}/{user_id}")
def clear_expired_effects(chat_id: int, user_id: int, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    effects = db.query(ActiveEffectDB).filter(
        ActiveEffectDB.chat_id == chat_id,
        ActiveEffectDB.user_id == user_id
    ).all()
    
    expired = []
    for e in effects:
        elapsed = (now - e.started_at).total_seconds()
        if elapsed >= e.duration_seconds:
            expired.append(e)
    
    for e in expired:
        db.delete(e)
    
    db.commit()
    return {"cleared": len(expired)}

# Здоровье
@app.get("/")
def root():
    return {"message": "МеханоБот API работает!"}

@app.get("/health")
def health():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)