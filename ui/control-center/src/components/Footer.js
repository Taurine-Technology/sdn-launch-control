/**
 * File: Footer.js
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

import React from 'react';
import { Box, Link, Typography, Grid } from '@mui/material';

const Footer = () => {
    return (
        <Box position="fixed" sx={{ backgroundColor: '#02032F', padding: 2, bottom: 0, left: 0, right: 0, zIndex: (theme) => theme.zIndex.drawer + 1 }}>
            <Grid container justifyContent="space-between" alignItems="center">
                <Grid item>
                    <Link href="mailto:info@taurinetech.com" color="inherit">
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <img src="./images/email.png" alt="Email" style={{ verticalAlign: 'middle', height: '22px' }} />
                            <Typography variant="body_footer" component="span" sx={{ ml: 1 }}>info@taurinetech.com</Typography>
                        </Box>
                    </Link>
                </Grid>
                <Grid item>
                    <Box sx={{ display: 'flex' }}>
                        <Link href="https://x.com/taurine_tech/" target="_blank"><Box sx={{ padding: '3px' }}><img src="./images/x.png" alt="Twitter" style={{height: '22px' }}/></Box></Link>
                        <Link href="https://www.instagram.com/taurinetech/" target="_blank"><Box sx={{ padding: '3px' }}><img src="./images/instagram.png" alt="Instagram" style={{ height: '22px' }}/></Box></Link>
                        <Link href="https://www.linkedin.com/company/taurine-technology/" target="_blank"><Box sx={{ padding: '3px' }}><img src="./images/linkedin.png" alt="LinkedIn" style={{height: '22px' }}/></Box></Link>
                    </Box>
                    <Typography variant="body_footer">
                        <Link href="#" target="_blank" color="#ffffff">terms & conditions</Link>
                    </Typography>
                </Grid>
            </Grid>
        </Box>
    );
};

export default Footer;
