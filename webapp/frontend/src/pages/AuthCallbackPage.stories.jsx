import { AuthCallbackPageComponent } from './AuthCallbackPage';

export default {
  title: 'Pages/AuthCallbackPage',
  component: AuthCallbackPageComponent,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export const Loading = {
  args: {
    initialError: null,
    initialLoading: true,
  },
};

export const ErrorAccessDenied = {
  args: {
    initialError: 'access_denied',
    initialLoading: false,
  },
};

export const ErrorInvalidGrant = {
  args: {
    initialError: 'invalid_grant',
    initialLoading: false,
  },
};

export const ErrorMissingCode = {
  args: {
    initialError: 'Missing authorization code or state',
    initialLoading: false,
  },
};

export const ErrorServerError = {
  args: {
    initialError: 'server_error',
    initialLoading: false,
  },
};

export const Mobile = {
  args: {
    initialError: null,
    initialLoading: true,
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
};
