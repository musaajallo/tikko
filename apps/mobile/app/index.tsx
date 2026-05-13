import { router } from "expo-router";
import { useEffect } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

import { getToken } from "@/lib/auth";

export default function Index() {
  useEffect(() => {
    (async () => {
      const token = await getToken();
      if (token) router.replace("/feed");
    })();
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>tikko</Text>
      <Text style={styles.tagline}>Time Attendance Management System.</Text>
      <TouchableOpacity
        accessibilityRole="button"
        onPress={() => router.push("/login")}
        style={styles.button}
      >
        <Text style={styles.buttonText}>Sign in</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    gap: 12,
  },
  heading: {
    fontSize: 48,
    fontWeight: "700",
  },
  tagline: {
    fontSize: 16,
    opacity: 0.7,
    marginBottom: 12,
  },
  button: {
    backgroundColor: "#22c55e",
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  buttonText: { color: "#fff", fontWeight: "600" },
});
