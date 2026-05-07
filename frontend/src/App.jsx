import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/lib/auth";
import { Navbar } from "./components/navbar";
import Home from "./pages/Home";
import Discover from "./pages/Discover";
import BookDetail from "./pages/BookDetail";
import AuthorDetail from "./pages/AuthorDetail";
import Profile from "./pages/Profile";
import ActivityPage from "./pages/Activity";
import Login from "./pages/Login";
import Register from "./pages/Register";

function ProtectedRoute({ children }) {
  const { user, ready } = useAuth();
  if (!ready) return null;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function PublicRoute({ children }) {
  const { user, ready } = useAuth();
  if (!ready) return null;
  if (user) return <Navigate to="/" replace />;
  return children;
}

function AppShell() {
  const { user } = useAuth();
  return (
    <>
      {user && <Navbar />}
      <Routes>
        <Route path="/login"    element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
        <Route path="/"         element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/discover" element={<ProtectedRoute><Discover /></ProtectedRoute>} />
        <Route path="/book/:id" element={<ProtectedRoute><BookDetail /></ProtectedRoute>} />
        <Route path="/author/:id" element={<ProtectedRoute><AuthorDetail /></ProtectedRoute>} />
        <Route path="/profile"   element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="/activity"  element={<ProtectedRoute><ActivityPage /></ProtectedRoute>} />
        <Route path="*"         element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
