import axios from "axios";

const axiosInstance = axios.create({
    baseURL: "http://127.0.0.1:8000/api/",
});

// Attach access token automatically
axiosInstance.interceptors.request.use(
    (config) => {
        const access = localStorage.getItem("access");
        if (access) {
            config.headers.Authorization = `Bearer ${access}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Handle token refresh
axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (
            error.response &&
            error.response.status === 401 &&
            !originalRequest._retry
        ) {
            originalRequest._retry = true;

            try {
                const refresh = localStorage.getItem("refresh");

                const response = await axios.post(
                    "http://127.0.0.1:8000/api/users/token/refresh/",
                    { refresh }
                );

                localStorage.setItem("access", response.data.access);

                originalRequest.headers.Authorization =
                    `Bearer ${response.data.access}`;

                return axiosInstance(originalRequest);
            } catch (refreshError) {
                localStorage.clear();
                window.location.href = "/login";
            }
        }

        return Promise.reject(error);
    }
);

export default axiosInstance;
