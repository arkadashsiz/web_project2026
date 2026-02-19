import { useState } from "react";
import axios from "axios";

export default function Register() {
  const [form, setForm] = useState({
    username: "",
    password: "",
    email: "",
    phone_number: "",
    first_name: "",
    last_name: "",
    national_id: "",
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post("/api/register/", form);
      alert("Registered successfully");
    } catch (err) {
      console.error(err.response.data);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {Object.keys(form).map((field) => (
        <input
          key={field}
          name={field}
          placeholder={field}
          onChange={handleChange}
        />
      ))}
      <button type="submit">Register</button>
    </form>
  );
}
