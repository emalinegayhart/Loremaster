import React, { ReactNode, AnchorHTMLAttributes } from 'react';
import './GoldButton.css';

interface GoldButtonProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  children: ReactNode;
  href: string;
}

export default function GoldButton({ children, href, ...props }: GoldButtonProps): React.ReactNode {
  return (
    <a href={href} className="gold-button" {...props}>
      {children}
    </a>
  );
}
