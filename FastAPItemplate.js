var dbName="movies"
var dbNameCaps="Movies"
var fields=["lengthy_description", "image_1", "image_2", "date_watched"]
var data=`from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import json

def create_connection():
    connection = sqlite3.connect("`+dbName+`.db")
    return connection

def create_table():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `+dbName+`s (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        `+dbName+`_data TEXT NOT NULL
    )
    """)
    connection.commit()
    connection.close()

create_table()  # Call this function to create the table

class `+dbNameCaps+`Create(BaseModel):\n`
	for (var i of fields){
    	data+=`    `+i+`: str`+`\n`
    }


data+=`\nclass `+dbNameCaps+`(`+dbNameCaps+`Create):
    id: int

def get_all_`+dbName+`s():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, `+dbName+`_data FROM `+dbName+`s")
    `+dbName+`s = cursor.fetchall()
    connection.close()

    `+dbName+`s_list = []
    for `+dbName+` in `+dbName+`s:
        `+dbName+`_dict = {"id": `+dbName+`[0], **json.loads(`+dbName+`[1])}
        `+dbName+`s_list.append(`+dbName+`_dict)

    return `+dbName+`s_list

def create_`+dbName+`(`+dbName+`: `+dbNameCaps+`Create):
    connection = create_connection()
    cursor = connection.cursor()
    `+dbName+`_data = json.dumps({`
	for (var i of fields){
      data+=`"`+i+`": `+dbName+`.`+i+`, `
    }
data+=`})
    cursor.execute("INSERT INTO `+dbName+`s (`+dbName+`_data) VALUES (?)", (`+dbName+`_data,))
    connection.commit()
    `+dbName+`_id = cursor.lastrowid
    connection.close()
    return `+dbName+`_id

def get_`+dbName+`_by_id(`+dbName+`_id: int):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT `+dbName+`_data FROM `+dbName+`s WHERE id = ?", (`+dbName+`_id,))
    `+dbName+` = cursor.fetchone()
    connection.close()
    if `+dbName+`:
        return json.loads(`+dbName+`[0])
    else:
        raise HTTPException(status_code=404, detail="`+dbNameCaps+` not found")

def update_`+dbName+`(`+dbName+`_id: int, `+dbName+`: `+dbNameCaps+`Create):
    connection = create_connection()
    cursor = connection.cursor()
    `+dbName+`_data = json.dumps({`
	for (var i of fields){
      data+=`"`+i+`": `+dbName+`.`+i+`, `
    }
data+=`})
    cursor.execute("UPDATE `+dbName+`s SET `+dbName+`_data = ? WHERE id = ?", (`+dbName+`_data, `+dbName+`_id))
    connection.commit()
    connection.close()

def delete_`+dbName+`(`+dbName+`_id: int):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM `+dbName+`s WHERE id = ?", (`+dbName+`_id,))
    connection.commit()
    connection.close()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the CRUD API"}

@app.get("/`+dbName+`s/")
def get_all_`+dbName+`s_endpoint():
    all_`+dbName+`s = get_all_`+dbName+`s()
    return {"`+dbName+`s": all_`+dbName+`s}

@app.post("/`+dbName+`s/")
def create_`+dbName+`_endpoint(`+dbName+`: `+dbNameCaps+`Create):
    `+dbName+`_id = create_`+dbName+`(`+dbName+`)
    return {"id": `+dbName+`_id, `
	for (var i of fields){
      data+=`"`+i+`": `+dbName+`.`+i+`, `
    }
//"title": book.title, "author": book.author
data+=`}

@app.get("/`+dbName+`s/{`+dbName+`_id}")
def get_`+dbName+`(`+dbName+`_id: int):
    `+dbName+` = get_`+dbName+`_by_id(`+dbName+`_id)
    return {"`+dbName+`": `+dbName+`}

@app.put("/`+dbName+`s/{`+dbName+`_id}")
def update_`+dbName+`_endpoint(`+dbName+`_id: int, `+dbName+`: `+dbNameCaps+`Create):
    get_`+dbName+`_by_id(`+dbName+`_id)
    update_`+dbName+`(`+dbName+`_id, `+dbName+`)
    return {"message": "`+dbNameCaps+` updated successfully", "id": `+dbName+`_id, "content": `+dbName+`}

@app.delete("/`+dbName+`s/{`+dbName+`_id}")
def delete_`+dbName+`_endpoint(`+dbName+`_id: int):
    get_`+dbName+`_by_id(`+dbName+`_id)
    delete_`+dbName+`(`+dbName+`_id)
    return {"message": "`+dbNameCaps+` deleted successfully"}
`
console.log(data)
