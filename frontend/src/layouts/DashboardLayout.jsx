import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";

import Header from "./Header.jsx";
import Sidebar from "./Sidebar.jsx";
import Footer from "./Footer.jsx";

import styles from "./DashboardLayout.module.css";

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const openSidebar = () => setSidebarOpen(true);

  const closeSidebar = () => setSidebarOpen(false);

  const toggleSidebar = () => setSidebarOpen((prev) => !prev);

  // Close sidebar automatically when switching to desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 1024) {
        closeSidebar();
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <div className={styles.shell}>
      <Sidebar
        isOpen={sidebarOpen}
        onClose={closeSidebar}
      />

      <div className={styles.content}>
        <Header
          onMenuClick={toggleSidebar}
        />

        <main
          className={styles.main}
          role="main"
        >
          <Outlet />
        </main>

        <Footer />
      </div>
    </div>
  );
}