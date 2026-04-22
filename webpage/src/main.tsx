import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./app/App";
import "./styles.css";

if (import.meta.env.DEV) {
  const rawConsoleError = console.error;
  console.error = (...args: unknown[]) => {
    const merged = args.map((x) => String(x)).join(" ");
    if (merged.includes("Support for defaultProps will be removed from function components")) {
      return;
    }
    rawConsoleError(...args);
  };
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
