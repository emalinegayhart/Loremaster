import React from 'react';
import './GoldButton.css';

export default function GoldButton({ children, href, ...props }) {
  return (
    <a href={href} className="gold-button" {...props}>
      {children}
    </a>
  );
}
