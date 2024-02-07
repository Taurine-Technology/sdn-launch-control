import React from 'react';
import { Link } from 'react-router-dom';
import { AppBar, Toolbar, Button, Grid } from '@mui/material';


const NavBar = () => {
    return (
        <AppBar position="static" sx={{

        }}>
            <Toolbar>
                <Grid
                    container
                    direction="row"
                    justifyContent="space-between"
                    alignItems="center"
                    sx={{ padding: '0 20px' }} // Add padding here
                >
                    <Grid item>
                        <Link to="/">
                            <img src="./logo100.png" alt="Logo" style={{height: '80px' }}/>
                        </Link>
                    </Grid>
                    <Grid item>
                        <Button color="inherit" component={Link} to="/">Home</Button>
                        <Button color="inherit" component={Link} to="/devices">Devices</Button>
                        <Button color="inherit" component={Link} to="/controllers">Controllers</Button>
                        <Button color="inherit" component={Link} to="/">Faq</Button>
                        <Button color="inherit" component={Link} to="/">Sign Out</Button>
                    </Grid>

                </Grid>
            </Toolbar>
        </AppBar>
    );
};


export default NavBar;
