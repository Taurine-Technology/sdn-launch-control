import React from 'react';
import { AuthProvider, useAuth } from './utilities/AuthContext';
import SignIn from './pages/SignIn';
import "./fonts.css";
import { ThemeProvider } from '@mui/material/styles';
import theme from './theme';
import HomePage from "./pages/HomePage";
import {BrowserRouter, Routes, Route, HashRouter} from "react-router-dom";
import DeviceListPage from "./pages/DeviceListPage";
function MainComponent() {
    return <div>
        <h1>Welcome to the Home Page</h1>
    </div>;
}

const App = () => {
    const { isAuthenticated } = useAuth();
    const { signIn } = useAuth();
    signIn();
    if (isAuthenticated) {
        return (
            <ThemeProvider theme={theme}>
                <HashRouter>
                    <Routes>
                            <Route path="/" element={<HomePage/>}/>
                            <Route path="/devices" element={<DeviceListPage/>}/>
                    </Routes>
                </HashRouter>
            </ThemeProvider>
        );
    }
    return (
        <ThemeProvider theme={theme}>
        <SignIn />
        </ThemeProvider>
    );

};

export default () => (
    <AuthProvider>
        <App />
    </AuthProvider>
);
