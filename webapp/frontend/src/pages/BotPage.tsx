import { useParams } from '@tanstack/react-router';

/**
 * Bot view page component
 * Public page for viewing a published bot by slug
 * URL: /bot-slug
 */
export const BotPage = () => {
  const { slug } = useParams({ from: '/$slug' });

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Bot: {slug}</h1>
        <p className="text-gray-600 dark:text-gray-400">Bot view page</p>
      </div>
    </div>
  );
};
