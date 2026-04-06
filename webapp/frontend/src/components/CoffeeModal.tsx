import { useState, useEffect, ReactNode } from 'react';

export default function CoffeeModal(): ReactNode {
  const [visible, setVisible] = useState<boolean>(false);

  useEffect((): (() => void) => {
    const timer = setTimeout((): void => setVisible(true), 10000);
    return (): void => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <div className="coffee-modal">
      <button className="coffee-close" onClick={(): void => setVisible(false)}>
        ✕
      </button>
      <a href="https://buymeacoffee.com/emzra" target="_blank" rel="noreferrer">
        ☕ Buy the creator a coffee!
      </a>
    </div>
  );
}
