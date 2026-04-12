import { Routes, Route } from "react-router-dom";
import { Navbar } from "./components/navbar";
import Home from "./pages/Home";
import Discover from "./pages/Discover";
import BookDetail from "./pages/BookDetail";
import AuthorDetail from "./pages/AuthorDetail";
import Profile from "./pages/Profile";

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/discover" element={<Discover />} />
        <Route path="/book/:id" element={<BookDetail />} />
        <Route path="/author/:id" element={<AuthorDetail />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </>
  );
}
