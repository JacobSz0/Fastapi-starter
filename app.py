from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import json

def create_connection():
    connection = sqlite3.connect("books.db")
    return connection

def create_table():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_data TEXT NOT NULL
    )
    """)
    connection.commit()
    connection.close()

create_table()  # Call this function to create the table

class BookCreate(BaseModel):
    title: str
    author: str

class Book(BookCreate):
    id: int

def get_all_books():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, book_data FROM books")
    books = cursor.fetchall()
    connection.close()

    books_list = []
    for book in books:
        book_dict = {"id": book[0], **json.loads(book[1])}
        books_list.append(book_dict)

    return books_list

def create_book(book: BookCreate):
    connection = create_connection()
    cursor = connection.cursor()
    book_data = json.dumps({"title": book.title, "author": book.author})
    cursor.execute("INSERT INTO books (book_data) VALUES (?)", (book_data,))
    connection.commit()
    book_id = cursor.lastrowid
    connection.close()
    return book_id

def get_book_by_id(book_id: int):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT book_data FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    connection.close()
    if book:
        return json.loads(book[0])
    else:
        raise HTTPException(status_code=404, detail="Book not found")

def update_book(book_id: int, book: BookCreate):
    connection = create_connection()
    cursor = connection.cursor()
    book_data = json.dumps({"title": book.title, "author": book.author})
    cursor.execute("UPDATE books SET book_data = ? WHERE id = ?", (book_data, book_id))
    connection.commit()
    connection.close()

def delete_book(book_id: int):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    connection.commit()
    connection.close()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the CRUD API"}

@app.get("/books/")
def get_all_books_endpoint():
    all_books = get_all_books()
    return {"books": all_books}

@app.post("/books/")
def create_book_endpoint(book: BookCreate):
    book_id = create_book(book)
    return {"id": book_id, "title": book.title, "author": book.author}

@app.get("/books/{book_id}")
def get_book(book_id: int):
    book = get_book_by_id(book_id)
    return {"book": book}

@app.put("/books/{book_id}")
def update_book_endpoint(book_id: int, book: BookCreate):
    get_book_by_id(book_id)
    update_book(book_id, book)
    return {"message": "Book updated successfully", "id": book_id, "content": book}

@app.delete("/books/{book_id}")
def delete_book_endpoint(book_id: int):
    get_book_by_id(book_id)
    delete_book(book_id)
    return {"message": "Book deleted successfully"}
