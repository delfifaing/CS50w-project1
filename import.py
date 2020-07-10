
import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL"))
db     = scoped_session(sessionmaker(bind = engine))

db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR NOT NULL, password VARCHAR NOT NULL)")
db.execute("CREATE TABLE reviews (book_isbn VARCHAR REFERENCES books(isbn), rating INTEGER NOT NULL,review VARCHAR NOT NULL, user_username VARCHAR NOT NULL, user_id BIGINT REFERENCES users(id),title VARCHAR NOT NULL, author VARCHAR NOT NULL)")
db.execute("CREATE TABLE books (isbn VARCHAR PRIMARY KEY,title VARCHAR NOT NULL,author VARCHAR NOT NULL,year VARCHAR NOT NULL)")

file   = open("books.csv")
reader = csv.reader(file)
for isbn, title, author, year in reader:
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
        {"isbn": isbn,
         "title": title,
         "author": author,
         "year": year})
    print(f"Book {title} added to database.")
db.commit()
