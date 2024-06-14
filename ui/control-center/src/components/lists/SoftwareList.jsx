import React from 'react';
import { List } from '@mui/material';
import SoftwareItem from "../items/SoftwareItem";

const SoftwareList = ({ softwares, onInstall }) => {
    return (
        <List>
            {softwares.map((software, index) => (
                <SoftwareItem key={index} software={software} onInstall={onInstall} />
            ))}
        </List>
    );
};

export default SoftwareList;
