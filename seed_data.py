from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Tradition, Saint, Icon

# SQLite connection
DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
db = SessionLocal()

# Clear existing data (optional)
db.query(Icon).delete()
db.query(Saint).delete()
db.query(Tradition).delete()
db.commit()

# Add some traditions
byzantine = Tradition(name="Byzantine")
russian = Tradition(name="Russian")
coptic = Tradition(name="Coptic")

db.add_all([byzantine, russian, coptic])
db.commit()

# Add some saints
st_basil = Saint(name="St. Basil the Great", feast_day="January 1")
st_george = Saint(name="St. George", feast_day="April 23")
st_mary = Saint(name="Theotokos (Virgin Mary)", feast_day="August 15")

db.add_all([st_basil, st_george, st_mary])
db.commit()

# Add some icons
icon1 = Icon(
    title="St. Basil Icon",
    image_url="/static/images/st_basil.jpg",
    century="10th Century",
    region="Byzantium",
    iconographer="Unknown",
    tradition_id=byzantine.id,
    description="Traditional Byzantine icon of St. Basil the Great."
)

icon2 = Icon(
    title="St. George Slaying the Dragon",
    image_url="/static/images/st_george.jpg",
    century="15th Century",
    region="Russia",
    iconographer="Unknown",
    tradition_id=russian.id,
    description="Russian Orthodox icon of St. George defeating the dragon."
)

icon3 = Icon(
    title="Theotokos Hodegetria",
    image_url="/static/images/theotokos.jpg",
    century="12th Century",
    region="Egypt",
    iconographer="Unknown",
    tradition_id=coptic.id,
    description="Coptic icon of the Virgin Mary pointing to Christ."
)

db.add_all([icon1, icon2, icon3])
db.commit()

# Link icons to saints
icon1.saints.append(st_basil)
icon2.saints.append(st_george)
icon3.saints.append(st_mary)

db.commit()
print("Sample data added successfully!")

