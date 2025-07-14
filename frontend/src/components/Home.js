// App.js

import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import axios from "axios";

function Home() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    axios
      .get("http://localhost:3001/")
      .then((res) => setMessage(res.data.msg))
      .catch((err) => console.error("Error:", err));
  }, []);

  return (
    <div>
      <h1>Home Page</h1>
      <h2>{message}</h2>
    </div>
  );
}

function UserProfile() {
  const [profile, setProfile] = useState([]);

  useEffect(() => {
    axios
      .get("http://localhost:3002/fetchUser")
      .then((res) => setProfile(res.data))
      .catch((err) => console.error("Error:", err));
  }, []);

  return (
    <div>
      <h1>User Profiles</h1>
      {profile.map((user, index) => (
        <div key={index}>
          <h3>Name: {user.name}</h3>
          <h3>Age: {user.age}</h3>
        </div>
      ))}
    </div>
  );
}

function App() {
  return (
    <Router>
      <nav>
        <Link to="/">Home</Link> | <Link to="/fetchUser">Users</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/fetchUser" element={<UserProfile />} />
      </Routes>
    </Router>
  );
}

export default App;
