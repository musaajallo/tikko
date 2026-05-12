import { StatusBar } from "expo-status-bar";
import { StyleSheet, Text, View } from "react-native";

export default function Index() {
  return (
    <View style={styles.container}>
      <Text style={styles.heading}>tikko</Text>
      <Text style={styles.tagline}>Attendance, on your terms.</Text>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  heading: {
    fontSize: 48,
    fontWeight: "700",
  },
  tagline: {
    marginTop: 8,
    fontSize: 16,
    opacity: 0.7,
  },
});
