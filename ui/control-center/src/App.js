import React from 'react';
import "./fonts.css";
import { ThemeProvider } from '@mui/material/styles';
import theme from './theme';
import HomePage from "./pages/HomePage";
import {BrowserRouter, Routes, Route, HashRouter} from "react-router-dom";
import DeviceListPage from "./pages/DeviceListPage";
import DeviceDetailsPage from "./pages/DeviceDetailsPage";
import ControllerListPage from "./pages/ControllerListPage";
import PluginPage from "./pages/PluginPage";
import InstallationPage from "./pages/InstallationPage";
import MonitoringHub from "./pages/MonitoringHubPage";
import OnosClassifierPage from "./pages/OnosClassifierPage";
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
                        <Route path="/plugins" element={<PluginPage/>}/>
                        <Route path="/install" element={<InstallationPage/>}/>
                        <Route path="/monitoring-hub" element={<MonitoringHub/>} />
                        <Route path="/onos-classifier" element={<OnosClassifierPage/>} />
                    </Routes>
                </HashRouter>
            </ThemeProvider>
        );
    };

export default () => (

        <App />

);
