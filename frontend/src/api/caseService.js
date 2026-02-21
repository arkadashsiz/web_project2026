import axios from "./axios";

export const getCases = () => axios.get("cases/");
export const createCase = (data) => axios.post("cases/", data);
export const deleteCase = (id) => axios.delete(`cases/${id}/`);
export const updateCase = (id, data) => axios.put(`cases/${id}/`, data);
