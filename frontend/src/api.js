import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000", // FastAPI backend
});

export const generatePlan = async (data) => {
  const res = await API.post("/generate", data);
  return res.data;
};