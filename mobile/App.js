import React, { useState, useEffect } from "react";
import { NavigationContainer } from "@react-navigation/native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import Tabs from "./screens/Tabs";
import LoginScreen from "./screens/LoginScreen";
import RegisterScreen from "./screens/RegisterScreen";
import { View, ActivityIndicator } from "react-native";

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await AsyncStorage.getItem("sb_token");
      setIsAuthenticated(!!token);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={{ flex: 1, backgroundColor: "#080b14", justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" color="#38bdf8" />
      </View>
    );
  }

  if (!isAuthenticated) {
    if (isRegistering) {
      return (
        <RegisterScreen 
          onRegisterSuccess={() => setIsRegistering(false)} 
          onSwitchToLogin={() => setIsRegistering(false)} 
        />
      );
    }
    return (
      <LoginScreen 
        onLoginSuccess={() => setIsAuthenticated(true)} 
        onSwitchToRegister={() => setIsRegistering(true)} 
      />
    );
  }

  return (
    <NavigationContainer>
      <Tabs onLogout={() => setIsAuthenticated(false)} />
    </NavigationContainer>
  );
}
