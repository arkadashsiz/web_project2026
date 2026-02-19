export default function Login() {
    const [identifier, setIdentifier] = useState("");
    const [password, setPassword] = useState("");
  
    const handleLogin = async (e) => {
      e.preventDefault();
  
      try {
        const res = await axios.post("/api/login/", {
          identifier,
          password,
        });
  
        localStorage.setItem("token", res.data.token);
        localStorage.setItem("roles", JSON.stringify(res.data.roles));
  
        window.location.href = "/dashboard";
      } catch (err) {
        console.error(err);
      }
    };
  
    return (
      <form onSubmit={handleLogin}>
        <input
          placeholder="Username / Email / Phone / National ID"
          onChange={(e) => setIdentifier(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit">Login</button>
      </form>
    );
  }
  