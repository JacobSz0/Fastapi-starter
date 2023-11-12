from fastapi import FastAPI, HTTPException, Depends, Response, Request
from pydantic import BaseModel
import sqlite3, json, uuid, os
from fastapi.middleware.cors import CORSMiddleware
from jwtdown_fastapi.authentication import Token, Authenticator


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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
    """)
    connection.commit()
    connection.close()

create_table()  # Call this function to create the table


class AccountIn(BaseModel):
    username: str
    email: str
    password: str
    role_id: int


class AccountOut(BaseModel):
    id: int
    username: str
    email: str
    role_id: int

class AccountOutWithPassword(AccountOut):
    hashed_password: str


class RoleIn(BaseModel):
    role: str


class RoleOut(BaseModel):
    id: int
    role: str

class DuplicateAccountError(ValueError):
    pass


class BookCreate(BaseModel):
    title: str
    author: str

class Book(BookCreate):
    id: int

class AccountQueries:
    def create_acc(self, info: AccountIn, hashed_password: str) -> AccountOutWithPassword:
        try:
            connection = create_connection()
            cursor = connection.cursor()
            query = """
                    INSERT INTO accounts (username, email, hashed_password, role_id)
                    VALUES (?, ?, ?, ?)
                    """
            cursor.execute(query, (info.username, info.email, hashed_password, info.role_id))
            connection.commit()
            account_id = cursor.lastrowid

            # Retrieve the created account to return the complete account information
            account = self.get_one_account(info.username)

            connection.close()
            if account:
                return account
            else:
                # If the account is not found or there's an issue, handle it accordingly
                raise ValueError("Error occurred while retrieving the created account")

        except sqlite3.Error as e:
            # Log the error for troubleshooting purposes
            print(f"Error occurred while creating account: {e}")
            # Re-raise the original exception to maintain the stack trace
            raise
    def get_one_account(self, username: str) -> AccountOutWithPassword:
        try:
            connection = create_connection()
            cursor = connection.cursor()
            query = """
                    SELECT id, username, email, hashed_password, role_id
                    FROM accounts
                    WHERE username = ?
                    """
            cursor.execute(query, (username,))
            record = None
            row = cursor.fetchone()
            if row is not None:
                record = {}
                for i, column in enumerate(cursor.description):
                    record[column[0]] = row[i]
            return record
        except sqlite3.Error as e:
            # Log the error or handle the exception according to your application's strategy
            print(f"Error occurred while retrieving account: {e}")
            return None

    def get_all_accounts(self):
        try:
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute(
                        """
                    SELECT id, username, email, role_id
                    FROM accounts
                    """
                    )
            results = [
                AccountOut(
                    id=row[0],
                    username=row[1],
                    email=row[2],
                    role_id=row[3],
                )
                for row in cursor.fetchall()
            ]
            return results
        except sqlite3.Error as e:
            # Log the error or handle the exception according to your application's strategy
            print(f"Error occurred while retrieving all accounts: {e}")
            return None

    def delete_account(self, id: int) -> bool:
        try:
            connection = create_connection()
            cursor = connection.cursor()
            query = """
                    DELETE FROM accounts
                    WHERE id = ?
                    """
            cursor.execute(query, (id,))
            connection.commit()
            return True
        except Exception as e:
            # Handle exceptions or log the error
            print(e)
            return False

class RoleQueries:
    def create_role(self, role: RoleIn) -> RoleOut:
        try:
            connection = create_connection()
            cursor = connection.cursor()
            query = """
                    INSERT INTO roles (role)
                    VALUES (?)
                    """
            cursor.execute(query, (role.role,))
            connection.commit()

            # Retrieve the last inserted row id
            cursor.execute("SELECT last_insert_rowid()")
            id = cursor.fetchone()[0]

            return self.role_in_out(id, role)
        except Exception as e:
            # Handle exceptions or log the error
            print(e)
            return None


    def roles(self):
        try:
            connection = create_connection()
            cursor = connection.cursor()
            result = cursor.execute(
                        """
                        SELECT
                        id,
                        role
                        FROM roles
                        """
            )
            return [self.records_in_out(record) for record in result]
        except Exception:
            return {"message": "Could not get all roles"}

    def delete_role(self, id: int) -> bool:
        try:
            connection = create_connection()
            cursor = connection.cursor()
            query = """
                    DELETE FROM roles
                    WHERE id = ?
                    """
            cursor.execute(query, (id,))
            connection.commit()
            return True
        except Exception:
            return False

    def role_in_out(self, id: int, role: RoleIn):
        data = role.dict()
        return RoleOut(id=id, **data)

    def records_in_out(self, record):
        return RoleOut(
            id=record[0],
            role=record[1],
        )


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

class AccountToken(Token):
    account: AccountOut


class HttpError(BaseModel):
    detail: str


class AccountForm(BaseModel):
    username: str
    email: str
    password: str



class MyAuthenticator(Authenticator):
    async def get_account_data(
        self,
        username: str,
        accounts: AccountQueries,
    ):
        # Use your repo to get the account based on the
        # username (which could be an email)
        return accounts.get_one_account(username)

    def get_account_getter(
        self,
        accounts: AccountQueries = Depends(),
    ):
        # Return the accounts. That's it.
        return accounts

    def get_hashed_password(self, account: AccountOutWithPassword):
        # Return the encrypted password value from your
        # account object
        return account["hashed_password"]

    def get_account_data_for_cookie(self, account: AccountOut):
        # Return the username and the data for the cookie.
        # You must return TWO values from this method.
        return account["username"], AccountOut(**account)

default_signing_key = str(uuid.uuid4())

signing_key = os.environ.get("SIGNING_KEY", default_signing_key)
authenticator = MyAuthenticator(signing_key)



app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",  # Example: React development server
    "https://jacobsz0.github.io",  # The domain of your React app
]

# Add the CORS middleware with allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the CRUD API"}

@app.get("/protected")
async def get_protected(
    account_data: dict = Depends(authenticator.get_current_account_data),
):
    return True


@app.get("/accounts")
def accounts_list(
    repo: AccountQueries = Depends(),
):
    return repo.get_all_accounts()


@app.post("/accounts", response_model=AccountToken | HttpError)
async def create_account(
    info: AccountIn,
    request: Request,
    response: Response,
    accounts: AccountQueries = Depends(),
):
    hashed_password = authenticator.hash_password(info.password)
    try:
        account = accounts.create_acc(info, hashed_password)
    except DuplicateAccountError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create an account with those credentials",
        )
    form = AccountForm(
        username=info.username, email=info.email, password=info.password
    )
    token = await authenticator.login(response, request, form, accounts)
    return AccountToken(account=account, **token.dict())


@app.get("/token", response_model=AccountToken | None)
async def get_token(
    request: Request,
    account: AccountOut = Depends(authenticator.try_get_current_account_data),
) -> AccountToken | None:
    if account and authenticator.cookie_name in request.cookies:
        return {
            "access_token": request.cookies[authenticator.cookie_name],
            "type": "Bearer",
            "account": account,
        }


@app.delete("/accounts/{id}")
def delete_account(id: int, response: Response, repo: AccountQueries = Depends()):
    return repo.delete_account(id)

@app.post("/role")
def create_role(role: RoleIn, repo: RoleQueries = Depends()):
    return repo.create_role(role)

@app.get("/role")
def all_roles(repo: RoleQueries = Depends()):
    return repo.roles()

@app.delete("/role/{role_id}")
def delete_role(role_id: int, repo: RoleQueries = Depends()):
    return repo.delete_role(role_id)



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
