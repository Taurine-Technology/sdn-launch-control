
import React from 'react';
import { List, Grid } from '@mui/material';
import ControllerItem from './ControllerItem';

function ControllerList({ controllers }) {
    return (
        <List>
            <Grid container>
                <Grid item >
                {controllers.map(controller => (
                        <ControllerItem key={controller.lan_ip_address} controller={controller} />
                ))}
                </Grid>
            </Grid>
        </List>
    );
}

export default ControllerList;
