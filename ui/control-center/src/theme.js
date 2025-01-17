/**
 * File: theme.js
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

import { createTheme } from '@mui/material/styles';

const theme = createTheme({
    components: {
        MuiAppBar: {
            styleOverrides: {
                root: {
                    backgroundColor: '#02032F',
                },
            },
        },
        MuiListItemText: {
            styleOverrides: {
                root: { // Apply styles to the root class
                    '& .MuiListItemText-primary': { // Target the primary class inside MuiListItemText
                        fontFamily: 'ComfortaaRegular',
                        fontSize: '1.2rem',
                        fontWeight: 'bold',
                        color: '#ffffff',
                    },
                    '& .MuiListItemText-secondary': { // Target the secondary class inside MuiListItemText
                        fontFamily: 'ComfortaaRegular',
                        color: '#ffffff',
                        fontSize: '1rem',
                    },
                },
            },
        },
    },
    palette: {
        primary: {
            main: '#3D019F',

        },
        secondary: {
            main: '#7456FD',

        },
        button_green: {
            main: '#33a84c',
            dark: '#1a6900'
        },
        button_red: {
            main: '#bf0000',
            dark: '#600707'
        },

    },
    typography: {
        fontFamily: [
            'ComfortaaRegular',
            'Arial', // Fallback font
            'sans-serif', // Generic fallback
        ].join(','),
        h1: {
            fontFamily: 'ComfortaaBold, Arial, sans-serif',
            fontSize: '2.5rem',
        },
        h2: {
            color: '#ffffff',
            fontFamily: 'ComfortaaBold, Arial, sans-serif',
            fontSize: '2rem',
        },
        body: {
            color: '#ffffff',
            fontFamily: 'ComfortaaRegular, Arial, sans-serif',
        },
        body_dark: {
            color: '#3D019F',
            fontFamily: 'ComfortaaRegular, Arial, sans-serif',
        },
        body_footer: {
            color: '#ffffff',
            fontFamily: 'ComfortaaRegular, Arial, sans-serif',
            fontSize: '0.75rem',
        }
    },

});

export default theme;
