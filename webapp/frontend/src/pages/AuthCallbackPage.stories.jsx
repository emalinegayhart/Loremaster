import { AuthCallbackPageContent } from './AuthCallbackPage';

export default {
  title: 'Pages/AuthCallbackPage',
  component: AuthCallbackPageContent,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export const Loading = {
  args: {
    isLoading: true,
    error: null,
  },
};

export const ErrorAccessDenied = {
  args: {
    isLoading: false,
    error: 'access_denied',
  },
};

export const ErrorInvalidGrant = {
  args: {
    isLoading: false,
    error: 'invalid_grant',
  },
};

export const ErrorMissingCode = {
  args: {
    isLoading: false,
    error: 'Missing authorization code or state',
  },
};

export const ErrorServerError = {
  args: {
    isLoading: false,
    error: 'server_error',
  },
};

export const Mobile = {
  args: {
    isLoading: true,
    error: null,
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
};
