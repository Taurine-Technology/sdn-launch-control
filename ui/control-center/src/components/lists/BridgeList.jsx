import React from 'react';
import { Grid, List } from '@mui/material';
import BridgeItem from '../items/BridgeItem'; // Make sure the path is correct

const BridgeList = ({ bridges, onEdit, onDelete }) => {
    return (
        <List>
            <Grid container>
                <Grid item>
                    {bridges.map((bridge) => (
                        <BridgeItem key={bridge.dpid} bridge={bridge} onEdit={onEdit} onDelete={onDelete} />
                    ))}
                </Grid>
            </Grid>
        </List>
    );
};

export default BridgeList;
