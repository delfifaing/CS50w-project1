# CS50’s Web Programming with Python and JavaScript
## Project 1
### Overview
PAPYRIR is a book reveiw web application, generated using a flask framework. This project was part of Harvard's CS50’s Web Programming with Python and JavaScript. It allows users to create an account, login, review/rate any of the books saved in books.csv and view other user's review. Additionally, it uses the third party API by Goodreads, to pull ratings from their audience. Finally, any user will be able to query for book details programmatically via the website’s API. A PostgreSQL database was used, hosted by Heroku. As seen in import.py, 3 tables were generated: books, users and reviews. All the management and queries of the tables were done via raw SQL commands.

A demonstration video can be found in:  https://youtu.be/16zsY3Z4Uak

### Run locally
``` 
# Clone repo
$ git clone 
$ cd CS50w_project1

# Install dependencies
$ pip install -r requirements.txt

# Set environment variables
$ export FLASK_APP=application.py 
$ export FLASK_DEBUG=1
$ export DATABASE_URL = <Heroku Postgres database URI>

# Run
$ flask run
```
### Tech Stack
- Backend: Flask, Python
- Frontend: HTML, CSS, Bootstrap
- Database management: PostgreSQL
- Online web hosting service: Heroku
