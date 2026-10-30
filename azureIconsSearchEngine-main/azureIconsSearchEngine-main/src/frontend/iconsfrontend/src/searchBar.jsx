import "./searchBar.css";
import { useState } from "react";
import axios from "axios";
import ImageComponent from "./imageComponent";
import { useContext } from "react";
import UserContext from "./context/userContext";

export default function SearchBar(){

    const [search, setSearch] = useState("");
    

    const {images} = useContext(UserContext);
    
    const {setImages} = useContext(UserContext);
    const handleSearch = (e) => {
        setSearch(e.target.value);
        console.log(search);
    }

    const searchDatabase = () => {
        alert(`searching for '${search}'`);
        axios.post("http://localhost:5000/dbquery", {
            user_query: `${search}`

    })
        .then((res) => {
            
            setImages(res.data);
            console.log(images);
        })
        .catch((err) => {
            console.log(err);
        })
    }

  
          return(
            <div className="searchdiv">
             <input type="text" placeholder="Search eg: 'Azure Ai Search', 'Azure Cosmos DB' " className="searchbar" onChange={handleSearch} />
             <button className="searchbutton" onClick={searchDatabase}>Search</button>
            
             
            </div>
        )
    
    
    
    

}