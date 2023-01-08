import logo from './logo.svg';
import './App.css';
import FilePicker from "./FilePicker"
import Dashboard from "./Dashboard";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ReportsView from './ReportsView';

function App() {
  return(
    <BrowserRouter>
    <Routes>
      <Route path="/" exact={false} element={<Dashboard component={<FilePicker />}/>}/>
      <Route path="reports" exact={false} element={<Dashboard component={<ReportsView />}/>}/>
    </Routes>
    </BrowserRouter>
  )
}

export default App;
