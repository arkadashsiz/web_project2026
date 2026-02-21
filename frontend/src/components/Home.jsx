import { useEffect, useState } from "react";
import { getHello } from "../api/api";

function Home() {
    const [message, setMessage] = useState("Loading...");

    useEffect(() => {
        getHello()
            .then(data => setMessage(data.message))
            .catch(() => setMessage("Error connecting to backend"));
    }, []);

    return (
        <div style={{ padding: "40px", fontFamily: "Arial" }}>
            <h1>Django + React Connection</h1>
            <p>{message}</p>
        </div>
    );
}

export default Home;
