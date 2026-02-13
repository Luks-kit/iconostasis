from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Many-to-many relationship table between icons and saints
icon_saints = Table(
    "icon_saints",
    Base.metadata,
    Column("icon_id", Integer, ForeignKey("icons.id"), primary_key=True),
    Column("saint_id", Integer, ForeignKey("saints.id"), primary_key=True)
)

class Tradition(Base):
    __tablename__ = "traditions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

class Saint(Base):
    __tablename__ = "saints"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    feast_day = Column(String(50))

    icons = relationship("Icon", secondary=icon_saints, back_populates="saints")

class Icon(Base):
    __tablename__ = "icons"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    image_url = Column(Text, nullable=False)
    century = Column(String(50))
    region = Column(String(100))
    iconographer = Column(String(255))
    description = Column(Text)

    tradition_id = Column(Integer, ForeignKey("traditions.id"))
    tradition = relationship("Tradition")

    saints = relationship("Saint", secondary=icon_saints, back_populates="icons")
    
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=False)
    hashed_pw = Column(String(255), nullable=False)
    # Relationships
    icons = relationship("Icon", back_populates="creator")
    comments = relationship("Comment", back_populates="author")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"))
    icon_id = Column(Integer, ForeignKey("icons.id"))
    # Relationships
    author = relationship("User", back_populates="comments")

