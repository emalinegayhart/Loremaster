import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import LoginModal from './LoginModal';

const meta: Meta<typeof LoginModal> = {
  title: 'Auth/LoginModal',
  component: LoginModal,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#f3f4f6' },
        { name: 'dark', value: '#1f2937' },
      ],
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    isOpen: true,
    onClose: () => alert('Modal closed'),
  },
  decorators: [
    (Story) => (
      <div className="w-full max-w-sm">
        <Story />
      </div>
    ),
  ],
};

export const DarkBackground: Story = {
  args: {
    isOpen: true,
    onClose: () => alert('Modal closed'),
  },
  parameters: {
    backgrounds: { default: 'dark' },
  },
  decorators: [
    (Story) => (
      <div className="w-full max-w-sm p-4">
        <Story />
      </div>
    ),
  ],
};

export const MobileSize: Story = {
  args: {
    isOpen: true,
    onClose: () => alert('Modal closed'),
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
  decorators: [
    (Story) => (
      <div className="w-full max-w-sm p-4">
        <Story />
      </div>
    ),
  ],
};

export const FullWidth: Story = {
  args: {
    isOpen: true,
    onClose: () => alert('Modal closed'),
  },
  decorators: [
    (Story) => (
      <div className="w-96">
        <Story />
      </div>
    ),
  ],
};
