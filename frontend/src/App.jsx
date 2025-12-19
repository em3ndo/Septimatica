import React from 'react';
import GraphCanvas from './components/GraphCanvas'; // Imports your custom component
import './App.css'; // Imports the CSS we just updated

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Septimatica</h1>
      </header>
      <main>
        {/* This renders the interactive graph builder we created */}
        <GraphCanvas />
      </main>
    </div>
  );
}

export default App;