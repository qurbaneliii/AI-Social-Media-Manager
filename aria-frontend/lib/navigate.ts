const STATIC_BASE_PATH = "/AI-Social-Media-Manager";

const resolveBasePath = () => {
  if (process.env.NEXT_PUBLIC_IS_STATIC === "true") {
    return STATIC_BASE_PATH;
  }

  if (typeof window !== "undefined") {
    const path = window.location.pathname;
    if (path === STATIC_BASE_PATH || path.startsWith(`${STATIC_BASE_PATH}/`)) {
      return STATIC_BASE_PATH;
    }
  }

  return "";
};

export const navigateTo = (path: string) => {
  if (typeof window !== "undefined") {
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    window.location.href = `${resolveBasePath()}${normalizedPath}`;
  }
};

export const getBasePath = () => resolveBasePath();