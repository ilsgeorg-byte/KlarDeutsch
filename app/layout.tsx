import "./globals.css";
import React from "react";
import ErrorBoundary from "./components/ErrorBoundary";

export const metadata = {
  title: "KlarDeutsch",
  description: "Учебный сайт для немецкого A1+"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body style={{ margin: 0, padding: 0 }}>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </body>
    </html>
  );
}

