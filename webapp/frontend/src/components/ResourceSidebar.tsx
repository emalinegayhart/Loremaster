import React, { ReactNode } from 'react';

interface Resource {
  name: string;
  url: string;
  desc: string;
}

interface ResourceSidebarProps {
  onLearnPromptClick: () => void;
}

const RESOURCES: Resource[] = [
  {
    name: 'Raidbots',
    url: 'https://www.raidbots.com/simbot',
    desc: 'Simulate your character\'s DPS and gear upgrades',
  },
  { name: 'Icy Veins', url: 'https://www.icy-veins.com/', desc: 'Class guides and raid strategies' },
  { name: 'Wowhead', url: 'https://www.wowhead.com/', desc: 'Item database, quests, and guides' },
  {
    name: 'Raider.io',
    url: 'https://raider.io/',
    desc: 'Mythic+ rankings and character scores',
  },
  {
    name: 'Warcraft Logs',
    url: 'https://www.warcraftlogs.com/',
    desc: 'Raid and dungeon performance analysis',
  },
  {
    name: 'Bloodmallet',
    url: 'https://bloodmallet.com/',
    desc: 'Trinket and item comparisons',
  },
  {
    name: 'Keystone.guru',
    url: 'https://keystone.guru/',
    desc: 'Plan and share M+ dungeon routes',
  },
  {
    name: 'CurseForge',
    url: 'https://www.curseforge.com/',
    desc: 'Browse and install WoW addons',
  },
  {
    name: 'Reddit',
    url: 'https://www.reddit.com/r/wow/',
    desc: 'WoW community discussions on r/wow',
  },
];

export default function ResourceSidebar({ onLearnPromptClick }: ResourceSidebarProps): ReactNode {
  const ENABLE_LEARN_PROMPT = import.meta.env.VITE_ENABLE_LEARN_PROMPT === 'true';

  return (
    <nav className="resource-sidebar">
      <div className="sidebar-title">Other Resources</div>
      {RESOURCES.map((r): ReactNode => (
        <a
          key={r.name}
          href={r.url}
          target="_blank"
          rel="noreferrer"
          className="sidebar-btn"
          data-tooltip={r.desc}
        >
          {r.name}
        </a>
      ))}
      {ENABLE_LEARN_PROMPT && (
        <button
          className="learn-prompt-btn"
          onClick={onLearnPromptClick}
          aria-label="Learn to Prompt"
        >
          Learn 2 Prompt
        </button>
      )}
      <a
        href="https://github.com/emalinegayhart/loremaster"
        target="_blank"
        rel="noreferrer"
        className="sidebar-github"
        data-tooltip="View source on GitHub"
      >
        <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
          <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
        </svg>
      </a>
    </nav>
  );
}
