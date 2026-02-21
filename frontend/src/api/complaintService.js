import axios from "./axios";

export const getComplaints = () =>
    axios.get("cases/complaints/");

export const createComplaint = (data) =>
    axios.post("cases/complaints/", data);

export const deleteComplaint = (id) =>
    axios.delete(`cases/complaints/${id}/`);

export const updateComplaint = (id, data) =>
    axios.put(`cases/complaints/${id}/`, data);
