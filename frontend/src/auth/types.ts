export type User = {
  id: number;
  username: string;
  role: "admin" | "user";
  mustChangePassword: boolean;
  fullName: string;
  email: string;
  phone: string;
  socialInstagram: string;
  socialTiktok: string;
  socialYoutube: string;
  socialWebsite: string;
  createdAt: string;
};

export type AuthSession = {
  accessToken: string;
  user: User;
};
