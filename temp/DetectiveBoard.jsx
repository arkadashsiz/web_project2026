import { useEffect, useState } from "react";
import { getCases, createCase, deleteCase } from "../api/caseService";

function DetectiveBoard() {
    const [cases, setCases] = useState([]);
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");

    const fetchCases = async () => {
        try {
            const response = await getCases();
            setCases(response.data);
        } catch (error) {
            console.error(error);
        }
    };

    useEffect(() => {
        fetchCases();
    }, []);

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            await createCase({ title, description, status: "Open" });
            setTitle("");
            setDescription("");
            fetchCases();
        } catch (error) {
            console.error(error);
        }
    };

    const handleDelete = async (id) => {
        try {
            await deleteCase(id);
            fetchCases();
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <div className="page">
            <div className="card" style={{ marginBottom: "1.5rem" }}>
                <h2 style={{ marginBottom: "1.25rem" }}>🕵️ Detective Board</h2>
                <h3 style={{ marginBottom: "0.75rem", fontSize: "1rem" }}>Create New Case</h3>
                <form onSubmit={handleCreate}>
                    <div className="form-group">
                        <label>Title</label>
                        <input
                            placeholder="Case title"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                    </div>
                    <div className="form-group" style={{ marginTop: "0.75rem" }}>
                        <label>Description</label>
                        <textarea
                            placeholder="Case description"
                            value={description}
                            rows={3}
                            onChange={(e) => setDescription(e.target.value)}
                        />
                    </div>
                    <button type="submit" style={{ marginTop: "0.75rem" }}>
                        + Create Case
                    </button>
                </form>
            </div>

            <div className="card">
                <h3 style={{ marginBottom: "1rem", fontSize: "1rem" }}>Cases</h3>
                {cases.length === 0 ? (
                    <p>No cases found.</p>
                ) : (
                    <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                        {cases.map((c) => (
                            <li
                                key={c.id}
                                style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                    padding: "0.75rem 1rem",
                                    borderRadius: "8px",
                                    border: "1px solid var(--border)",
                                    background: "var(--bg)",
                                }}
                            >
                                <div>
                                    <strong style={{ color: "var(--text)" }}>{c.title}</strong>
                                    <span className="role-badge" style={{ marginLeft: "0.5rem" }}>{c.status}</span>
                                </div>
                                <button
                                    onClick={() => handleDelete(c.id)}
                                    className="logout-btn"
                                    style={{ padding: "0.3em 0.8em", fontSize: "0.8rem" }}
                                >
                                    Delete
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}

export default DetectiveBoard;
