import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Create the root element and render the App component into the div with id="root"
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
