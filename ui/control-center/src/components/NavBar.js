/**
 * File: NavBar.js
 * Copyright (C) 2025 Keegan White
 *
 * This file is part of the SDN Launch Control project.
 *
 * This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
 * available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
 *
 * Contributions to this project are governed by a Contributor License Agreement (CLA).
 * By submitting a contribution, contributors grant Keegan White exclusive rights to
 * the contribution, including the right to relicense it under a different license
 * at the copyright owner's discretion.
 *
 * Unless required by applicable law or agreed to in writing, software distributed
 * under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the GNU General Public License for more details.
 *
 * For inquiries, contact Keegan White at keeganwhite@taurinetech.com.
 */

import React, {useEffect, useState} from 'react';
import { Link } from 'react-router-dom';
import { AppBar, Toolbar, IconButton, Button, Grid, Drawer, List, ListItem, ListItemButton, ListItemText, Collapse } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import { Box } from '@mui/system';
import axios from "axios";


const NavBar = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [openLobby, setOpenLobby] = useState(false);
    const [openHardware, setOpenHardware] = useState(false);
    const [openSystem, setOpenSystem] = useState(false);
    const [openMonitoring, setOpenMonitoring] = useState(false);
    const [openAi, setOpenAi] = useState(false);
    const [isPluginInstalled, setIsPluginInstalled] = useState(false);

    useEffect(() => {
        const checkPluginInstallation = async () => {
            try {
                const response = await axios.get(`http://localhost:8000/plugins/check/tau-onos-metre-traffic-classification/`);
                setIsPluginInstalled(response.data.message); // Assuming response includes installation status
            } catch (error) {
                console.error('Error checking plugin installation:', error);
            }
        };

        checkPluginInstallation();
    }, []);

    const handleClickLobby = () => {
        setOpenLobby(!openLobby);
    };

    const handleClickAi = () => {
        setOpenAi(!openAi);
    };

    const handleClickHardware = () => {
        setOpenHardware(!openHardware);
    };

    const handleClickSystem = () => {
        setOpenSystem(!openSystem);
    };

    const handleClickMonitoring = () => {
        setOpenMonitoring(!openMonitoring);
    };

    const toggleDrawer = (open) => (event) => {
        if (event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) {
            return;
        }
        setIsOpen(open);
    };

    const handleMenuItemClick = (event) => {
        event.stopPropagation();
    };


    return (
        <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
            <Toolbar>
                <Grid container direction="row" justifyContent="space-between" alignItems="center" sx={{ padding: '0 20px' }}>
                    <Grid item>
                        <IconButton onClick={toggleDrawer(true)} edge="start" color="inherit" aria-label="menu">
                            <MenuIcon />
                        </IconButton>
                        <Drawer anchor='left' open={isOpen} onClose={toggleDrawer(false)} sx={{ '& .MuiDrawer-paper': { backgroundColor: '#02032F', color: 'white' }}}>
                            <Box sx={{ width: 250, paddingTop: '100px' }} role="presentation">
                                <List>
                                    {/* Lobby Heading */}
                                    <ListItemButton onClick={(event) => {handleMenuItemClick(event); handleClickLobby();}}>
                                        <ListItemText primary="Lobby" />
                                        {openLobby ? <ExpandLess /> : <ExpandMore />}
                                    </ListItemButton>
                                    <Collapse in={openLobby} timeout="auto" unmountOnExit>
                                        <List component="div" disablePadding>
                                            <ListItemButton sx={{ pl: 4 }} component={Link} to="/">
                                                <ListItemText primary="Dashboard" />
                                            </ListItemButton>
                                        </List>
                                    </Collapse>

                                    {/*AI section*/}
                                    {isPluginInstalled && (
                                        <>
                                            <ListItemButton onClick={handleClickAi}>
                                            <ListItemText primary="AI Services" />
                                            {openAi ? <ExpandLess /> : <ExpandMore />}
                                            </ListItemButton>
                                            <Collapse in={openAi} timeout="auto" unmountOnExit>
                                                    <List component="div" disablePadding>
                                                        <ListItemButton sx={{ pl: 4 }} component={Link} to="/onos-classifier">
                                                            <ListItemText primary="ONOS Traffic Classification" />
                                                        </ListItemButton>
                                                    </List>
                                            </Collapse>
                                        </>
                                    )}


                                    {/* Hardware Heading */}
                                    <ListItemButton onClick={handleClickHardware}>
                                        <ListItemText primary="Hardware" />
                                        {openHardware ? <ExpandLess /> : <ExpandMore />}
                                    </ListItemButton>
                                    <Collapse in={openHardware} timeout="auto" unmountOnExit>
                                        <List component="div" disablePadding>
                                            <ListItemButton sx={{ pl: 4 }} component={Link} to="/controllers">
                                                <ListItemText primary="Controllers" />
                                            </ListItemButton>
                                            <ListItemButton sx={{ pl: 4 }} component={Link} to="/devices">
                                                <ListItemText primary="Devices" />
                                            </ListItemButton>
                                        </List>
                                    </Collapse>

                                    {/* System Heading */}
                                    <ListItemButton onClick={handleClickSystem}>
                                        <ListItemText primary="System" />
                                        {openSystem ? <ExpandLess /> : <ExpandMore />}
                                    </ListItemButton>
                                    <Collapse in={openSystem} timeout="auto" unmountOnExit>
                                        <List component="div" disablePadding>
                                            <ListItemButton sx={{ pl: 4 }} component={Link} to="/plugins">
                                                <ListItemText primary="Plugins" />
                                            </ListItemButton>
                                            <ListItemButton sx={{ pl: 4 }} component={Link} to="/install">
                                                <ListItemText primary="Install Software" />
                                            </ListItemButton>
                                        </List>
                                    </Collapse>

                                    {/* Monitoring Heading */}
                                    <ListItemButton onClick={handleClickMonitoring}>
                                        <ListItemText primary="Monitoring" />
                                        {openMonitoring ? <ExpandLess /> : <ExpandMore />}
                                    </ListItemButton>
                                    <Collapse in={openMonitoring} timeout="auto" unmountOnExit>
                                        <List component="div" disablePadding>
                                            <ListItemButton sx={{ pl: 4 }} component={Link} to="/monitoring-hub">
                                                <ListItemText primary="Hub" />
                                            </ListItemButton>
                                        </List>
                                    </Collapse>
                                </List>
                            </Box>
                        </Drawer>
                    </Grid>
                    <Grid item>

                            <img src="./logo100.png" alt="Logo" style={{height: '80px', padding: '10px' }}/>

                    </Grid>
                </Grid>
            </Toolbar>
        </AppBar>
    );
};



export default NavBar;
