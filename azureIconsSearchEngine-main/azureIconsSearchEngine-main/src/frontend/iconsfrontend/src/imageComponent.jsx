import "./imageComponent.css";
import { useContext } from "react";
import UserContext from "./context/userContext";


export default function ImageComponent(){
    const {images} = useContext(UserContext);
    const {setImages} = useContext(UserContext);
    console.log(images);
    console.log("hi");
    console.log(images.length);
    if(images.length === 0){
        return(
            <div className="imageDiv">
             <div className="websiteLogoDiv">
        <img src="https://azureiconskuljot.blob.core.windows.net/iconsofazure/svg_website_logo.png" alt="Azure Icon" className="websiteLogo"/>
        </div>
            </div>

        )
    }
    return(
        <div className = "imageDiv">
        {images.map((image) => (
            <div key={image.url} className="componentDiv">
                <img src={image.url} alt="icon" className="iconImage"/>
                <p className="similarityScore"> <b>Similarity Score:</b> {image.SimilarityScore}</p>
                <p className="imageName"><b>Image Name:</b>{image.name}</p>
                <p className="imageDescription"><b>Image description:</b> {image.description}</p>
                <label for = "downloadLink"><b>Download Link:</b></label>
                <a href={image.url} className="downloadLink"> {image.url}</a>
          
            </div>
        ))}
        


        </div>
    )


}