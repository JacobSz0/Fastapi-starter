from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

def create_connection():
  connection = sqlite3.connect("books.db")
  return connection

def create_table():
 connection = create_connection()
 cursor = connection.cursor()
 cursor.execute("""
 CREATE TABLE IF NOT EXISTS books (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL,
 author TEXT NOT NULL
 )
 """)
 connection.commit()
 connection.close()

create_table() # Call this function to create the table

class BookCreate(BaseModel):
  title: str
  author: str

class Book(BookCreate):
  id: int

def get_all_books():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    connection.close()
    return books

def create_book(book: BookCreate):
 connection = create_connection()
 cursor = connection.cursor()
 cursor.execute("INSERT INTO books (title, author) VALUES (?, ?)", (book.title, book.author))
 connection.commit()
 connection.close()
 book_id = cursor.lastrowid

 connection.close()
 return book_id

def get_book_by_id(book_id: int):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    connection.close()
    if book:
        return book
    else:
        raise HTTPException(status_code=404, detail="Book not found")

# Function to update a book by its ID
def update_book(book_id: int, book: BookCreate):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE books SET title = ?, author = ? WHERE id = ?", (book.title, book.author, book_id))
    connection.commit()
    connection.close()

# Function to delete a book by its ID
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
 return {"id": book_id, **book.model_dump()}

# Endpoint to get a single book by its ID
@app.get("/books/{book_id}")
def get_book(book_id: int):
    book = get_book_by_id(book_id)
    return {"book": book}

# Endpoint to update a book by its ID
@app.put("/books/{book_id}")
def update_book_endpoint(book_id: int, book: BookCreate):
    get_book_by_id(book_id)  # Check if the book exists, raises 404 if not found
    update_book(book_id, book)
    return {"book": book, "id":book_id}

# Endpoint to delete a book by its ID
@app.delete("/books/{book_id}")
def delete_book_endpoint(book_id: int):
    get_book_by_id(book_id)  # Check if the book exists, raises 404 if not found
    delete_book(book_id)
    return {"message": "Book deleted successfully"}
