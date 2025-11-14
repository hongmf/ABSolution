import { DataPanel } from './components/DataPanel';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__logo">
          <h1>ABSolution</h1>
          <p>Asset-Backed Securities Analytics Platform</p>
        </div>
      </header>
      <main className="app-main">
        <DataPanel />
      </main>
      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} ABSolution. Powered by AWS.</p>
      </footer>
    </div>
  );
}

export default App;
