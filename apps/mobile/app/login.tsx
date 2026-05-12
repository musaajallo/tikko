import { router } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      const tokens = await api.login({ email, password });
      await setToken(tokens.access_token, tokens.refresh_token);
      router.replace("/");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const friendly = /401/.test(message) ? "Invalid credentials." : message;
      Alert.alert("Sign in failed", friendly);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Sign in to tikko</Text>
      <TextInput
        accessibilityLabel="email"
        placeholder="Email"
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
        style={styles.input}
      />
      <TextInput
        accessibilityLabel="password"
        placeholder="Password"
        secureTextEntry
        autoComplete="current-password"
        value={password}
        onChangeText={setPassword}
        style={styles.input}
      />
      <TouchableOpacity
        accessibilityRole="button"
        onPress={onSubmit}
        disabled={submitting}
        style={[styles.button, submitting && styles.buttonDisabled]}
      >
        {submitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Sign in</Text>}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, justifyContent: "center" },
  heading: { fontSize: 24, fontWeight: "600", marginBottom: 16 },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  button: {
    backgroundColor: "#111",
    padding: 14,
    borderRadius: 8,
    alignItems: "center",
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#fff", fontWeight: "600" },
});
