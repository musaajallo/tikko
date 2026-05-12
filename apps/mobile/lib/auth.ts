import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "tikko.access_token";
const REFRESH_KEY = "tikko.refresh_token";

export async function getToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export async function setToken(token: string, refreshToken?: string): Promise<void> {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
  if (refreshToken) {
    await SecureStore.setItemAsync(REFRESH_KEY, refreshToken);
  }
}

export async function clearToken(): Promise<void> {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(REFRESH_KEY);
}
