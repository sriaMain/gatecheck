import axios from "axios";

// const baseAPI = "https://gate-check.onrender.com";
const baseAPI = "http://192.168.0.174:7000";
// const baseAPI = "https://wh4r7n48-8000.inc1.devtunnels.ms/";
//  axios instance
export const axiosInstance = axios.create({
  baseURL: baseAPI,
  headers: {
    "Content-Type": "application/json",
  },
});
