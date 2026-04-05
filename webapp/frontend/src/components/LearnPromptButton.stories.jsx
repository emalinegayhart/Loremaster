import '../App.css';

export default {
  title: 'Components/LearnPromptButton',
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export const Default = {
  render: () => (
    <button 
      className="learn-prompt-btn" 
      onClick={() => console.log('Learn 2 Prompt clicked')}
      aria-label="Learn to Prompt"
    >
      Learn 2 Prompt
    </button>
  ),
};

export const Hover = {
  render: () => (
    <button 
      className="learn-prompt-btn" 
      onClick={() => console.log('Learn 2 Prompt clicked')}
      aria-label="Learn to Prompt"
      style={{ boxShadow: '0 0 20px rgba(240, 192, 64, 0.35)' }}
    >
      Learn 2 Prompt
    </button>
  ),
};

export const Focus = {
  render: () => (
    <button 
      className="learn-prompt-btn" 
      onClick={() => console.log('Learn 2 Prompt clicked')}
      aria-label="Learn to Prompt"
      autoFocus
    >
      Learn 2 Prompt
    </button>
  ),
};

export const Mobile = {
  render: () => (
    <button 
      className="learn-prompt-btn" 
      onClick={() => console.log('Learn 2 Prompt clicked')}
      aria-label="Learn to Prompt"
    >
      Learn 2 Prompt
    </button>
  ),
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
};
