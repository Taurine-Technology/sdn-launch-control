// Footer.js
import React from 'react';
import { Box, Link, Typography, Grid } from '@mui/material';

const Footer = () => {
    return (
        <Box position="static" sx={{ backgroundColor: '#02032F', padding: 2 }}>
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
                        <Link href="https://twitter.com" target="_blank"><Box sx={{ padding: '3px' }}><img src="./images/x.png" alt="Twitter" style={{height: '22px' }}/></Box></Link>
                        <Link href="https://instagram.com" target="_blank"><Box sx={{ padding: '3px' }}><img src="./images/instagram.png" alt="Instagram" style={{ height: '22px' }}/></Box></Link>
                        <Link href="https://linkedin.com" target="_blank"><Box sx={{ padding: '3px' }}><img src="./images/linkedin.png" alt="LinkedIn" style={{height: '22px' }}/></Box></Link>
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
