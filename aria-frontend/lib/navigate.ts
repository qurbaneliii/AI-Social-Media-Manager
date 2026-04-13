const BASE_PATH = '/AI-Social-Media-Manager';

export const navigateTo = (path: string) => {
  if (typeof window !== 'undefined') {
    window.location.href = BASE_PATH + path;
  }
};

export const getBasePath = () => BASE_PATH;