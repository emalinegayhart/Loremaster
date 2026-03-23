import { useState, useEffect } from "react";

export default function CoffeeModal() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 10000);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <div className="coffee-modal">
      <button className="coffee-close" onClick={() => setVisible(false)}>✕</button>
      <a href="https://buymeacoffee.com/emzra" target="_blank" rel="noreferrer">
        ☕ Buy the creator a coffee!
      </a>
    </div>
  );
}
