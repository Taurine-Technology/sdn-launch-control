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
