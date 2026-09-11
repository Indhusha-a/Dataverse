import { HashRouter, Routes, Route } from "react-router-dom"
import Landing from "./pages/Landing"
import Dashboard from "./pages/Dashboard"

export default function App() {
  return (
    <HashRouter>
      <div className="h-screen w-screen">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </div>
    </HashRouter>
  )
}
