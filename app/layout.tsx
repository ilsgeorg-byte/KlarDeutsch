import "./globals.css";
import React from "react";

<link rel="icon" href="/icon.svg" type="image/svg+xml" />


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
        {children}
      </body>
    </html>
  );
}
