export const errorMessageMap = {
  access_denied: 'You denied access. Please try again.',
  invalid_grant: 'Your session expired. Please try again.',
  invalid_request: 'Invalid request. Please try again.',
  invalid_scope: 'Invalid permissions requested. Please try again.',
  server_error: 'Server error. Please try again.',
  temporarily_unavailable: 'Service temporarily unavailable. Please try again.',
  'Missing authorization code or state': 'Authentication failed. Please try again.',
};

export function getHumanReadableErrorMessage(errorCode) {
  return errorMessageMap[errorCode] || `Authentication error: ${errorCode}. Please try again.`;
}
