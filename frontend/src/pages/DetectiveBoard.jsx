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
        <div style={{ padding: 40 }}>
            <h2>Detective Board</h2>

            <h3>Create New Case</h3>
            <form onSubmit={handleCreate}>
                <input
                    placeholder="Title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                />
                <br /><br />
                <textarea
                    placeholder="Description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                />
                <br /><br />
                <button type="submit">Create Case</button>
            </form>

            <hr />

            <h3>Cases</h3>
            <ul>
                {cases.map((c) => (
                    <li key={c.id}>
                        <strong>{c.title}</strong> — {c.status}
                        <button
                            style={{ marginLeft: 10 }}
                            onClick={() => handleDelete(c.id)}
                        >
                            Delete
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default DetectiveBoard;
