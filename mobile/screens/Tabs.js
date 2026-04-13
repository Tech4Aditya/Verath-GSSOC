import React from "react";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { Platform, View } from "react-native";

import AskScreen from "./AskScreen";
import HomeScreen from "./HomeScreen";
import SettingsScreen from "./SettingsScreen";
import TimelineScreen from "./TimelineScreen";

const Tab = createBottomTabNavigator();

export default function Tabs({ onLogout }) {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: { 
          backgroundColor: "#080b14",
          borderTopWidth: 1,
          borderTopColor: "rgba(255,255,255,0.05)",
          height: Platform.OS === "ios" ? 88 : 68,
          paddingBottom: Platform.OS === "ios" ? 30 : 10,
          elevation: 0,
        },
        tabBarActiveTintColor: "#38bdf8",
        tabBarInactiveTintColor: "#64748b",
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: "700",
          textTransform: "uppercase",
          letterSpacing: 0.5,
          marginTop: -4,
        },
        tabBarIcon: ({ color, size, focused }) => {
          let iconName;
          if (route.name === "Home") iconName = focused ? "home" : "home-outline";
          else if (route.name === "Ask") iconName = focused ? "brain" : "brain";
          else if (route.name === "Timeline") iconName = focused ? "clock-check" : "clock-check-outline";
          else iconName = focused ? "cog" : "cog-outline";
          
          return (
            <View style={focused ? styles.iconContainerFocused : null}>
              <MaterialCommunityIcons name={iconName} size={24} color={color} />
            </View>
          );
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Ask" component={AskScreen} />
      <Tab.Screen name="Timeline" component={TimelineScreen} />
      <Tab.Screen name="Settings">
        {(props) => <SettingsScreen {...props} onLogout={onLogout} />}
      </Tab.Screen>
    </Tab.Navigator>
  );
}

const styles = {
  iconContainerFocused: {
    shadowColor: "#38bdf8",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 10,
    elevation: 10,
  }
};
