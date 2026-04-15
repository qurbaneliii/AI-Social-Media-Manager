const RAW_BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const BASE_PATH = RAW_BASE_PATH.endsWith("/")
  ? RAW_BASE_PATH.slice(0, -1)
  : RAW_BASE_PATH;

const withBasePath = (path: string): string => {
  if (!path.startsWith("/")) {
    path = `/${path}`;
  }
  return `${BASE_PATH}${path}`;
};

export const navigateTo = (path: string) => {
  if (typeof window !== "undefined") {
    window.location.href = withBasePath(path);
  }
};

export const getBasePath = () => BASE_PATH;