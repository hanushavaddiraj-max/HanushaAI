import React from "react";

import UserContext from "./userContext";

const UserContextProvider = ({children}) => {
    const [images, setImages] = React.useState([]);
    return (
    <UserContext.Provider value={{images, setImages}}>
        {children}
    </UserContext.Provider>
    )
}

export { UserContextProvider };
export default UserContextProvider;

