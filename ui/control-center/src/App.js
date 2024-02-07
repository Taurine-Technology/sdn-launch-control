import React from 'react';
import "./fonts.css";
import { ThemeProvider } from '@mui/material/styles';
import theme from './theme';
import HomePage from "./pages/HomePage";
import {BrowserRouter, Routes, Route, HashRouter} from "react-router-dom";
import DeviceListPage from "./pages/DeviceListPage";
import DeviceDetailsPage from "./pages/DeviceDetailsPage";
import ControllerListPage from "./pages/ControllerListPage";
function MainComponent() {
    return <div>
        <h1>Welcome to the Home Page</h1>
    </div>;
}

const App = () => {

        return (
            <ThemeProvider theme={theme}>
                <HashRouter>
                    <Routes>
                            <Route path="/" element={<HomePage/>}/>
                            <Route path="/devices" element={<DeviceListPage/>}/>
                        <Route path="/controllers" element={<ControllerListPage/>}/>
                        <Route path="/devices/:deviceIp" element={<DeviceDetailsPage/>}/>
                    </Routes>
                </HashRouter>
            </ThemeProvider>
        );
    };

export default () => (

        <App />

);
