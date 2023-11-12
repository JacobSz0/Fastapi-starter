import './App.css';
import React, {useEffect, useState} from "react";
import Template from "./template";

function App() {

  const [DBName, setDBName] = useState("");
  const [Accounts, setAccounts] = useState(false);
  const [Tables, setTables] = useState([{"name":"", "data":""}]);

  const handleDBNameChange = (event) => {
    const value = event.target.value;
    setDBName(value.toLowerCase());
  };

  const handleAccountsChange = () => {
    if (Accounts===true){
      setAccounts(false)
    }
    else{
      setAccounts(true);
    }
  };

  const handleTableNameChange = (event, index) => {
    const { value } = event.target;
    const updatedTables = [...Tables];
    updatedTables[index].name = value.toLowerCase();
    setTables(updatedTables);
  }

  const handleTableDataChange = (event, index) => {
    const { value } = event.target;
    const updatedTables = [...Tables];
    updatedTables[index].data = value.toLowerCase();
    setTables(updatedTables);
  }

  function plusy(){
    const newTable = [...Tables, { name: "", data: "" }];
    setTables(newTable)
    console.log(newTable)
  }

  const downloadPythonFile = () => {
    var pythonCode=Template(DBName, Tables)

    // Create a Blob containing the Python content
    const blob = new Blob([pythonCode], { type: 'text/plain' });

    // Create a URL for the Blob
    const url = window.URL.createObjectURL(blob);

    // Create a download link
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'app.py');
    document.body.appendChild(link);

    // Simulate a click to trigger the download
    link.click();

    // Clean up: remove the link and URL
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  useEffect(() => {}, [Tables]);

  return (
    <div className="App">
      DB Name
      <input onChange={handleDBNameChange}
        placeholder="database"
        required
        type="text"
        value={DBName}></input>
      <div>
        Accounts?
        <input type="checkbox" onChange={handleAccountsChange}></input>
        <hr></hr>
      </div>
      <div>
        Tables
        <hr></hr>
          {Tables.map((data, index) => (
            <div key={index}>
              <span>Name</span>
              <input
                value={data["name"]}
                onChange={(e) => handleTableNameChange(e, index)}
                ></input>
              <p>Feilds {"(Like this: name,date,expiration...)"}</p>
              <textarea
                value={data["data"]}
                onChange={(e) => handleTableDataChange(e, index)}
                ></textarea>
              <hr></hr>
            </div>
          ))}
        <button onClick={plusy}>+</button>{"   "}
        <button onClick={downloadPythonFile}>Download Python File</button>
      </div>
    </div>
  );
}

export default App;
