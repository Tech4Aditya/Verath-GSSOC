import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
} from 'react-native';
import { FontAwesome } from '@expo/vector-icons';
import { askQuestion, startRecording } from '../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function AskScreen({ navigation }) {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [sources, setSources] = useState([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(0);
  const scrollViewRef = useRef(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = await AsyncStorage.getItem('sb_token');
    if (token) {
      setIsAuthenticated(true);
    } else {
      setShowOnboarding(true);
    }
  };

  const handleOnboardingNext = async () => {
    if (onboardingStep === 0) {
      setOnboardingStep(1);
    } else if (onboardingStep === 1) {
      setOnboardingStep(2);
    } else {
      setShowOnboarding(false);
    }
  };

  const handleSubmit = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setAnswer('');
    setSources([]);

    try {
      const response = await askQuestion(query);
      setAnswer(response.answer);
      setSources(response.sources || []);
      setQuery('');
    } catch (error) {
      Alert.alert('Error', 'Failed to get answer. Please try again.');
      setAnswer('Sorry, I could not connect to your SecondBrain. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceInput = async () => {
    if (recording) return;

    setRecording(true);
    setAnswer('');
    setSources([]);

    try {
      const response = await startRecording(5);
      if (response.success) {
        setAnswer('Processing your voice input...');
        setTimeout(async () => {
          try {
            const queryResponse = await askQuestion('What did I just record?');
            setAnswer(queryResponse.answer);
            setSources(queryResponse.sources || []);
          } catch (error) {
            setAnswer('Voice recording processed. You can now ask questions about your memory.');
          }
        }, 2000);
      } else {
        Alert.alert('Error', response.error || 'Failed to record audio');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to record audio');
    } finally {
      setRecording(false);
    }
  };

  const OnboardingOverlay = () => (
    <View style={styles.overlay}>
      <View style={styles.onboardingCard}>
        {onboardingStep === 0 && (
          <>
            <FontAwesome name="brain" size={60} color="#6366f1" />
            <Text style={styles.onboardingTitle}>Welcome to SecondBrain</Text>
            <Text style={styles.onboardingText}>
              What do you want to remember? Lectures, meetings, conversations, or daily life?
            </Text>
            <TouchableOpacity style={styles.onboardingButton} onPress={handleOnboardingNext}>
              <Text style={styles.onboardingButtonText}>Continue</Text>
            </TouchableOpacity>
          </>
        )}

        {onboardingStep === 1 && (
          <>
            <FontAwesome name="microphone" size={60} color="#6366f1" />
            <Text style={styles.onboardingTitle}>Microphone Access</Text>
            <Text style={styles.onboardingText}>
              SecondBrain needs microphone access to record and transcribe your conversations.
            </Text>
            <TouchableOpacity style={styles.onboardingButton} onPress={handleOnboardingNext}>
              <Text style={styles.onboardingButtonText}>Allow Access</Text>
            </TouchableOpacity>
          </>
        )}

        {onboardingStep === 2 && (
          <>
            <FontAwesome name="lightbulb" size={60} color="#6366f1" />
            <Text style={styles.onboardingTitle}>Try It Out</Text>
            <Text style={styles.onboardingText}>
              Ask anything like "What did I do today?" or record a voice note.
            </Text>
            <TouchableOpacity style={styles.onboardingButton} onPress={handleOnboardingNext}>
              <Text style={styles.onboardingButtonText}>Get Started</Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </View>
  );

  if (showOnboarding) {
    return <OnboardingOverlay />;
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>SecondBrain</Text>
        <TouchableOpacity onPress={() => navigation.navigate('Settings')}>
          <FontAwesome name="cog" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      <ScrollView
        ref={scrollViewRef}
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
      >
        {answer ? (
          <View style={styles.answerContainer}>
            <View style={styles.answerHeader}>
              <FontAwesome name="robot" size={20} color="#6366f1" />
              <Text style={styles.answerLabel}>SecondBrain</Text>
            </View>
            <Text style={styles.answerText}>{answer}</Text>
            
            {sources.length > 0 && (
              <View style={styles.sourcesContainer}>
                <Text style={styles.sourcesTitle}>Sources</Text>
                {sources.map((source, index) => (
                  <View key={index} style={styles.sourceItem}>
                    <FontAwesome name="user-circle" size={14} color="#888" />
                    <Text style={styles.sourceText}>
                      {source.speaker} • {source.timestamp} • {(source.importance * 100).toFixed(0)}%
                    </Text>
                  </View>
                ))}
              </View>
            )}
          </View>
        ) : (
          <View style={styles.placeholderContainer}>
            <FontAwesome name="comments" size={60} color="#374151" />
            <Text style={styles.placeholderText}>
              Ask anything about your memories, or record a voice note
            </Text>
          </View>
        )}

        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#6366f1" />
            <Text style={styles.loadingText}>Thinking...</Text>
          </View>
        )}

        {recording && (
          <View style={styles.recordingContainer}>
            <View style={styles.recordingIndicator} />
            <Text style={styles.recordingText}>Recording...</Text>
          </View>
        )}
      </ScrollView>

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder="Ask anything..."
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={handleSubmit}
          multiline
          maxLength={500}
        />
        <TouchableOpacity
          style={[styles.iconButton, recording && styles.iconButtonDisabled]}
          onPress={handleVoiceInput}
          disabled={recording || loading}
        >
          <FontAwesome name="microphone" size={24} color="#6366f1" />
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.sendButton, !query.trim() && styles.sendButtonDisabled]}
          onPress={handleSubmit}
          disabled={!query.trim() || loading}
        >
          <FontAwesome name="paper-plane" size={24} color="#fff" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  onboardingCard: {
    backgroundColor: '#1f2937',
    borderRadius: 20,
    padding: 30,
    alignItems: 'center',
    width: '100%',
    maxWidth: 400,
  },
  onboardingTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 20,
    marginBottom: 10,
    textAlign: 'center',
  },
  onboardingText: {
    fontSize: 16,
    color: '#9ca3af',
    textAlign: 'center',
    marginBottom: 30,
    lineHeight: 24,
  },
  onboardingButton: {
    backgroundColor: '#6366f1',
    paddingVertical: 15,
    paddingHorizontal: 40,
    borderRadius: 10,
    width: '100%',
  },
  onboardingButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: Platform.OS === 'ios' ? 60 : 20,
    backgroundColor: '#1f2937',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 100,
  },
  answerContainer: {
    backgroundColor: '#1f2937',
    borderRadius: 15,
    padding: 20,
    marginBottom: 10,
  },
  answerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  answerLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#6366f1',
    marginLeft: 10,
  },
  answerText: {
    fontSize: 16,
    color: '#fff',
    lineHeight: 24,
  },
  sourcesContainer: {
    marginTop: 15,
    paddingTop: 15,
    borderTopWidth: 1,
    borderTopColor: '#374151',
  },
  sourcesTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#9ca3af',
    marginBottom: 10,
  },
  sourceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 5,
  },
  sourceText: {
    fontSize: 12,
    color: '#9ca3af',
    marginLeft: 8,
  },
  placeholderContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  placeholderText: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 20,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 30,
  },
  loadingText: {
    fontSize: 16,
    color: '#9ca3af',
    marginTop: 10,
  },
  recordingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    backgroundColor: '#1f2937',
    borderRadius: 10,
    marginBottom: 10,
  },
  recordingIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#ef4444',
    marginRight: 10,
  },
  recordingText: {
    fontSize: 16,
    color: '#fff',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 20,
    backgroundColor: '#1f2937',
    borderTopWidth: 1,
    borderTopColor: '#374151',
  },
  input: {
    flex: 1,
    backgroundColor: '#374151',
    borderRadius: 25,
    paddingHorizontal: 20,
    paddingVertical: 12,
    color: '#fff',
    fontSize: 16,
    maxHeight: 100,
    marginRight: 10,
  },
  iconButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#374151',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  iconButtonDisabled: {
    opacity: 0.5,
  },
  sendButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#6366f1',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#374151',
    opacity: 0.5,
  },
});
