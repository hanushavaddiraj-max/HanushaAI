import React from "react";
import "./udemyCourseComponent.css";

export default function UdemyCourseComponent({imageUrl, courseTitle, courseLink}) {
    return(
        <div className="parentDiv">
            <img src={imageUrl} alt={courseTitle} className="courseImage"/>
            <h2 className="courseTitle">{courseTitle}</h2>
            <a href={courseLink} className="courseLink">Link to Course</a>
        </div>

    )
}
