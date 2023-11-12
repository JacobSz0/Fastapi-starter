from fastapi import FastAPI, HTTPException, Depends, Response, Request
from pydantic import BaseModel
import sqlite3, json, uuid, os
from fastapi.middleware.cors import CORSMiddleware
from jwtdown_fastapi.authentication import Token, Authenticator


def create_connection():
    connection = sqlite3.connect("data.db")
    return connection

def create_table():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_data TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candy_data TEXT NOT NULL
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

class FoodCreate(BaseModel):
    name: str
    date: str
    expiration: str

class Food(FoodCreate):
    id: int
class CandyCreate(BaseModel):
    name: str
    date: str
    cost: str

class Candy(CandyCreate):
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

def get_all_foods():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, food_data FROM foods")
    foods = cursor.fetchall()
    connection.close()

    foods_list = []
    for food in foods:
        food_dict = {"id": food[0], **json.loads(food[1])}
        foods_list.append(food_dict)
    return foods_list

def create_food(food: FoodCreate):
    connection = create_connection()
    cursor = connection.cursor()
    food_data = json.dumps({"name": food.name, "date": food.date, "expiration": food.expiration})
    cursor.execute("INSERT INTO foods (food_data) VALUES (?)", (food_data,))
    connection.commit()
    food_id = cursor.lastrowid
    connection.close()
    return food_id

def get_food_by_id(food_id: int):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT food_data FROM foods WHERE id = ?", (food_id,))
    food = cursor.fetchone()
    connection.close()
    if food:
        return json.loads(food[0])
    else:
        raise HTTPException(status_code=404, detail="Food not found")

def update_food(food_id: int, food: FoodCreate):
    connection = create_connection()
    cursor = connection.cursor()
    food_data = json.dumps({"name": food.name, "date": food.date, "expiration": food.expiration})
    cursor.execute("UPDATE foods SET food_data = ? WHERE id = ?", (food_data, food_id))
    connection.commit()
    connection.close()

def delete_food(food_id: int):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM foods WHERE id = ?", (food_id,))
    connection.commit()
    connection.close()

def get_all_candys():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, candy_data FROM candys")
    candys = cursor.fetchall()
    connection.close()

    candys_list = []
    for candy in candys:
        candy_dict = {"id": candy[0], **json.loads(candy[1])}
        candys_list.append(candy_dict)
    return candys_list

def create_candy(candy: CandyCreate):
    connection = create_connection()
    cursor = connection.cursor()
    candy_data = json.dumps({"name": candy.name, "date": candy.date, "cost": candy.cost})
    cursor.execute("INSERT INTO candys (candy_data) VALUES (?)", (candy_data,))
    connection.commit()
    candy_id = cursor.lastrowid
    connection.close()
    return candy_id

def get_candy_by_id(candy_id: int):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT candy_data FROM candys WHERE id = ?", (candy_id,))
    candy = cursor.fetchone()
    connection.close()
    if candy:
        return json.loads(candy[0])
    else:
        raise HTTPException(status_code=404, detail="Candy not found")

def update_candy(candy_id: int, candy: CandyCreate):
    connection = create_connection()
    cursor = connection.cursor()
    candy_data = json.dumps({"name": candy.name, "date": candy.date, "cost": candy.cost})
    cursor.execute("UPDATE candys SET candy_data = ? WHERE id = ?", (candy_data, candy_id))
    connection.commit()
    connection.close()

def delete_candy(candy_id: int):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM candys WHERE id = ?", (candy_id,))
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


@app.get("/foods/")
def get_all_foods_endpoint():
    all_foods = get_all_foods()
    return {"foods": all_foods}

@app.post("/foods/")
def create_food_endpoint(food: FoodCreate):
    food_id = create_food(food)
    return {"id": food_id, "name": food.name, "date": food.date, "expiration": food.expiration}

@app.get("/foods/{food_id}")
def get_food(food_id: int):
    food = get_food_by_id(food_id)
    return {"food": food}

@app.put("/foods/{food_id}")
def update_food_endpoint(food_id: int, food: FoodCreate):
    get_food_by_id(food_id)
    update_food(food_id, food)
    return {"message": "Food updated successfully", "id": food_id, "content": food}

@app.delete("/foods/{food_id}")
def delete_food_endpoint(food_id: int):
    get_food_by_id(food_id)
    delete_food(food_id)
    return {"message": "Food deleted successfully"}
@app.get("/candys/")
def get_all_candys_endpoint():
    all_candys = get_all_candys()
    return {"candys": all_candys}

@app.post("/candys/")
def create_candy_endpoint(candy: CandyCreate):
    candy_id = create_candy(candy)
    return {"id": candy_id, "name": candy.name, "date": candy.date, "cost": candy.cost}

@app.get("/candys/{candy_id}")
def get_candy(candy_id: int):
    candy = get_candy_by_id(candy_id)
    return {"candy": candy}

@app.put("/candys/{candy_id}")
def update_candy_endpoint(candy_id: int, candy: CandyCreate):
    get_candy_by_id(candy_id)
    update_candy(candy_id, candy)
    return {"message": "Candy updated successfully", "id": candy_id, "content": candy}

@app.delete("/candys/{candy_id}")
def delete_candy_endpoint(candy_id: int):
    get_candy_by_id(candy_id)
    delete_candy(candy_id)
    return {"message": "Candy deleted successfully"}
