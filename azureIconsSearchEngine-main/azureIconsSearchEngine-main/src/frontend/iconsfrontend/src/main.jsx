import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import SearchBar from './searchBar.jsx'
import "./index.css";
import { useState } from "react";
import axios from "axios";
import { createContext } from 'react';
import {UserContextProvider} from './context/userContextProvider.jsx'
import ImageComponent from './imageComponent.jsx';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Heading from './heading.jsx';
import AboutMe from './aboutMe.jsx';
import CourseCarousel from './courseCarousel.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
  <UserContextProvider>
  <Heading/>
    <SearchBar/>
    <ImageComponent />
    <AboutMe/>
    <CourseCarousel/>
    </UserContextProvider>
  </StrictMode>
)
