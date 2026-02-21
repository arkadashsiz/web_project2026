const API_BASE_URL = "http://127.0.0.1:8000/api/";

export async function getHello() {
    const response = await fetch(`${API_BASE_URL}hello/`);
    if (!response.ok) {
        throw new Error("Failed to fetch data");
    }
    return response.json();
}
