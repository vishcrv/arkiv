import { Routes, Route } from "react-router-dom";
import { Navbar } from "./components/navbar";
import Home from "./pages/Home";

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </>
  );
}
